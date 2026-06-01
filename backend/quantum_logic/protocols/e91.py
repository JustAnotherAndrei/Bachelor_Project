"""
E91 protocol (Ekert 1991).

E91 is an entanglement-based QKD protocol. A central source emits pairs of
photons in the maximally-entangled Bell state

    |Phi+> = (|00> + |11>) / sqrt(2)

One photon of each pair goes to Alice, the other to Bob. They independently
choose a measurement angle from their respective triplets of bases:

    Alice angles:   a1 = 0°,    a2 = 22.5°, a3 = 45°
    Bob angles:     b1 = 22.5°, b2 = 45°,   b3 = 67.5°

These are the canonical CHSH-violating choices. Two of the nine (a_i, b_j)
combinations produce perfectly correlated outcomes in the noise-free case ---
the matching pairs (a2, b1) at 22.5° and (a3, b2) at 45°. Bits from these
"key rounds" become the sifted key. The remaining mismatched rounds are not
discarded but used to compute the CHSH correlator

    S = E(a1, b1) - E(a1, b3) + E(a3, b1) + E(a3, b3)

If the channel and source are honest, quantum mechanics predicts |S| = 2*sqrt(2)
~= 2.828 (violation of Bell's inequality). Any intercept-resend Eve replaces
the entangled pair with a separable mixture, driving |S| down toward 2 or
below. The security check therefore is |S| > 2 + delta, rather than a
QBER threshold.

This file implements E91 with two-qubit Qiskit circuits that prepare |Phi+>
and apply per-party rotations before Z-basis measurement.

References:
    A. K. Ekert, "Quantum cryptography based on Bell's theorem",
    Phys. Rev. Lett. 67, pp. 661-663, 1991.
"""

from dataclasses import dataclass
from typing import Any
import math
import numpy as np
from qiskit import QuantumCircuit

NAME = "e91"
DISPLAY_NAME = "E91"
USES_ENTANGLEMENT = True
SIFTING_EFFICIENCY = 2 / 9       # only (a2, b1) and (a3, b2) yield key bits
QBER_UNDER_STRONG_EVE = 0.25


# Measurement angles in radians (canonical CHSH-violating choice).
# Alice:  0°,    22.5°, 45°
# Bob:    22.5°, 45°,   67.5°
ALICE_ANGLES_RAD = [0.0, math.pi / 8, math.pi / 4]
BOB_ANGLES_RAD   = [math.pi / 8, math.pi / 4, 3 * math.pi / 8]

# Indices (a_i, b_j) producing perfectly correlated rounds (key rounds)
# (a2,b1) -> both at 22.5°; (a3,b2) -> both at 45°
KEY_ROUNDS = {(1, 0), (2, 1)}
# CHSH rounds used for the Bell test (S = E(a1,b1) - E(a1,b3) + E(a3,b1) + E(a3,b3))
CHSH_ROUNDS = {
    (0, 0): +1,   # E(a1, b1) sign +
    (0, 2): -1,   # E(a1, b3) sign -
    (2, 0): +1,   # E(a3, b1) sign +
    (2, 2): +1,   # E(a3, b3) sign +
}


@dataclass
class Preparation:
    alice_bases: list[int]   # 0,1,2 indexing ALICE_ANGLES
    bob_bases: list[int]     # 0,1,2 indexing BOB_ANGLES
    alice_bits: list[int]    # filled in by measurement; placeholder for now
    bob_bases_arg: list[int] # alias kept for API symmetry with other protocols


def prepare(rng: np.random.Generator, n_qubits: int) -> Preparation:
    a_bases = rng.integers(0, 3, n_qubits).tolist()
    b_bases = rng.integers(0, 3, n_qubits).tolist()
    return Preparation(
        alice_bases=a_bases,
        bob_bases=b_bases,
        alice_bits=[0] * n_qubits,   # populated after circuit execution
        bob_bases_arg=b_bases,
    )


