"""
Decoy-state BB84 with weak coherent pulse (WCP) source modelling.

Real-world BB84 implementations do not have single-photon sources. Instead,
they use attenuated laser pulses whose photon number follows a Poisson
distribution. This exposes the protocol to the Photon Number Splitting (PNS)
attack: an eavesdropper can split off one photon from a multi-photon pulse
and forward the rest without disturbing the quantum state.

The decoy-state method (Lo, Ma, Chen, PRL 94, 230504, 2005) defends against
PNS by varying the source intensity randomly between three levels (signal μ,
decoy ν, vacuum 0). Comparing detection statistics across the three intensities
yields tight bounds on the single-photon yield Y₁ and single-photon error rate
e₁, allowing a secure key rate to be computed using the GLLP formula.

References:
  H.-K. Lo, X. Ma, K. Chen, "Decoy State Quantum Key Distribution",
  Physical Review Letters 94, 230504, 2005.
  D. Gottesman, H.-K. Lo, N. Lütkenhaus, J. Preskill, "Security of QKD with
  Imperfect Devices", Quantum Inf. Comput. 4, 325 (2004).
"""

import math
from dataclasses import dataclass


@dataclass
class PulseResult:
    """Outcome of a single WCP pulse traversing the channel."""
    intensity: float        # 0 (vacuum), ν (decoy), or μ (signal)
    n_emitted: int          # number of photons sampled from Poisson(intensity)
    n_survived: int         # photons that reached Bob (after channel loss)
    detected: bool          # True if Bob registered ≥1 photon
    pns_vulnerable: bool    # True if pulse had ≥2 photons (PNS-exploitable)


def poisson_sample(mean: float, rng) -> int:
    """Sample a non-negative integer from Poisson(mean), capped at 6 for sim speed."""
    if mean <= 0:
        return 0
    return min(int(rng.poisson(mean)), 6)


def simulate_wcp_pulses(
    n_pulses: int,
    mu_signal: float,
    mu_decoy: float,
    p_signal: float,
    p_decoy: float,
    eta: float,
    rng,
) -> list[PulseResult]:
    """
    Simulate `n_pulses` weak coherent pulses with random intensity selection.

    Intensities are sampled per pulse: signal (μ) with probability p_signal,
    decoy (ν) with p_decoy, vacuum (0) with the remainder.

    Args:
        n_pulses:   Total number of pulses Alice emits.
        mu_signal:  Mean photon number of signal pulses (typ. 0.5).
        mu_decoy:   Mean photon number of decoy pulses (typ. 0.1).
        p_signal:   Probability of choosing the signal intensity per pulse.
        p_decoy:    Probability of choosing the decoy intensity per pulse.
        eta:        Channel transmittance per photon (from channel_model).
        rng:        numpy Generator.

    Returns:
        List of PulseResult.
    """
    p_vacuum = max(0.0, 1.0 - p_signal - p_decoy)
    intensity_choices = rng.choice(
        [mu_signal, mu_decoy, 0.0],
        size=n_pulses,
        p=[p_signal, p_decoy, p_vacuum],
    )

    pulses: list[PulseResult] = []
    for intensity in intensity_choices:
        n_emitted = poisson_sample(float(intensity), rng)
        # Each emitted photon survives the channel independently with prob η
        if n_emitted == 0 or eta <= 0:
            n_survived = 0
        elif eta >= 1.0:
            n_survived = n_emitted
        else:
            n_survived = int(rng.binomial(n_emitted, eta))
        pulses.append(PulseResult(
            intensity=float(intensity),
            n_emitted=n_emitted,
            n_survived=n_survived,
            detected=(n_survived >= 1),
            pns_vulnerable=(n_emitted >= 2),
        ))
    return pulses


