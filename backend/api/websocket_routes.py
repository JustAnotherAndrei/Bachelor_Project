"""
WebSocket endpoint for real-time BB84 simulation streaming.

The client connects with a session_id, and the server streams qubit-level
events as the simulation progresses.
"""

import asyncio
import logging
import os
import time
import numpy as np
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from dotenv import load_dotenv

from api.websocket_manager import session_manager
from auth.security import ACCESS_COOKIE, decode_token
from database.models import User
from quantum_logic.bb84_circuit import build_bb84_circuits
from quantum_logic.noise_model import build_noise_model
from quantum_logic.channel_model import apply_channel_loss, channel_transmittance
from quantum_logic.decoy_state import (
    simulate_wcp_pulses, aggregate_by_intensity, find_intensity,
    decoy_analysis, secure_key_rate,
)
from quantum_logic.smart_eve import smart_eve_decide
from ml.eavesdrop_detector import predict as ml_predict, extract_features_from_dict
from classical_processing.sifting import sift_keys
from classical_processing.qber import calculate_qber, is_channel_secure
from classical_processing.error_correction import correct_errors
from classical_processing.cascade import cascade_correct
from classical_processing.privacy_amplification import amplify_privacy
from qiskit_aer import AerSimulator
from database.db import SessionLocal
from database.models import SimulationRun

load_dotenv()
log = logging.getLogger(__name__)

ws_router = APIRouter(tags=["websocket"])

IBM_BACKENDS = ["ibm_fez", "ibm_marrakesh", "ibm_kingston"]


