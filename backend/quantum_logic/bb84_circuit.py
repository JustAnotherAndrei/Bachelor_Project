"""
BB84 circuit generation using Qiskit.

Generates the quantum circuits for Alice's encoding and Bob's measurement
according to the BB84 QKD protocol.
"""

from qiskit import QuantumCircuit
import numpy as np


def encode_qubit(bit: int, basis: int) -> QuantumCircuit:
    """
    Encode a single classical bit into a qubit using the given basis.

    Args:
        bit:   Classical bit value (0 or 1).
        basis: Measurement basis — 0 for rectilinear (Z), 1 for diagonal (X).

    Returns:
        A single-qubit QuantumCircuit representing |0>, |1>, |+>, or |->.
    """
    qc = QuantumCircuit(1, 1)
    if bit == 1:
        qc.x(0)          # Flip to |1>
    if basis == 1:
        qc.h(0)          # Rotate to diagonal basis: |+> or |->
    return qc


def measure_qubit(basis: int) -> QuantumCircuit:
    """
    Return the measurement circuit for Bob in the given basis.

    Args:
        basis: 0 for Z-basis, 1 for X-basis.

    Returns:
        A single-qubit QuantumCircuit with measurement applied.
    """
    qc = QuantumCircuit(1, 1)
    if basis == 1:
        qc.h(0)          # Rotate back from diagonal basis before measuring
    qc.measure(0, 0)
    return qc


def build_bb84_circuits(
    alice_bits: list[int],
    alice_bases: list[int],
    bob_bases: list[int],
) -> list[QuantumCircuit]:
    """
    Build a list of full BB84 circuits (encode + measure) for simulation.

    Args:
        alice_bits:  List of bits Alice wants to send.
        alice_bases: List of bases Alice uses for encoding.
        bob_bases:   List of bases Bob uses for measurement.

    Returns:
        A list of QuantumCircuits, one per qubit exchange.
    """
    assert len(alice_bits) == len(alice_bases) == len(bob_bases), \
        "All input lists must have the same length."

    circuits = []
    for bit, a_basis, b_basis in zip(alice_bits, alice_bases, bob_bases):
        qc = encode_qubit(bit, a_basis)
        # Append measurement in Bob's basis
        if b_basis == 1:
            qc.h(0)
        qc.measure(0, 0)
        circuits.append(qc)

    return circuits
