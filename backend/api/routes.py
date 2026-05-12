from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from database.db import get_db
from database.models import SimulationRun

router = APIRouter(prefix="/api/v1", tags=["bb84"])


class SimulationRequest(BaseModel):
    n_qubits: int = Field(default=100, ge=10, le=1000)
    mode: str = Field(default="simulator", pattern="^(simulator|ibm_hardware)$")
    depolarizing_prob: float = Field(default=0.01, ge=0.0, le=0.5)
    measurement_error_prob: float = Field(default=0.02, ge=0.0, le=0.5)
    eve_intercept: bool = Field(default=False)
    ibm_token: str | None = Field(default=None)


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
async def run_simulation(request: SimulationRequest, db: Session = Depends(get_db)):
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
    eve_bases = rng.integers(0, 2, request.n_qubits).tolist() if request.eve_intercept else None
    for i, qc in enumerate(circuits):
        job = simulator.run(qc, shots=1)
        counts = job.result().get_counts()
        result = int(max(counts, key=counts.get))
        if request.eve_intercept and eve_bases[i] != alice_bases[i]:
            result = int(rng.integers(0, 2))
        bob_results.append(result)

    alice_key, bob_key = sift_keys(alice_bits, alice_bases, bob_results, bob_bases)
    qber = calculate_qber(alice_key, bob_key)
    secure = is_channel_secure(qber)
    corrected_alice, _ = correct_errors(alice_key, bob_key)
    final_key = amplify_privacy(corrected_alice) if corrected_alice else ""

    db.add(SimulationRun(
        n_qubits=request.n_qubits,
        depolarizing_prob=request.depolarizing_prob,
        measurement_error_prob=request.measurement_error_prob,
        eve_intercept=request.eve_intercept,
        sifted_key_length=len(alice_key),
        qber=round(qber, 4),
        is_secure=secure,
        final_key=final_key,
    ))
    db.commit()

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


@router.get("/history")
def get_history(limit: int = 50, db: Session = Depends(get_db)):
    runs = (
        db.query(SimulationRun)
        .order_by(SimulationRun.id.desc())
        .limit(limit)
        .all()
    )
    return [
        {
            "id": r.id,
            "created_at": r.created_at.isoformat(),
            "n_qubits": r.n_qubits,
            "eve_intercept": r.eve_intercept,
            "sifted_key_length": r.sifted_key_length,
            "qber": r.qber,
            "is_secure": r.is_secure,
        }
        for r in reversed(runs)
    ]


@router.delete("/history")
def clear_history(db: Session = Depends(get_db)):
    deleted = db.query(SimulationRun).delete()
    db.commit()
    return {"deleted": deleted}
