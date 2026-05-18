"""
WebSocket endpoint for real-time BB84 simulation streaming.

The client connects with a session_id, and the server streams qubit-level
events as the simulation progresses.
"""

import asyncio
import logging
import os
import numpy as np
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from dotenv import load_dotenv

from api.websocket_manager import session_manager
from quantum_logic.bb84_circuit import build_bb84_circuits
from quantum_logic.noise_model import build_noise_model
from classical_processing.sifting import sift_keys
from classical_processing.qber import calculate_qber, is_channel_secure
from classical_processing.error_correction import correct_errors
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
        config = await websocket.receive_json()
        n_qubits = config.get("n_qubits", 100)
        dep_prob = config.get("depolarizing_prob", 0.01)
        meas_prob = config.get("measurement_error_prob", 0.02)
        eve_mode = config.get("eve_mode", "none")   # 'none' | 'weak' | 'strong'
        mode = config.get("mode", "simulator")
        ibm_backend_name = config.get("ibm_backend", "ibm_fez")

        # Weak Eve intercepts 30% of qubits; strong Eve intercepts 100%
        EVE_RATE = {"none": 0.0, "weak": 0.30, "strong": 1.0}
        eve_intercept = eve_mode != "none"

        rng = np.random.default_rng()
        alice_bits = rng.integers(0, 2, n_qubits).tolist()
        alice_bases = rng.integers(0, 2, n_qubits).tolist()
        bob_bases = rng.integers(0, 2, n_qubits).tolist()

        if eve_intercept:
            rate = EVE_RATE[eve_mode]
            eve_intercepts = (rng.random(n_qubits) < rate).tolist()
            eve_bases = rng.integers(0, 2, n_qubits).tolist()
        else:
            eve_intercepts = None
            eve_bases = None

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
                })
                await asyncio.sleep(0)

        alice_key, bob_key = sift_keys(alice_bits, alice_bases, bob_results, bob_bases)
        qber = calculate_qber(alice_key, bob_key) if alice_key else 0.0
        secure = is_channel_secure(qber)
        corrected_alice, _ = correct_errors(alice_key, bob_key)
        final_key = amplify_privacy(corrected_alice) if corrected_alice else ""
        final_qber = round(qber, 4)

        await session_manager.send_event(session_id, {
            "type": "result",
            "sifted_key_length": len(alice_key),
            "qber": final_qber,
            "is_secure": secure,
            "final_key": final_key,
            "mode": mode,
            "ibm_backend": ibm_backend_name if mode == "ibm_hardware" else None,
        })

        db = SessionLocal()
        try:
            db.add(SimulationRun(
                n_qubits=n_qubits,
                depolarizing_prob=dep_prob,
                measurement_error_prob=meas_prob,
                eve_intercept=eve_intercept,  # True for weak or strong
                sifted_key_length=len(alice_key),
                qber=final_qber,
                is_secure=secure,
                final_key=final_key,
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
