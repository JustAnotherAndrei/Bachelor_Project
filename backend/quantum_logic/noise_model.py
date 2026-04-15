"""
Configurable Qiskit noise model for the BB84 simulator.

Implements depolarizing_error (gate noise) and pauli_error (measurement noise)
as required by the project constraints.
"""

from qiskit_aer.noise import (
    NoiseModel,
    depolarizing_error,
    pauli_error,
)


def build_noise_model(
    depolarizing_prob: float = 0.01,
    measurement_error_prob: float = 0.02,
) -> NoiseModel:
    """
    Build a noise model with depolarizing gate error and Pauli measurement error.

    Args:
        depolarizing_prob:      Probability of depolarizing error on single-qubit gates.
        measurement_error_prob: Probability of bit-flip during measurement.

    Returns:
        A configured Qiskit NoiseModel.
    """
    noise_model = NoiseModel()

    # Depolarizing error on all single-qubit gates (X, H)
    dep_error = depolarizing_error(depolarizing_prob, 1)
    noise_model.add_all_qubit_quantum_error(dep_error, ["x", "h"])

    # Pauli measurement error: P(0->1) = P(1->0) = measurement_error_prob
    p = measurement_error_prob
    meas_error = pauli_error([("X", p), ("I", 1 - p)])
    noise_model.add_all_qubit_quantum_error(meas_error, ["measure"])

    return noise_model
