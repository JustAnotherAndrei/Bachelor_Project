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
    decoy_analysis, secure_key_rate, apply_pns_attack,
)
from quantum_logic.smart_eve import smart_eve_decide
from quantum_logic.finite_key_analysis import finite_key_analysis
from quantum_logic.protocols import get_protocol, SUPPORTED_PROTOCOLS
from ml.eavesdrop_detector import predict as ml_predict, extract_features_from_dict
from ml import lstm_detector
from classical_processing.sifting import sift_keys
from classical_processing.qber import calculate_qber, is_channel_secure
from classical_processing.error_correction import correct_errors
from classical_processing.cascade import cascade_correct
from classical_processing.privacy_amplification import amplify_privacy
from qiskit_aer import AerSimulator
from database.db import SessionLocal
from database.models import SimulationRun

load_dotenv()


def _coerce_seed(raw) -> int | None:
    """Accept loose JSON shapes ("", null, "42", 42) and return int | None."""
    if raw is None or raw == "" or raw is False:
        return None
    try:
        return int(raw)
    except (TypeError, ValueError):
        return None
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
        protocol_name = config.get("protocol", "bb84")
        if protocol_name not in SUPPORTED_PROTOCOLS:
            protocol_name = "bb84"
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
        # Detector imperfections (η_det, dark counts). 1.0 / 0.0 = ideal detector.
        eta_det = float(config.get("detector_efficiency", 1.0))
        dark_count_rate = float(config.get("dark_count_rate", 0.0))
        # Optional reproducibility seed — coerce loose JSON shapes to int|None.
        seed = _coerce_seed(config.get("seed"))
        mu_signal = float(config.get("mu_signal", 0.5))
        mu_decoy = float(config.get("mu_decoy", 0.1))

        # ------------------------------------------------------------------
        # Dispatch alternative protocols (B92, SARG04, E91) to a dedicated
        # path. The BB84 path below retains decoy-state, smart-Eve, IBM
        # hardware, and all advanced features.
        # ------------------------------------------------------------------
        # Read WCP source params here too so we can forward them to the
        # alt-protocol path (B92/SARG04). E91 ignores them.
        p_signal = float(config.get("p_signal", 0.70))
        p_decoy = float(config.get("p_decoy", 0.15))

        if protocol_name != "bb84":
            await _run_alt_protocol(
                session_id=session_id,
                protocol_name=protocol_name,
                n_qubits=n_qubits,
                dep_prob=dep_prob, meas_prob=meas_prob,
                eve_mode=eve_mode,
                channel_km=channel_km, ec_method=ec_method,
                start_time=start_time, ws_user_id=ws_user_id,
                eta_det=eta_det, dark_count_rate=dark_count_rate, seed=seed,
                source_type=source_type,
                mu_signal=mu_signal, mu_decoy=mu_decoy,
                p_signal=p_signal, p_decoy=p_decoy,
            )
            return

        # Weak Eve intercepts 30% of qubits; strong Eve intercepts 100%.
        # PNS Eve does NOT do intercept-resend (no QBER added) — handled
        # separately inside the WCP source block.
        EVE_RATE = {"none": 0.0, "weak": 0.30, "strong": 1.0, "pns": 0.0}
        eve_intercept = eve_mode != "none"
        pns_attack_active = (eve_mode == "pns")
        pns_summary = None

        rng = np.random.default_rng(seed)
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
                # If PNS Eve is active, override the detection pattern: she
                # blocks single-photon pulses and splits multi-photon ones,
                # forwarding the remainder through a lossless channel.
                if pns_attack_active:
                    pns_summary = apply_pns_attack(wcp_pulses)
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

                # Detector imperfections: dark count overrides the click with a
                # spurious random bit; finite η_det randomises lost photons (we
                # keep the array dense rather than discarding so sifting stays
                # parallel — the missed click manifests as extra QBER, which is
                # the textbook outcome).
                if dark_count_rate > 0 and rng.random() < dark_count_rate:
                    result = int(rng.integers(0, 2))
                elif eta_det < 1.0 and rng.random() > eta_det:
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
            "protocol": "bb84",
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
            "lstm_prediction": lstm_detector.predict(
                alice_bits, alice_bases, bob_bases, bob_results,
            ),
            "ml_prediction": ml_predict(extract_features_from_dict({
                "qber": final_qber,
                "sifted_key_length": len(alice_key),
                "depolarizing_prob": dep_prob,
                "measurement_error_prob": meas_prob,
                "channel_distance_km": channel_km,
                "n_qubits": n_sent,
            })),
            "pns_attack": pns_summary,
            "finite_key": finite_key_analysis(len(alice_key), final_qber),
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
    instance = os.getenv("IBM_QUANTUM_INSTANCE")
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
        service = await asyncio.to_thread(get_ibm_service, token, instance)
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