@ws_router.websocket("/ws/simulate/{session_id}")
async def simulate_stream(websocket: WebSocket, session_id: str):
    await session_manager.connect(session_id, websocket)
    try:
        # Read the user from the access-token cookie that the browser sent
        # during the WebSocket upgrade. If absent/invalid, the run is treated
        # as a guest run (user_id stays None on the DB record).
        ws_user_id = None
        access_cookie = websocket.cookies.get(ACCESS_COOKIE)
        if access_cookie:
            payload = decode_token(access_cookie, expected_type="access")
            if payload:
                try:
                    ws_user_id = int(payload["sub"])
                except (KeyError, ValueError):
                    ws_user_id = None

        config = await websocket.receive_json()
        start_time = time.perf_counter()
        n_qubits = config.get("n_qubits", 100)
        dep_prob = config.get("depolarizing_prob", 0.01)
        meas_prob = config.get("measurement_error_prob", 0.02)
        eve_mode = config.get("eve_mode", "none")   # 'none' | 'weak' | 'strong' | 'smart'
        smart_target_qber = float(config.get("smart_target_qber", 0.09))
        mode = config.get("mode", "simulator")
        ibm_backend_name = config.get("ibm_backend", "ibm_fez")
        channel_km = float(config.get("channel_distance_km", 0.0))
        ec_method = config.get("ec_method", "parity")  # 'parity' | 'cascade'
        source_type = config.get("source_type", "ideal")  # 'ideal' | 'wcp'
        mu_signal = float(config.get("mu_signal", 0.5))
        mu_decoy = float(config.get("mu_decoy", 0.1))
        p_signal = float(config.get("p_signal", 0.70))
        p_decoy = float(config.get("p_decoy", 0.15))

        # Weak Eve intercepts 30% of qubits; strong Eve intercepts 100%
        EVE_RATE = {"none": 0.0, "weak": 0.30, "strong": 1.0}
        eve_intercept = eve_mode != "none"

        rng = np.random.default_rng()
        n_sent = n_qubits  # original qubit count before channel loss
        alice_bits = rng.integers(0, 2, n_qubits).tolist()
        alice_bases = rng.integers(0, 2, n_qubits).tolist()
        bob_bases = rng.integers(0, 2, n_qubits).tolist()

        smart_eve_state = None
        if eve_intercept:
            if eve_mode == "smart":
                smart_eve_state = smart_eve_decide(n_qubits, smart_target_qber, rng)
                eve_intercepts = list(smart_eve_state.intercepts)
                eve_bases = rng.integers(0, 2, n_qubits).tolist()
            else:
                rate = EVE_RATE.get(eve_mode, 0.0)
                eve_intercepts = (rng.random(n_qubits) < rate).tolist()
                eve_bases = rng.integers(0, 2, n_qubits).tolist()
        else:
            eve_intercepts = None
            eve_bases = None

        # Apply fiber-optic channel loss (simulator mode only).
        # If WCP (decoy-state) source is selected, channel loss is folded into the
        # per-photon survival inside simulate_wcp_pulses, so don't double-apply it.
        eta = 1.0
        wcp_pulses = None
        if mode != "ibm_hardware":
            if source_type == "wcp":
                eta = channel_transmittance(channel_km)
                wcp_pulses = simulate_wcp_pulses(
                    n_qubits, mu_signal, mu_decoy, p_signal, p_decoy, eta, rng,
                )
                detected_mask = [p.detected for p in wcp_pulses]

                def _filt(lst):
                    if lst is None:
                        return None
                    return [x for x, d in zip(lst, detected_mask) if d]

                alice_bits = _filt(alice_bits)
                alice_bases = _filt(alice_bases)
                bob_bases = _filt(bob_bases)
                eve_intercepts = _filt(eve_intercepts)
                eve_bases = _filt(eve_bases)
            elif channel_km > 0:
                alice_bits, alice_bases, bob_bases, eve_intercepts, eve_bases, eta = apply_channel_loss(
                    alice_bits, alice_bases, bob_bases, eve_intercepts, eve_bases, channel_km, rng
                )

        n_qubits = len(alice_bits)  # qubits that survived channel transmission

        if n_qubits == 0:
            await session_manager.send_event(session_id, {
                "type": "error",
                "message": f"All {n_sent} photons were lost in the channel ({channel_km} km). "
                           "Reduce the distance or increase the number of qubits.",
            })
            return

        circuits = build_bb84_circuits(alice_bits, alice_bases, bob_bases)
        bob_results = []

        if mode == "ibm_hardware":
            bob_results = await _run_ibm(
                session_id, circuits, n_qubits, ibm_backend_name,
                rng, eve_intercepts, eve_bases, alice_bases,
            )
            if bob_results is None:
                return

            # Results are in — animate grid rapidly
            for i in range(n_qubits):
                await session_manager.send_event(session_id, {
                    "type": "qubit",
                    "index": i,
                    "alice_bit": alice_bits[i],
                    "alice_basis": alice_bases[i],
                    "bob_basis": bob_bases[i],
                    "bob_result": bob_results[i],
                    "basis_match": alice_bases[i] == bob_bases[i],
                    "eve_intercept": eve_intercepts[i] if eve_intercepts else False,
                })
                await asyncio.sleep(0.01)

        else:  # simulator
            noise_model = build_noise_model(dep_prob, meas_prob)
            simulator = AerSimulator(noise_model=noise_model)

            for i, qc in enumerate(circuits):
                job = simulator.run(qc, shots=1)
                counts = job.result().get_counts()
                result = int(max(counts, key=counts.get))

                if eve_intercepts and eve_intercepts[i] and eve_bases[i] != alice_bases[i]:
                    result = int(rng.integers(0, 2))

                bob_results.append(result)

                await session_manager.send_event(session_id, {
                    "type": "qubit",
                    "index": i,
                    "alice_bit": alice_bits[i],
                    "alice_basis": alice_bases[i],
                    "bob_basis": bob_bases[i],
                    "bob_result": result,
                    "basis_match": alice_bases[i] == bob_bases[i],
                    "eve_intercept": eve_intercepts[i] if eve_intercepts else False,
                })
                await asyncio.sleep(0)

        alice_key, bob_key = sift_keys(alice_bits, alice_bases, bob_results, bob_bases)
        qber = calculate_qber(alice_key, bob_key) if alice_key else 0.0
        secure = is_channel_secure(qber)

        ec_stats = None
        if ec_method == "cascade" and alice_key:
            corrected_alice, corrected_bob, ec_stats = cascade_correct(
                alice_key, bob_key, qber if qber > 0 else 0.001
            )
        else:
            corrected_alice, _ = correct_errors(alice_key, bob_key)

        final_key = amplify_privacy(corrected_alice) if corrected_alice else ""
        final_qber = round(qber, 4)
        elapsed = round(time.perf_counter() - start_time, 3)

        # Decoy-state analysis (only if WCP source was used)
        decoy_result = None
        if wcp_pulses is not None:
            detected_orig_idx = [i for i, p in enumerate(wcp_pulses) if p.detected]
            error_flags = [False] * len(wcp_pulses)
            for trial_j, orig_i in enumerate(detected_orig_idx):
                if alice_bases[trial_j] == bob_bases[trial_j]:
                    if bob_results[trial_j] != alice_bits[trial_j]:
                        error_flags[orig_i] = True

            per_int = aggregate_by_intensity(wcp_pulses, error_flags)
            sig_row = find_intensity(per_int, mu_signal) or {"gain": 0.0, "qber": 0.0}
            dec_row = find_intensity(per_int, mu_decoy) or {"gain": 0.0, "qber": 0.0}
            vac_row = find_intensity(per_int, 0.0) or {"gain": 0.0}
            Q_mu, E_mu = sig_row["gain"], sig_row["qber"]
            Q_nu, E_nu = dec_row["gain"], dec_row["qber"]
            Q_0 = vac_row["gain"]

            bounds = decoy_analysis(Q_mu, Q_nu, Q_0, E_mu, E_nu, mu_signal, mu_decoy)
            R_secure = secure_key_rate(
                Q_mu, E_mu, bounds.get("Q_1", 0.0), bounds.get("e_1", 0.5)
            )
            multi_photon = sum(1 for p in wcp_pulses if p.pns_vulnerable)

            decoy_result = {
                "per_intensity": per_int,
                "mu_signal": mu_signal,
                "mu_decoy": mu_decoy,
                "bounds": bounds,
                "secure_key_rate": round(R_secure, 6),
                "pns_vulnerable": multi_photon,
                "multi_photon_fraction": round(multi_photon / len(wcp_pulses), 4),
                "n_pulses": len(wcp_pulses),
                "n_detected": sum(1 for p in wcp_pulses if p.detected),
            }

        await session_manager.send_event(session_id, {
            "type": "result",
            "n_qubits_sent": n_sent,
            "n_qubits_received": n_qubits,
            "transmission_efficiency": round(eta, 4),
            "channel_distance_km": channel_km,
            "sifted_key_length": len(alice_key),
            "bits_after_ec": len(corrected_alice),
            "final_key_length": len(final_key) * 4,
            "qber": final_qber,
            "is_secure": secure,
            "final_key": final_key,
            "elapsed_seconds": elapsed,
            "mode": mode,
            "ibm_backend": ibm_backend_name if mode == "ibm_hardware" else None,
            "ec_method": ec_method,
            "ec_stats": ec_stats,
            "source_type": source_type,
            "decoy_state": decoy_result,
            "ml_prediction": ml_predict(extract_features_from_dict({
                "qber": final_qber,
                "sifted_key_length": len(alice_key),
                "depolarizing_prob": dep_prob,
                "measurement_error_prob": meas_prob,
                "channel_distance_km": channel_km,
                "n_qubits": n_sent,
            })),
            "smart_eve": (
                {
                    "target_qber": smart_target_qber,
                    "total_intercepted": smart_eve_state.total_intercepted,
                    "interception_rates": smart_eve_state.interception_rates,
                    "observed_qber_trace": smart_eve_state.observed_qber_trace,
                    "intercept_fraction": round(
                        smart_eve_state.total_intercepted / max(len(smart_eve_state.intercepts), 1), 4
                    ),
                }
                if smart_eve_state is not None
                else None
            ),
        })

        db = SessionLocal()
        try:
            db.add(SimulationRun(
                n_qubits=n_sent,
                depolarizing_prob=dep_prob,
                measurement_error_prob=meas_prob,
                eve_intercept=eve_intercept,
                sifted_key_length=len(alice_key),
                qber=final_qber,
                is_secure=secure,
                final_key=final_key,
                channel_distance_km=channel_km,
                user_id=ws_user_id,
            ))
            db.commit()
            log.info("Saved run to DB (mode=%s, qber=%.4f, sifted=%d)", mode, final_qber, len(alice_key))
        except Exception as exc:
            db.rollback()
            log.error("Failed to save simulation run: %s", exc)
        finally:
            db.close()

    except WebSocketDisconnect:
        pass
    finally:
        session_manager.disconnect(session_id)


