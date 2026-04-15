"""
Simple parity-block error correction for the sifted BB84 key.

Splits the key into blocks, computes parity, and discards blocks with errors.
This is a simplified CASCADE-like first pass.
"""


def parity(block: list[int]) -> int:
    """Return the XOR parity of a bit block."""
    result = 0
    for bit in block:
        result ^= bit
    return result


def correct_errors(
    alice_key: list[int],
    bob_key: list[int],
    block_size: int = 4,
) -> tuple[list[int], list[int]]:
    """
    Discard blocks where Alice's and Bob's parity disagrees.

    Args:
        alice_key:  Alice's sifted key.
        bob_key:    Bob's sifted key.
        block_size: Number of bits per parity block.

    Returns:
        (corrected_alice, corrected_bob): Keys with erroneous blocks removed.
    """
    corrected_alice, corrected_bob = [], []

    for i in range(0, len(alice_key) - block_size + 1, block_size):
        a_block = alice_key[i:i + block_size]
        b_block = bob_key[i:i + block_size]
        if parity(a_block) == parity(b_block):
            corrected_alice.extend(a_block)
            corrected_bob.extend(b_block)

    return corrected_alice, corrected_bob
