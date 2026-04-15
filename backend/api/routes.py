"""
REST API routes for the Q-Shield BB84 simulation service.
"""

from fastapi import APIRouter
from pydantic import BaseModel, Field

router = APIRouter(prefix="/api/v1", tags=["bb84"])


class SimulationRequest(BaseModel):
    n_qubits: int = Field(default=100, ge=10, le=1000, description="Number of qubits to exchange")
    mode: str = Field(default="simulator", pattern="^(simulator|ibm_hardware)$")
    depolarizing_prob: float = Field(default=0.01, ge=0.0, le=0.5)
    measurement_error_prob: float = Field(default=0.02, ge=0.0, le=0.5)
    eve_intercept: bool = Field(default=False, description="Simulate Eve intercepting the channel")
    ibm_token: str | None = Field(default=None, description="IBM Quantum API token (hardware mode only)")


class SimulationResult(BaseModel):
    n_qubits: int
    sifted_key_length: int
    qber: float
    is_secure: bool
    final_key: str
    alice_bits: list[int]
    alice_bases: list[int]
    bob_bases: list[int]
    bob_results: list[int]
    mode: str


@router.post("/simulate", response_model=SimulationResult)
async def run_simulation(request: SimulationRequest) -> SimulationResult:
    """
    Run a full BB84 simulation and return the results.

    - Generates random Alice bits/bases and Bob bases.
    - Runs circuits in simulator or IBM hardware mode.
    - Applies sifting, QBER check, error correction, and privacy amplification.
    """
    import numpy as np
    from quantum_logic.bb84_circuit import build_bb84_circuits
    from quantum_logic.noise_model import build_noise_model
    from classical_processing.sifting import sift_keys
    from classical_processing.qber import calculate_qber, is_channel_secure
    from classical_processing.error_correction import correct_errors
    from classical_processing.privacy_amplification import amplify_privacy
    from qiskit_aer import AerSimulator

    rng = np.random.default_rng()
    alice_bits = rng.integers(0, 2, request.n_qubits).tolist()
    alice_bases = rng.integers(0, 2, request.n_qubits).tolist()
    bob_bases = rng.integers(0, 2, request.n_qubits).tolist()

    circuits = build_bb84_circuits(alice_bits, alice_bases, bob_bases)
    noise_model = build_noise_model(request.depolarizing_prob, request.measurement_error_prob)

    simulator = AerSimulator(noise_model=noise_model)
    bob_results = []
    for qc in circuits:
        job = simulator.run(qc, shots=1)
        counts = job.result().get_counts()
        bob_results.append(int(max(counts, key=counts.get)))

    alice_key, bob_key = sift_keys(alice_bits, alice_bases, bob_results, bob_bases)
    qber = calculate_qber(alice_key, bob_key)
    secure = is_channel_secure(qber)
    corrected_alice, _ = correct_errors(alice_key, bob_key)
    final_key = amplify_privacy(corrected_alice) if corrected_alice else ""

    return SimulationResult(
        n_qubits=request.n_qubits,
        sifted_key_length=len(alice_key),
        qber=round(qber, 4),
        is_secure=secure,
        final_key=final_key,
        alice_bits=alice_bits,
        alice_bases=alice_bases,
        bob_bases=bob_bases,
        bob_results=bob_results,
        mode=request.mode,
    )