def build_circuits(prep: Preparation) -> list[QuantumCircuit]:
    """
    Build per-round 2-qubit circuits:
        q0 = Alice's photon, q1 = Bob's photon
        Prepare |Phi+> = (|00> + |11>) / sqrt(2) via H + CX,
        rotate each qubit by its chosen angle (Ry(-2*theta) gives Z-basis
        readout equivalent to measuring in the rotated basis), then measure.
    """
    circuits = []
    for a_idx, b_idx in zip(prep.alice_bases, prep.bob_bases):
        qc = QuantumCircuit(2, 2)
        # Entangle the pair
        qc.h(0)
        qc.cx(0, 1)
        # Rotate each qubit to its measurement basis
        qc.ry(-2 * ALICE_ANGLES_RAD[a_idx], 0)
        qc.ry(-2 * BOB_ANGLES_RAD[b_idx], 1)
        qc.measure(0, 0)
        qc.measure(1, 1)
        circuits.append(qc)
    return circuits


def parse_two_qubit_result(counts: dict[str, int]) -> tuple[int, int]:
    """
    Qiskit returns bitstrings little-endian: 'c1 c0'. We measured q0 into c0
    (Alice) and q1 into c1 (Bob), so the most-likely bitstring 'b a' gives
    Alice bit = a, Bob bit = b.
    """
    best = max(counts, key=counts.get).replace(" ", "")
    if len(best) == 1:        # single-bit fallback
        return int(best), int(best)
    return int(best[-1]), int(best[-2])  # (alice_bit, bob_bit)


def sift(prep: Preparation, bob_results: list[int]) -> tuple[list[int], list[int], dict[str, Any]]:
    """
    Inputs:
        prep.alice_bits  : populated with Alice's q0 measurement outcomes
        bob_results      : list of Bob's q1 measurement outcomes

    Sifting keeps rounds whose (a, b) angle indices are in KEY_ROUNDS.
    The CHSH correlator S is estimated from the remaining rounds.
    """
    alice_key, bob_key = [], []
    kept_indices = []
    chsh_terms: dict[tuple[int, int], list[int]] = {k: [] for k in CHSH_ROUNDS}

    for i, (a_idx, b_idx, a_bit, b_bit) in enumerate(
        zip(prep.alice_bases, prep.bob_bases, prep.alice_bits, bob_results)
    ):
        if (a_idx, b_idx) in KEY_ROUNDS:
            alice_key.append(a_bit)
            bob_key.append(b_bit)
            kept_indices.append(i)
        elif (a_idx, b_idx) in CHSH_ROUNDS:
            # Map bits {0,1} to spins {+1,-1} for the correlator
            a_spin = 1 if a_bit == 0 else -1
            b_spin = 1 if b_bit == 0 else -1
            chsh_terms[(a_idx, b_idx)].append(a_spin * b_spin)

    # Compute Bell parameter S = sum over CHSH rounds of sign * mean correlation
    chsh_S = 0.0
    chsh_evidence = {}
    for (a, b), spins in chsh_terms.items():
        if spins:
            E_ab = sum(spins) / len(spins)
        else:
            E_ab = 0.0
        chsh_evidence[f"E({a},{b})"] = round(E_ab, 4)
        chsh_S += CHSH_ROUNDS[(a, b)] * E_ab

    bell_violation = abs(chsh_S) > 2.0     # > 2 ⇒ Bell-inequality violated
    quantum_bound = 2 * math.sqrt(2)        # Tsirelson bound

    meta = {
        "kept_indices": kept_indices,
        "sifting_efficiency": len(kept_indices) / max(len(prep.alice_bases), 1),
        "chsh_S": round(chsh_S, 4),
        "chsh_terms": chsh_evidence,
        "quantum_bound": round(quantum_bound, 4),
        "bell_violation": bell_violation,
        "key_rounds": len(kept_indices),
    }
    return alice_key, bob_key, meta
