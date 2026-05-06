"""
QBER (Quantum Bit Error Rate) calculation for the BB84 protocol.

Security threshold: QBER >= 11% signals a compromised channel (Eve present).
"""

QBER_SECURITY_THRESHOLD = 0.11 # 11% QBER threshold for security in BB84 algorithm. anything above this is marked as 'compromised'


def calculate_qber(alice_key: list[int], bob_key: list[int]) -> float:
    """
    Calculate the Quantum Bit Error Rate between Alice's and Bob's sifted keys.

    Args:
        alice_key: Alice's sifted key.
        bob_key:   Bob's sifted key.

    Returns:
        QBER as a float in [0, 1].

    Raises:
        ValueError: If the sifted keys are empty.
    """
    if not alice_key:
        raise ValueError("Sifted key is empty — cannot compute QBER.")

    errors = sum(a != b for a, b in zip(alice_key, bob_key))
    return errors / len(alice_key)


def is_channel_secure(qber: float) -> bool:
    """
    Determine if the channel is secure based on QBER.

    Returns False (Compromised) if QBER >= 11%.
    """
    return qber < QBER_SECURITY_THRESHOLD
