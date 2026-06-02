"""
Finite-key security analysis for BB84-family QKD protocols.

The textbook BB84 security proof (Shor-Preskill, GLLP) assumes the number of
exchanged qubits goes to infinity. In practice protocols use a finite block
of N qubits, and the QBER, basis-mismatch statistics, and Eve's information
estimate all carry statistical uncertainty. Composable finite-key bounds
quantify this uncertainty via concentration inequalities (Hoeffding,
Chernoff) and a set of security parameters.

This module implements the finite-key length formula of Tomamichel et al.
(Nature Communications 3, 634, 2012) in a simplified form:

    ℓ ≤ n · [1 − h(Q + δ_PE)] − leak_EC − log₂(2/ε_corr)
        − 2·log₂(1/(2·ε_PA))

where:
    n         : length of the sifted (raw) key
    Q         : measured QBER on the sifted bits
    δ_PE      : Hoeffding statistical correction on the QBER estimate,
                δ_PE = √( ln(2/ε_PE) / (2·n) )
    h(·)      : binary Shannon entropy
    leak_EC   : bits leaked during error correction = f · n · h(Q)
                with f ≈ 1.16 the CASCADE efficiency factor near Q=0.05
    ε_corr    : correctness security parameter (probability Alice's and
                Bob's keys differ after EC). Default 1e-10.
    ε_PA      : privacy-amplification security parameter. Default 1e-10.
    ε_PE      : parameter-estimation security parameter. Default 1e-10.

The total security parameter ε_sec = ε_corr + ε_PA + ε_PE bounds the
probability the produced key fails composable security.

References:
  M. Tomamichel et al., "Tight finite-key analysis for quantum cryptography",
    Nature Communications 3, 634 (2012).
  C. Lim, M. Curty, N. Walenta, F. Xu, H. Zbinden,
    "Concise security bounds for practical decoy-state QKD", PRA 89, 022307 (2014).
"""

import math


def _h(p: float) -> float:
    """Binary Shannon entropy h(p) = -p·log₂(p) − (1−p)·log₂(1−p)."""
    if p <= 0.0 or p >= 1.0:
        return 0.0
    return -p * math.log2(p) - (1.0 - p) * math.log2(1.0 - p)


def finite_key_analysis(
    n_sifted: int,
    qber: float,
    f_ec: float = 1.16,
    eps_corr: float = 1e-10,
    eps_pa: float = 1e-10,
    eps_pe: float = 1e-10,
) -> dict:
    """
    Compute asymptotic and finite-key secure key lengths for a single run.

    Returns a JSON-friendly dict containing both lengths and the individual
    correction terms, so the front-end can visualise the cost of the
    finite-key regime.
    """
    if n_sifted <= 0:
        return {
            "valid": False,
            "reason": "Empty sifted key — no bound applicable.",
        }

    qber = max(min(qber, 0.5), 0.0)

    # Hoeffding statistical correction on the QBER estimate.
    # δ_PE shrinks like 1/√n: more sifted bits → tighter bound.
    delta_pe = math.sqrt(math.log(2.0 / eps_pe) / (2.0 * n_sifted))
    qber_upper = min(qber + delta_pe, 0.5)

    h_q = _h(qber)
    h_q_upper = _h(qber_upper)

    # Error-correction leakage (Slepian-Wolf bound, with realistic
    # efficiency factor f ≈ 1.16 for CASCADE near 5 % QBER).
    leak_ec = f_ec * n_sifted * h_q

    # Privacy-amplification overhead (correctness + secrecy security).
    pa_overhead = (
        math.log2(2.0 / eps_corr)
        + 2.0 * math.log2(1.0 / (2.0 * eps_pa))
    )

    # --- Asymptotic key length (textbook GLLP / Shor-Preskill) ---
    # ℓ_asymp = n · [1 − h(Q)] − leak_EC
    asymptotic_length = n_sifted * (1.0 - h_q) - leak_ec

    # --- Finite-key length (statistical correction on the phase error) ---
    # ℓ_finite = n · [1 − h(Q + δ_PE)] − leak_EC − PA overhead
    finite_length = (
        n_sifted * (1.0 - h_q_upper)
        - leak_ec
        - pa_overhead
    )

    # The cost of finiteness: how many secure bits we forgo because N is
    # finite. Always non-negative (δ_PE ≥ 0 and PA overhead > 0).
    cost = max(asymptotic_length - finite_length, 0.0)

    asymptotic_length = max(asymptotic_length, 0.0)
    finite_length_floor = max(finite_length, 0.0)

    return {
        "valid": True,
        "n_sifted": n_sifted,
        "qber": round(qber, 6),
        "qber_upper": round(qber_upper, 6),
        "delta_pe": round(delta_pe, 6),
        "h_q": round(h_q, 6),
        "h_q_upper": round(h_q_upper, 6),
        "leak_ec": round(leak_ec, 2),
        "pa_overhead": round(pa_overhead, 2),
        "asymptotic_length": round(asymptotic_length, 1),
        "finite_length": round(finite_length_floor, 1),
        "finite_length_raw": round(finite_length, 1),  # may be negative
        "cost": round(cost, 1),
        "secure": finite_length > 0,
        "eps_corr": eps_corr,
        "eps_pa": eps_pa,
        "eps_pe": eps_pe,
        "eps_sec_total": eps_corr + eps_pa + eps_pe,
        "f_ec": f_ec,
    }
