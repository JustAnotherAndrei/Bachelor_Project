"""
Fiber-optic channel model for BB84 photon loss simulation.

Models photon transmission probability using the Beer-Lambert attenuation
model for single-mode fiber (SMF-28, α = 0.2 dB/km).
"""

import math

FIBER_ATTENUATION_DB_PER_KM = 0.2  # standard SMF-28


def channel_transmittance(distance_km: float) -> float:
    """Return η(L) = 10^(-α·L / 10) for a given fiber length."""
    if distance_km <= 0:
        return 1.0
    return 10 ** (-FIBER_ATTENUATION_DB_PER_KM * distance_km / 10)


def apply_channel_loss(
    alice_bits: list[int],
    alice_bases: list[int],
    bob_bases: list[int],
    eve_intercepts,   # list[bool] | None
    eve_bases,        # list[int]  | None
    distance_km: float,
    rng,
) -> tuple:
    """
    Simulate photon loss over the fiber channel.

    Each qubit survives transmission with probability η(distance_km).
    Lost photons are removed from all per-qubit arrays.

    Returns:
        (alice_bits, alice_bases, bob_bases, eve_intercepts, eve_bases, eta)
        where eta is the computed transmittance.
    """
    eta = channel_transmittance(distance_km)
    if eta >= 1.0:
        return alice_bits, alice_bases, bob_bases, eve_intercepts, eve_bases, 1.0

    survived = (rng.random(len(alice_bits)) < eta).tolist()

    def filt(lst):
        if lst is None:
            return None
        return [x for x, s in zip(lst, survived) if s]

    return (
        filt(alice_bits),
        filt(alice_bases),
        filt(bob_bases),
        filt(eve_intercepts),
        filt(eve_bases),
        eta,
    )


def _h(x: float) -> float:
    """Binary entropy function."""
    if x <= 0 or x >= 1:
        return 0.0
    return -x * math.log2(x) - (1 - x) * math.log2(1 - x)


def key_rate_vs_distance(
    distance_points: list[float],
    qber_noise: float = 0.03,
) -> list[dict]:
    """
    Theoretical secure key fraction as a function of fiber distance.

    Simplified BB84 model:
        R(L) = η(L) × max(0, 1 - 2·h(Q_noise))

    where h is the binary entropy function and the 0.5 sifting factor
    is absorbed into the normalisation (rate is expressed as fraction
    of the raw qubit source rate).

    Args:
        distance_points: Distances in km at which to evaluate R(L).
        qber_noise:      Baseline QBER from channel noise alone (no Eve).

    Returns:
        List of dicts with keys: distance_km, key_rate, transmittance.
    """
    rate_factor = max(0.0, 1.0 - 2.0 * _h(qber_noise))
    return [
        {
            "distance_km": d,
            "key_rate": round(channel_transmittance(d) * rate_factor, 6),
            "transmittance": round(channel_transmittance(d), 6),
        }
        for d in distance_points
    ]
