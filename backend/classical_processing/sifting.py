"""
BB84 sifting step: retain only the bits where Alice and Bob used the same basis.
"""


def sift_keys(
    alice_bits: list[int],
    alice_bases: list[int],
    bob_bits: list[int],
    bob_bases: list[int],
) -> tuple[list[int], list[int]]:
    """
    Perform basis reconciliation (sifting).

    Args:
        alice_bits:  Alice's raw bit string.
        alice_bases: Alice's basis choices (0=Z, 1=X).
        bob_bits:    Bob's raw measurement results.
        bob_bases:   Bob's basis choices (0=Z, 1=X).

    Returns:
        (alice_key, bob_key): Sifted key fragments for Alice and Bob.
    """
    alice_key, bob_key = [], []
    for a_bit, a_basis, b_bit, b_basis in zip(alice_bits, alice_bases, bob_bits, bob_bases):
        if a_basis == b_basis:
            alice_key.append(a_bit)
            bob_key.append(b_bit)
    return alice_key, bob_key
