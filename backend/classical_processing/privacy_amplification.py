"""
Privacy amplification via SHA-256 hashing.

Compresses the reconciled key to reduce Eve's potential knowledge to negligible.
"""

import hashlib


def amplify_privacy(key: list[int], output_bits: int = 128) -> str:
    """
    Apply privacy amplification using SHA-256.

    Converts the corrected bit string to bytes, hashes it, then truncates
    the digest to the desired number of bits.

    Args:
        key:         Corrected bit list (0s and 1s).
        output_bits: Desired final key length in bits (must be <= 256).

    Returns:
        Final secret key as a hex string of length output_bits // 4.
    """
    if output_bits > 256:
        raise ValueError("SHA-256 produces at most 256 bits.")

    # Pack bits into bytes (pad with zeros on the right if needed)
    byte_length = (len(key) + 7) // 8
    key_int = int("".join(str(b) for b in key), 2) if key else 0
    key_bytes = key_int.to_bytes(byte_length, byteorder="big")

    digest = hashlib.sha256(key_bytes).hexdigest()
    # Truncate to desired output length (hex chars = bits / 4)
    return digest[: output_bits // 4]
