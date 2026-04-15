"""
WebSocket endpoint for real-time BB84 simulation streaming.

The client connects with a session_id, and the server streams qubit-level
events as the simulation progresses.
"""

import asyncio
import uuid
import numpy as np
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from api.websocket_manager import session_manager
from quantum_logic.bb84_circuit import build_bb84_circuits
from quantum_logic.noise_model import build_noise_model
from classical_processing.sifting import sift_keys
from classical_processing.qber import calculate_qber, is_channel_secure
from classical_processing.error_correction import correct_errors
from classical_processing.privacy_amplification import amplify_privacy
from qiskit_aer import AerSimulator

ws_router = APIRouter(tags=["websocket"])


@ws_router.websocket("/ws/simulate/{session_id}")
async def simulate_stream(websocket: WebSocket, session_id: str):
    """
    Stream BB84 simulation events in real-time.

    Message protocol:
        -> Client sends JSON: { "n_qubits": int, "depolarizing_prob": float, ... }
        <- Server sends per-qubit events: { "type": "qubit", "index": int, ... }
        <- Server sends final result:     { "type": "result", "qber": float, ... }
    """
    await session_manager.connect(session_id, websocket)
    try:
        config = await websocket.receive_json()
        n_qubits = config.get("n_qubits", 100)
        dep_prob = config.get("depolarizing_prob", 0.01)
        meas_prob = config.get("measurement_error_prob", 0.02)

        rng = np.random.default_rng()
        alice_bits = rng.integers(0, 2, n_qubits).tolist()
        alice_bases = rng.integers(0, 2, n_qubits).tolist()
        bob_bases = rng.integers(0, 2, n_qubits).tolist()

        noise_model = build_noise_model(dep_prob, meas_prob)
        simulator = AerSimulator(noise_model=noise_model)
        circuits = build_bb84_circuits(alice_bits, alice_bases, bob_bases)

        bob_results = []
        for i, qc in enumerate(circuits):
            job = simulator.run(qc, shots=1)
            counts = job.result().get_counts()
            result = int(max(counts, key=counts.get))
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
            await asyncio.sleep(0)  # Yield to event loop

        alice_key, bob_key = sift_keys(alice_bits, alice_bases, bob_results, bob_bases)
        qber = calculate_qber(alice_key, bob_key) if alice_key else 0.0
        secure = is_channel_secure(qber)
        corrected_alice, _ = correct_errors(alice_key, bob_key)
        final_key = amplify_privacy(corrected_alice) if corrected_alice else ""

        await session_manager.send_event(session_id, {
            "type": "result",
            "sifted_key_length": len(alice_key),
            "qber": round(qber, 4),
            "is_secure": secure,
            "final_key": final_key,
        })

    except WebSocketDisconnect:
        pass
    finally:
        session_manager.disconnect(session_id)
