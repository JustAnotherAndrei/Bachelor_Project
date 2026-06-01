"""
BB84 protocol — reference implementation, wrapped for the multi-protocol API.

Alice picks (bit, basis) uniformly at random, encodes one of |0>, |1>, |+>, |->,
Bob picks a basis uniformly and measures. Sifting keeps positions where the
two bases agree (~50% retention).
"""

from dataclasses import dataclass
from typing import Any
import numpy as np
from qiskit import QuantumCircuit

NAME = "bb84"
DISPLAY_NAME = "BB84"
USES_ENTANGLEMENT = False
SIFTING_EFFICIENCY = 0.50  # asymptotic
QBER_UNDER_STRONG_EVE = 0.25


@dataclass
class Preparation:
    alice_bits: list[int]
    alice_bases: list[int]
    bob_bases: list[int]


def prepare(rng: np.random.Generator, n_qubits: int) -> Preparation:
    return Preparation(
        alice_bits=rng.integers(0, 2, n_qubits).tolist(),
        alice_bases=rng.integers(0, 2, n_qubits).tolist(),
        bob_bases=rng.integers(0, 2, n_qubits).tolist(),
    )


def build_circuits(prep: Preparation) -> list[QuantumCircuit]:
    circuits = []
    for bit, a_basis, b_basis in zip(prep.alice_bits, prep.alice_bases, prep.bob_bases):
        qc = QuantumCircuit(1, 1)
        if bit == 1:
            qc.x(0)
        if a_basis == 1:
            qc.h(0)
        if b_basis == 1:
            qc.h(0)
        qc.measure(0, 0)
        circuits.append(qc)
    return circuits


def sift(prep: Preparation, bob_results: list[int]) -> tuple[list[int], list[int], dict[str, Any]]:
    alice_key, bob_key = [], []
    kept_indices = []
    for i, (a_bit, a_basis, b_bit, b_basis) in enumerate(
        zip(prep.alice_bits, prep.alice_bases, bob_results, prep.bob_bases)
    ):
        if a_basis == b_basis:
            alice_key.append(a_bit)
            bob_key.append(b_bit)
            kept_indices.append(i)
    meta = {
        "kept_indices": kept_indices,
        "sifting_efficiency": len(kept_indices) / max(len(prep.alice_bits), 1),
    }
    return alice_key, bob_key, meta