async def _run_ibm(session_id, circuits, n_qubits, backend_name,
                   rng, eve_intercepts, eve_bases, alice_bases):
    """Run circuits on IBM Quantum hardware and return bob_results list."""
    from qiskit import transpile
    from qiskit_ibm_runtime import SamplerV2 as IBMSampler
    from quantum_logic.ibm_integration import get_ibm_service

    token = os.getenv("IBM_QUANTUM_TOKEN")
    if not token:
        await session_manager.send_event(session_id, {
            "type": "error",
            "message": "IBM_QUANTUM_TOKEN not set on the server.",
        })
        return None

    try:
        await session_manager.send_event(session_id, {
            "type": "status",
            "message": f"Connecting to {backend_name}...",
        })
        # All IBM calls are blocking — run them in a thread pool
        service = await asyncio.to_thread(get_ibm_service, token)
        backend = await asyncio.to_thread(service.backend, backend_name)

        await session_manager.send_event(session_id, {
            "type": "status",
            "message": f"Transpiling {n_qubits} circuits for {backend_name}...",
        })
        transpiled = await asyncio.to_thread(transpile, circuits, backend)

        sampler = IBMSampler(backend)
        job = await asyncio.to_thread(sampler.run, transpiled, shots=1)

        await session_manager.send_event(session_id, {
            "type": "status",
            "message": f"Job {job.job_id()} submitted. Waiting for IBM Quantum results (this may take several minutes)...",
        })

        # job.result() blocks until the job finishes — must be in thread
        result = await asyncio.to_thread(job.result)

        bob_results = []
        for i, pub_result in enumerate(result):
            counts = pub_result.data.c.get_counts()
            bob_result = int(max(counts, key=counts.get))
            if eve_intercepts and eve_intercepts[i] and eve_bases[i] != alice_bases[i]:
                bob_result = int(rng.integers(0, 2))
            bob_results.append(bob_result)

        log.info("IBM job complete on %s (%d qubits)", backend_name, n_qubits)
        return bob_results

    except Exception as exc:
        log.error("IBM hardware error: %s", exc)
        await session_manager.send_event(session_id, {
            "type": "error",
            "message": f"IBM hardware error: {exc}",
        })
        return None
