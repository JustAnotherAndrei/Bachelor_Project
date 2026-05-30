"""
CASCADE error correction algorithm (Brassard & Salvail, 1994).

Iterative information reconciliation protocol that locates and corrects
individual erroneous bits via binary search on parity, rather than
discarding whole blocks. Achieves near-Shannon reconciliation efficiency.

Reference:
  G. Brassard and L. Salvail, "Secret-Key Reconciliation by Public Discussion",
  EUROCRYPT 1993, LNCS 765, pp. 410-423, Springer, 1994.
"""

import math
import random


def _parity(bits: list[int], indices) -> int:
    """XOR parity of the bits at the given indices."""
    p = 0
    for i in indices:
        p ^= bits[i]
    return p


def _initial_block_size(qber: float) -> int:
    """
    Optimal first-pass block size: k1 = ceil(0.73 / QBER).

    For very low QBER, cap at the key length (handled by caller).
    """
    if qber <= 0:
        return 0  # no errors -> no need to correct
    return max(2, math.ceil(0.73 / qber))


def _binary_locate(
    alice: list[int],
    bob: list[int],
    indices: list[int],
    parity_announcements: int,
) -> tuple[int, int]:
    """
    BINARY sub-protocol: locate one erroneous bit in `indices` via binary search
    on parity (Alice announces parity of each half).

    Returns:
        (corrected_bit_position, parity_announcements_used)
    """
    while len(indices) > 1:
        mid = len(indices) // 2
        left = indices[:mid]
        parity_announcements += 1  # Alice reveals parity of left half
        if _parity(alice, left) != _parity(bob, left):
            indices = left
        else:
            indices = indices[mid:]

    # Single bit located — flip Bob's bit to match Alice's
    pos = indices[0]
    bob[pos] ^= 1
    return pos, parity_announcements


def cascade_correct(
    alice_key: list[int],
    bob_key: list[int],
    qber: float,
    n_passes: int = 4,
    seed: int | None = None,
) -> tuple[list[int], list[int], dict]:
    """
    Reconcile Bob's key with Alice's via the CASCADE protocol.

    Args:
        alice_key: Alice's sifted key (reference).
        bob_key:   Bob's sifted key (will be corrected — modified copy returned).
        qber:      Estimated QBER from a sacrificed subset (sets block size).
        n_passes:  Number of CASCADE passes (typically 4).
        seed:      Optional RNG seed for reproducible permutations.

    Returns:
        (corrected_alice, corrected_bob, stats)
        where stats = {
            "initial_errors": int,
            "remaining_errors": int,
            "parity_announcements": int,
            "bits_revealed": int,
            "efficiency": float,
        }
    """
    if not alice_key or not bob_key:
        return list(alice_key), list(bob_key), {
            "initial_errors": 0,
            "remaining_errors": 0,
            "parity_announcements": 0,
            "bits_revealed": 0,
            "efficiency": 0.0,
        }

    n = len(alice_key)
    alice = list(alice_key)
    bob = list(bob_key)
    rng = random.Random(seed)

    initial_errors = sum(1 for a, b in zip(alice, bob) if a != b)

    if qber <= 0 or initial_errors == 0:
        return alice, bob, {
            "initial_errors": 0,
            "remaining_errors": 0,
            "parity_announcements": 0,
            "bits_revealed": 0,
            "efficiency": 0.0,
        }

    # Track block memberships across passes for the cascade effect.
    # pass_blocks[p] = list of blocks, where each block is a list of bit indices.
    # bit_to_blocks[p][i] = the block in pass p that contains bit i.
    pass_blocks: list[list[list[int]]] = []
    bit_to_blocks: list[list[list[int]]] = []

    k = _initial_block_size(qber)
    parity_counter = [0]  # list so nested calls can mutate it

    for pass_idx in range(n_passes):
        block_size = min(max(k, 2), n)
        if pass_idx == 0:
            permutation = list(range(n))
        else:
            permutation = list(range(n))
            rng.shuffle(permutation)

        blocks: list[list[int]] = [
            permutation[i:i + block_size] for i in range(0, n, block_size)
        ]
        bit_block: list[list[int]] = [None] * n  # type: ignore
        for block in blocks:
            for bit in block:
                bit_block[bit] = block

        pass_blocks.append(blocks)
        bit_to_blocks.append(bit_block)

        for block in blocks:
            parity_counter[0] += 1  # Alice announces this block's parity
            if _parity(alice, block) != _parity(bob, block):
                pos, parity_counter[0] = _binary_locate(
                    alice, bob, list(block), parity_counter[0]
                )
                # Cascade backward through earlier-pass blocks containing `pos`.
                _cascade_back(alice, bob, bit_to_blocks[:pass_idx + 1], pos, parity_counter)

        k *= 2

    parity_announcements = parity_counter[0]

    remaining_errors = sum(1 for a, b in zip(alice, bob) if a != b)
    # Reconciliation efficiency relative to Shannon limit n * h(QBER):
    # f = parity_bits_revealed / (n * h(QBER))   (lower is better)
    h_q = _binary_entropy(qber)
    shannon_limit = max(n * h_q, 1.0)
    efficiency = parity_announcements / shannon_limit

    return alice, bob, {
        "initial_errors": initial_errors,
        "remaining_errors": remaining_errors,
        "parity_announcements": parity_announcements,
        "bits_revealed": parity_announcements,
        "efficiency": round(efficiency, 3),
    }


def _cascade_back(
    alice: list[int],
    bob: list[int],
    bit_to_blocks_so_far: list[list[list[int]]],
    flipped_bit: int,
    parity_counter: list[int],
) -> None:
    """
    Recursive cascade step: after `flipped_bit` was corrected in the current pass,
    re-check all earlier-pass blocks containing it. Any block whose parity now
    disagrees gets a new BINARY sweep, which may flip another bit and recurse.
    """
    # Examine each earlier pass (and the current pass except the block we came from)
    for pass_blocks in bit_to_blocks_so_far[:-1]:
        block = pass_blocks[flipped_bit]
        if block is None:
            continue
        parity_counter[0] += 1
        if _parity(alice, block) != _parity(bob, block):
            new_pos, parity_counter[0] = _binary_locate(
                alice, bob, list(block), parity_counter[0]
            )
            _cascade_back(alice, bob, bit_to_blocks_so_far, new_pos, parity_counter)


def _binary_entropy(p: float) -> float:
    """Binary entropy h(p) = -p log2 p - (1-p) log2(1-p)."""
    if p <= 0 or p >= 1:
        return 0.0
    return -p * math.log2(p) - (1 - p) * math.log2(1 - p)
