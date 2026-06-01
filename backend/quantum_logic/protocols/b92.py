"""
B92 protocol (Bennett 1992).

A simplification of BB84 that uses only **two** non-orthogonal states:

    bit 0  --> |0>     (Z eigenstate)
    bit 1  --> |+>     (X eigenstate)

Bob picks a measurement basis uniformly at random (Z or X). Only *conclusive*
measurement outcomes survive sifting:

    Bob in Z, result 1  --> Alice's bit was 1   (|0> can never yield 1 in Z)
    Bob in X, result 1  --> Alice's bit was 0   (|+> can never yield - in X)

Any other outcome is *inconclusive* and discarded. Under ideal conditions the
sifting efficiency is therefore only 25%, half that of BB84, in exchange for a
simpler physical setup (fewer state-preparation hardware paths). B92 is also
more vulnerable to intercept-resend attacks, because there is no basis-
mismatch detection mechanism — Eve who guesses correctly produces no error.

References:
    C. H. Bennett, "Quantum cryptography using any two nonorthogonal states",
    Phys. Rev. Lett. 68(21), pp. 3121-3124, 1992.
"""

from dataclasses import dataclass
from typing import Any
import numpy as np
from qiskit import QuantumCircuit

NAME = "b92"
DISPLAY_NAME = "B92"
USES_ENTANGLEMENT = False
SIFTING_EFFICIENCY = 0.25
QBER_UNDER_STRONG_EVE = 0.25


@dataclass
class Preparation:
    alice_bits: list[int]
    alice_bases: list[int]  # derived from bits: 0->Z, 1->X
    bob_bases: list[int]    # random Z/X


def prepare(rng: np.random.Generator, n_qubits: int) -> Preparation:
    alice_bits = rng.integers(0, 2, n_qubits).tolist()
    # In B92, the basis is fully determined by the bit:
    #   bit 0 prepared in Z (|0>),  bit 1 prepared in X (|+>)
    alice_bases = list(alice_bits)
    bob_bases = rng.integers(0, 2, n_qubits).tolist()
    return Preparation(alice_bits=alice_bits, alice_bases=alice_bases, bob_bases=bob_bases)


def build_circuits(prep: Preparation) -> list[QuantumCircuit]:
    circuits = []
    for bit, b_basis in zip(prep.alice_bits, prep.bob_bases):
        qc = QuantumCircuit(1, 1)
        # bit=0 -> |0> (no gate). bit=1 -> |+> (apply H to |0>).
        if bit == 1:
            qc.h(0)
        if b_basis == 1:  # measure in X-basis: rotate, then measure in Z
            qc.h(0)
        qc.measure(0, 0)
        circuits.append(qc)
    return circuits


def sift(prep: Preparation, bob_results: list[int]) -> tuple[list[int], list[int], dict[str, Any]]:
    """
    Conclusive-outcome sifting:
        Bob Z, result 1  -> infer Alice bit = 1
        Bob X, result 1  -> infer Alice bit = 0    (X-result "1" after H == |->)
    """
    alice_key, bob_key = [], []
    kept_indices = []
    for i, (a_bit, b_bit, b_basis) in enumerate(zip(prep.alice_bits, bob_results, prep.bob_bases)):
        inferred = None
        if b_basis == 0 and b_bit == 1:
            inferred = 1
        elif b_basis == 1 and b_bit == 1:
            inferred = 0
        if inferred is not None:
            alice_key.append(a_bit)
            bob_key.append(inferred)
            kept_indices.append(i)
    meta = {
        "kept_indices": kept_indices,
        "sifting_efficiency": len(kept_indices) / max(len(prep.alice_bits), 1),
    }
    return alice_key, bob_key, meta