def aggregate_by_intensity(
    pulses: list[PulseResult],
    error_flags: list[bool],
) -> list[dict]:
    """
    Compute per-intensity gain Q_x = detections / pulses_at_x and
    error rate E_x = errors / detections at each intensity class.

    Returns a JSON-friendly list (one entry per intensity), sorted by intensity
    descending so the signal level appears first.
    """
    buckets: dict[float, dict] = {}
    for pulse, err in zip(pulses, error_flags):
        b = buckets.setdefault(pulse.intensity, {"total": 0, "detected": 0, "errors": 0})
        b["total"] += 1
        if pulse.detected:
            b["detected"] += 1
            if err:
                b["errors"] += 1

    rows = []
    for intensity, b in sorted(buckets.items(), key=lambda kv: -kv[0]):
        q = b["detected"] / b["total"] if b["total"] > 0 else 0.0
        e = b["errors"] / b["detected"] if b["detected"] > 0 else 0.0
        rows.append({
            "intensity": round(intensity, 4),
            "pulses": b["total"],
            "detections": b["detected"],
            "errors": b["errors"],
            "gain": round(q, 6),
            "qber": round(e, 4),
        })
    return rows


def find_intensity(rows: list[dict], intensity: float, tol: float = 1e-3) -> dict | None:
    """Find the aggregation row for a specific intensity (with float tolerance)."""
    for r in rows:
        if abs(r["intensity"] - intensity) < tol:
            return r
    return None


def decoy_analysis(
    Q_mu: float,
    Q_nu: float,
    Q_0: float,
    E_mu: float,
    E_nu: float,
    mu: float,
    nu: float,
    e0: float = 0.5,
) -> dict:
    """
    Lo-Ma-Chen 2005 decoy-state bounds on single-photon yield and error rate.

    Lower bound on single-photon yield Y₁:
        Y₁ ≥ (μ / (μν − ν²)) · (Q_ν·e^ν − Q_μ·e^μ·(ν/μ)² − Y₀·(μ² − ν²)/μ²)
    where Y₀ = Q_0 is the vacuum (dark-count) yield.

    Upper bound on single-photon error rate e₁:
        e₁ ≤ (E_ν·Q_ν·e^ν − e₀·Y₀) / (Y₁·ν)
    where e₀ = 0.5 is the error rate of a vacuum (random bit).

    Returns:
        Dict with Y_1, e_1, Q_1 (single-photon gain), and individual terms.
    """
    if mu <= nu or nu <= 0:
        return {"valid": False, "reason": "Require μ > ν > 0"}

    Y_0 = Q_0  # vacuum yield = dark count rate (≈ 0 in noise-free model)

    # Y₁ lower bound
    term1 = Q_nu * math.exp(nu)
    term2 = Q_mu * math.exp(mu) * (nu / mu) ** 2
    term3 = Y_0 * (mu ** 2 - nu ** 2) / (mu ** 2)
    Y_1_lower = (mu / (mu * nu - nu ** 2)) * (term1 - term2 - term3)
    Y_1_lower = max(Y_1_lower, 0.0)

    # Q₁ = μ·e^(-μ)·Y₁ (single-photon gain at signal intensity)
    Q_1 = mu * math.exp(-mu) * Y_1_lower

    # e₁ upper bound (only valid if Y₁ > 0)
    if Y_1_lower > 0:
        e_1_upper = (E_nu * Q_nu * math.exp(nu) - e0 * Y_0) / (Y_1_lower * nu)
        e_1_upper = min(max(e_1_upper, 0.0), 0.5)
    else:
        e_1_upper = 0.5

    return {
        "valid": True,
        "Y_1": round(Y_1_lower, 6),
        "e_1": round(e_1_upper, 4),
        "Q_1": round(Q_1, 6),
        "Y_0": round(Y_0, 6),
    }


def _h(p: float) -> float:
    """Binary entropy."""
    if p <= 0 or p >= 1:
        return 0.0
    return -p * math.log2(p) - (1 - p) * math.log2(1 - p)


def secure_key_rate(
    Q_mu: float,
    E_mu: float,
    Q_1: float,
    e_1: float,
    f_ec: float = 1.16,
) -> float:
    """
    GLLP asymptotic secure key rate per signal pulse (after sifting factor).

        R = (1/2) · {-Q_μ · f · h(E_μ) + Q_1 · [1 - h(e_1)]}

    where f is the error-correction efficiency (~1.16 for CASCADE near 5% QBER).
    The 1/2 absorbs the sifting factor.

    Returns the rate; clipped at 0 if the formula yields a negative value
    (indicating the channel is too lossy / noisy for a positive rate).
    """
    rate = 0.5 * (Q_1 * (1 - _h(e_1)) - Q_mu * f_ec * _h(E_mu))
    return max(rate, 0.0)
