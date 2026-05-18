"""
IBM Quantum Runtime integration for running BB84 circuits on real hardware.

Uses Qiskit IBM Runtime (SamplerV2) with the new ibm_cloud channel.
"""

from qiskit_ibm_runtime import QiskitRuntimeService, SamplerV2 as Sampler
from qiskit import QuantumCircuit


def get_ibm_service(token: str, instance: str = "open-instance") -> QiskitRuntimeService:
    """
    Authenticate with IBM Quantum (new platform) and return the service object.

    Args:
        token:    IBM Cloud API key.
        instance: Service instance name. Default is "open-instance" (free/trial plan).

    Returns:
        An authenticated QiskitRuntimeService.
    """
    return QiskitRuntimeService(channel="ibm_cloud", token=token, instance=instance)


def list_available_backends(service: QiskitRuntimeService) -> list[str]:
    """Return names of all operational backends on this account."""
    return [b.name for b in service.backends(operational=True)]


def run_on_ibm(
    circuits: list[QuantumCircuit],
    service: QiskitRuntimeService,
    backend_name: str = "ibm_fez",
    shots: int = 1,
) -> list[int]:
    """
    Execute BB84 circuits on a real IBM Quantum backend.

    Args:
        circuits:     List of transpiled QuantumCircuits to run.
        service:      Authenticated QiskitRuntimeService.
        backend_name: Name of the IBM backend to target.
        shots:        Number of shots per circuit.

    Returns:
        List of measurement outcomes (0 or 1) per circuit.
    """
    backend = service.backend(backend_name)
    sampler = Sampler(backend)
    job = sampler.run(circuits, shots=shots)
    result = job.result()

    outcomes = []
    for pub_result in result:
        counts = pub_result.data.c.get_counts()
        # Take the most frequent outcome for a single-shot protocol
        outcome = int(max(counts, key=counts.get))
        outcomes.append(outcome)

    return outcomes
