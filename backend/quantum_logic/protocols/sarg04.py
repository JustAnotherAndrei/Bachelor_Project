"""
SARG04 protocol (Scarani, Acín, Ribordy, Gisin 2004).

SARG04 uses the same four quantum states as BB84 (|0>, |1>, |+>, |->) but
differs in the classical reconciliation step. After Bob measures, Alice does
NOT announce her basis. Instead, for each transmitted qubit she announces a
*pair* of non-orthogonal states (one from each basis) — one of which she
actually sent. Bob keeps the bit only if his measurement result is
incompatible with one element of the pair, allowing him to deduce the other.

This trades sifting efficiency (now ~25% asymptotically, vs 50% in BB84) for
greatly improved resistance to the photon-number-splitting (PNS) attack on
weak-coherent-pulse sources. Intuitively, even when Eve obtains multiple
photons via PNS, she cannot deterministically distinguish the announced pair
without making her own basis assumption, so PNS no longer gives her a
"free" bit.

Sifting rule (announcement of the {|0>, |+>} pair, encoding bit b=0):
    Alice sent |0>  (b=0)  --> Bob in Z gets 0 (matches |0>), in X gets ±
    Alice sent |+>  (b=0)  --> Bob in Z gets ±, in X gets 0
    Bob keeps the result iff he can rule out one of the two announced states.

We use the symmetric four-pair announcement and apply the standard SARG04
sifting filter: Bob retains his outcome iff, given the announced pair and his
measurement basis, exactly one of the two states is *inconsistent* with what
he observed, so the other (and hence the bit) is uniquely determined.

References:
    V. Scarani, A. Acín, G. Ribordy, N. Gisin,
    "Quantum cryptography protocols robust against photon number splitting
    attacks for weak laser pulses", Phys. Rev. Lett. 92, 057901, 2004.
"""

from dataclasses import dataclass
from typing import Any
import numpy as np
from qiskit import QuantumCircuit

NAME = "sarg04"
DISPLAY_NAME = "SARG04"
USES_ENTANGLEMENT = False
SIFTING_EFFICIENCY = 0.25
QBER_UNDER_STRONG_EVE = 0.25


# Mapping (bit, basis) -> state label, where bases 0=Z, 1=X
#   (0, 0) -> |0>     (0, 1) -> |+>
#   (1, 0) -> |1>     (1, 1) -> |->
_STATE_OF = {
    (0, 0): "0",
    (1, 0): "1",
    (0, 1): "+",
    (1, 1): "-",
}

# Pairs Alice may announce: one Z-state and one X-state, encoding the SAME bit.
# Alice picks her state from this pair uniformly. The recipient sees the pair
# label (e.g. "0+", "1-") and must rule out one element using Bob's outcome.
_ANNOUNCE_PAIRS = ["0+", "0-", "1+", "1-"]


def _state_to_pair(state: str, rng: np.random.Generator) -> str:
    """For a given prepared state, return one of the two pairs containing it."""
    candidates = [p for p in _ANNOUNCE_PAIRS if state in p]
    return rng.choice(candidates) if candidates else _ANNOUNCE_PAIRS[0]


@dataclass
class Preparation:
    alice_bits: list[int]
    alice_bases: list[int]
    bob_bases: list[int]
    announced_pairs: list[str]


def prepare(rng: np.random.Generator, n_qubits: int) -> Preparation:
    alice_bits = rng.integers(0, 2, n_qubits).tolist()
    alice_bases = rng.integers(0, 2, n_qubits).tolist()
    bob_bases = rng.integers(0, 2, n_qubits).tolist()
    announced = [
        _state_to_pair(_STATE_OF[(b, a)], rng) for b, a in zip(alice_bits, alice_bases)
    ]
    return Preparation(
        alice_bits=alice_bits,
        alice_bases=alice_bases,
        bob_bases=bob_bases,
        announced_pairs=announced,
    )


def build_circuits(prep: Preparation) -> list[QuantumCircuit]:
    """
    Circuits are identical to BB84 — only the post-processing differs.
    """
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


def _can_rule_out(state: str, bob_basis: int, bob_result: int) -> bool:
    """
    Return True if Bob's outcome is *inconsistent* with the given prepared state.

    A Z-basis measurement of |0> always gives 0 (so result 1 rules |0> out).
    A Z-basis measurement of |1> always gives 1 (so result 0 rules |1> out).
    An X-basis measurement of |+> always gives 0 (so result 1 rules |+> out).
    An X-basis measurement of |-> always gives 1 (so result 0 rules |-> out).
    All other (state, basis) combinations yield random outcomes and cannot
    rule the state out.
    """
    if bob_basis == 0:                    # Z-basis
        if state == "0" and bob_result == 1: return True
        if state == "1" and bob_result == 0: return True
    else:                                 # X-basis
        if state == "+" and bob_result == 1: return True
        if state == "-" and bob_result == 0: return True
    return False


def _bit_of(state: str) -> int:
    return 0 if state in ("0", "+") else 1


def sift(prep: Preparation, bob_results: list[int]) -> tuple[list[int], list[int], dict[str, Any]]:
    alice_key, bob_key = [], []
    kept_indices = []
    for i, (a_bit, pair, b_basis, b_res) in enumerate(
        zip(prep.alice_bits, prep.announced_pairs, prep.bob_bases, bob_results)
    ):
        s1, s2 = pair[0], pair[1]
        ruled_out_s1 = _can_rule_out(s1, b_basis, b_res)
        ruled_out_s2 = _can_rule_out(s2, b_basis, b_res)
        # Conclusive iff exactly one of the two announced states is ruled out
        if ruled_out_s1 ^ ruled_out_s2:
            kept_state = s2 if ruled_out_s1 else s1
            alice_key.append(a_bit)
            bob_key.append(_bit_of(kept_state))
            kept_indices.append(i)

    meta = {
        "kept_indices": kept_indices,
        "sifting_efficiency": len(kept_indices) / max(len(prep.alice_bits), 1),
    }
    return alice_key, bob_key, meta