# =====================================================================
# Alternative-protocol path (B92, SARG04, E91)
# =====================================================================

async def _run_alt_protocol(
    *,
    session_id: str,
    protocol_name: str,
    n_qubits: int,
    dep_prob: float, meas_prob: float,
    eve_mode: str,
    channel_km: float, ec_method: str,
    start_time: float, ws_user_id: int | None,
    eta_det: float = 1.0, dark_count_rate: float = 0.0,
    seed: int | None = None,
    source_type: str = "ideal",
    mu_signal: float = 0.5, mu_decoy: float = 0.1,
    p_signal: float = 0.7, p_decoy: float = 0.15,
):
    """
    Run a non-BB84 QKD protocol (B92, SARG04, or E91) end-to-end.

    Supports the same source model as the BB84 path (ideal single-photon or
    WCP + 3-intensity decoy state) plus PNS attacks. E91 forces ideal source
    because the protocol is entanglement-based — weak coherent pulses don't
    apply.
    """
    protocol = get_protocol(protocol_name)
    rng = np.random.default_rng(seed)

    # E91 is entanglement-based — WCP / decoy / PNS don't apply physically.
    if protocol.USES_ENTANGLEMENT and source_type == "wcp":
        source_type = "ideal"

    # PNS does not do intercept-resend (its threat is silent multi-photon
    # splitting). The existing "smart" branch is BB84-only, so we drop it
    # here and treat it as a weak attacker for the alt-protocol path.
    EVE_RATE = {"none": 0.0, "weak": 0.30, "strong": 1.0, "smart": 0.30, "pns": 0.0}
    eve_rate = EVE_RATE.get(eve_mode, 0.0)
    eve_intercept = eve_mode != "none"
    pns_attack_active = (eve_mode == "pns") and (source_type == "wcp")
    pns_summary = None

    # --- 1. Prepare state choices for the protocol ---
    prep = protocol.prepare(rng, n_qubits)
    n_sent = n_qubits

    def _filter_prep(mask):
        """Apply a boolean mask to every list-typed field of `prep`."""
        for fld in vars(prep):
            v = getattr(prep, fld, None)
            if v is not None and isinstance(v, list):
                setattr(prep, fld, [x for x, keep in zip(v, mask) if keep])

    # --- 2. Source / channel: either WCP (decoy + optional PNS) or ideal+loss ---
    eta = 1.0
    wcp_pulses = None
    if source_type == "wcp":
        # WCP folds channel transmittance into per-pulse survival, so don't
        # double-apply the channel loss step.
        eta = channel_transmittance(channel_km) if channel_km > 0 else 1.0
        wcp_pulses = simulate_wcp_pulses(
            n_qubits, mu_signal, mu_decoy, p_signal, p_decoy, eta, rng,
        )
        if pns_attack_active:
            pns_summary = apply_pns_attack(wcp_pulses)
        detected_mask = [p.detected for p in wcp_pulses]
        _filter_prep(detected_mask)
        n_qubits = len(getattr(prep, "alice_bases", []) or
                       getattr(prep, "alice_bits", []))
    elif channel_km > 0:
        eta = channel_transmittance(channel_km)
        survive_mask = (rng.random(n_qubits) < eta).tolist()
        _filter_prep(survive_mask)
        n_qubits = len(getattr(prep, "alice_bases", []) or
                       getattr(prep, "alice_bits", []))

    if n_qubits == 0:
        await session_manager.send_event(session_id, {
            "type": "error",
            "message": f"All {n_sent} photons lost in {channel_km} km. "
                       "Reduce distance, increase qubit count, or raise μ.",
        })
        return

    # --- 3. Eve: per-qubit interception mask (intercept-resend) ---
    eve_intercepts = (rng.random(n_qubits) < eve_rate).tolist() if eve_intercept else None

    # --- 4. Build circuits and run on the Aer simulator ---
    circuits = protocol.build_circuits(prep)
    noise_model = build_noise_model(dep_prob, meas_prob)
    simulator = AerSimulator(noise_model=noise_model)

    bob_results: list[int] = []
    alice_meas: list[int] = []  # populated only for E91 (entangled measurements)

    for i, qc in enumerate(circuits):
        job = simulator.run(qc, shots=1)
        counts = job.result().get_counts()

        if protocol.USES_ENTANGLEMENT:
            # Two-qubit result: 'ba' bitstring -> (alice_bit, bob_bit)
            from quantum_logic.protocols.e91 import parse_two_qubit_result
            a_bit, b_bit = parse_two_qubit_result(counts)
            # When Eve intercepts one photon of the entangled pair she
            # collapses the Bell state; Alice and Bob are left with
            # independent random outcomes, destroying the CHSH correlations.
            eve_did_intercept = bool(eve_intercepts[i]) if eve_intercepts else False
            if eve_did_intercept:
                a_bit = int(rng.integers(0, 2))
                b_bit = int(rng.integers(0, 2))
            # Detector imperfections affect Bob's side (Alice's measurement is
            # treated as a trusted source-side outcome here).
            if dark_count_rate > 0 and rng.random() < dark_count_rate:
                b_bit = int(rng.integers(0, 2))
            elif eta_det < 1.0 and rng.random() > eta_det:
                b_bit = int(rng.integers(0, 2))
            alice_meas.append(a_bit)
            bob_results.append(b_bit)
            await session_manager.send_event(session_id, {
                "type": "qubit",
                "index": i,
                "alice_bit": a_bit,
                "alice_basis": prep.alice_bases[i],
                "bob_basis": prep.bob_bases[i],
                "bob_result": b_bit,
                "basis_match": (prep.alice_bases[i], prep.bob_bases[i]) in {(1, 0), (2, 1)},
                "eve_intercept": eve_did_intercept,
            })
        else:
            result = int(max(counts, key=counts.get))
            # Single-qubit intercept-resend: Eve guesses a basis; if she picks
            # a different basis than Alice did, the resent state is randomised.
            if eve_intercepts and eve_intercepts[i]:
                eve_basis = int(rng.integers(0, 2))
                if eve_basis != prep.alice_bases[i]:
                    result = int(rng.integers(0, 2))
            # Detector imperfections (same model as the BB84 path).
            if dark_count_rate > 0 and rng.random() < dark_count_rate:
                result = int(rng.integers(0, 2))
            elif eta_det < 1.0 and rng.random() > eta_det:
                result = int(rng.integers(0, 2))
            bob_results.append(result)
            await session_manager.send_event(session_id, {
                "type": "qubit",
                "index": i,
                "alice_bit": prep.alice_bits[i],
                "alice_basis": prep.alice_bases[i],
                "bob_basis": prep.bob_bases[i],
                "bob_result": result,
                "basis_match": prep.alice_bases[i] == prep.bob_bases[i],
                "eve_intercept": bool(eve_intercepts[i]) if eve_intercepts else False,
            })
        await asyncio.sleep(0)

    # --- 5. Protocol-specific sifting ---
    if protocol.USES_ENTANGLEMENT:
        prep.alice_bits = alice_meas
    alice_key, bob_key, sift_meta = protocol.sift(prep, bob_results)
    qber = calculate_qber(alice_key, bob_key) if alice_key else 0.0
    secure = is_channel_secure(qber)

    # --- 6. Error correction + privacy amplification ---
    ec_stats = None
    if ec_method == "cascade" and alice_key:
        corrected_alice, _, ec_stats = cascade_correct(alice_key, bob_key, max(qber, 0.001))
    else:
        corrected_alice, _ = correct_errors(alice_key, bob_key)

    final_key = amplify_privacy(corrected_alice) if corrected_alice else ""
    final_qber = round(qber, 4)
    elapsed = round(time.perf_counter() - start_time, 3)

    # --- 6a. Decoy-state analysis (mirrors the BB84 path) ---
    # We use basis-match-bit-mismatch as the error proxy. For B92/SARG04 the
    # full sifting predicate is stricter, but the gain signature (Y_1 collapse
    # under PNS) doesn't depend on the exact per-error counting, so it's a
    # defensible approximation for the decoy bounds.
    decoy_result = None
    if wcp_pulses is not None and not protocol.USES_ENTANGLEMENT:
        detected_orig_idx = [i for i, p in enumerate(wcp_pulses) if p.detected]
        error_flags = [False] * len(wcp_pulses)
        a_bases = getattr(prep, "alice_bases", None) or []
        b_bases = getattr(prep, "bob_bases", None) or []
        a_bits = getattr(prep, "alice_bits", None) or []
        for trial_j, orig_i in enumerate(detected_orig_idx):
            if (trial_j < len(a_bases) and trial_j < len(b_bases)
                    and a_bases[trial_j] == b_bases[trial_j]
                    and trial_j < len(a_bits)
                    and bob_results[trial_j] != a_bits[trial_j]):
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

    # --- 7. Send final result ---
    await session_manager.send_event(session_id, {
        "type": "result",
        "protocol": protocol_name,
        "protocol_display_name": protocol.DISPLAY_NAME,
        "n_qubits_sent": n_sent,
        "n_qubits_received": n_qubits,
        "transmission_efficiency": round(eta, 4),
        "channel_distance_km": channel_km,
        "sifted_key_length": len(alice_key),
        "sifting_efficiency": round(sift_meta.get("sifting_efficiency", 0.0), 4),
        "bits_after_ec": len(corrected_alice),
        "final_key_length": len(final_key) * 4,
        "qber": final_qber,
        "is_secure": secure,
        "final_key": final_key,
        "elapsed_seconds": elapsed,
        "mode": "simulator",
        "ec_method": ec_method,
        "ec_stats": ec_stats,
        "source_type": source_type,
        "decoy_state": decoy_result,
        "pns_attack": pns_summary,
        "finite_key": finite_key_analysis(len(alice_key), final_qber),
        # LSTM was trained on BB84-style {alice,bob}_basis ∈ {0,1}; B92/SARG04
        # share that schema (E91 uses angle indices 0/1/2 — skipped here).
        "lstm_prediction": (
            lstm_detector.predict(
                prep.alice_bits, prep.alice_bases, prep.bob_bases, bob_results,
            ) if not protocol.USES_ENTANGLEMENT else None
        ),
        # Bell test data for E91 (None for B92/SARG04)
        "bell_test": (
            {
                "chsh_S": sift_meta.get("chsh_S"),
                "quantum_bound": sift_meta.get("quantum_bound"),
                "bell_violation": sift_meta.get("bell_violation"),
                "chsh_terms": sift_meta.get("chsh_terms"),
            }
            if "chsh_S" in sift_meta else None
        ),
    })

    # --- 8. Persist run ---
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
        log.info("Saved %s run to DB (qber=%.4f, sifted=%d)",
                 protocol_name, final_qber, len(alice_key))
    except Exception as exc:
        db.rollback()
        log.error("Failed to save %s run: %s", protocol_name, exc)
    finally:
        db.close()
