"""
Adaptive intercept-resend eavesdropper for BB84 ("Smart Eve").

Unlike the static Weak (30%) and Strong (100%) Eves which use a fixed
interception probability for every qubit, Smart Eve observes the cumulative
QBER as the protocol unfolds and adapts her interception rate to maximise
extracted information while staying below the abort threshold.

Strategy (greedy threshold-tracking):
  - Eve maintains an estimate of the running QBER she induces, based on the
    fraction of intercepted qubits and the 25% per-intercept error rate.
  - At each new qubit, she chooses to intercept with probability p_t computed
    so that the expected running QBER stays below a safety margin
    (target_qber, typically 9% — comfortably below the 11% threshold).
  - When her induced QBER drifts above the safety margin, she lowers p_t
    aggressively. When it drifts below, she raises p_t.

This produces a more realistic adversary that demonstrates why a fixed
abort threshold is insufficient: a patient Eve who only attacks part of
the channel can extract substantial information without detection.

Reference for the broader argument:
  D. Mayers, "Unconditional Security in Quantum Cryptography", J. ACM 48(3),
  pp. 351-406, 2001 — discusses why the security analysis must account for
  adaptive adversaries, not just memoryless attacks.
"""

from dataclasses import dataclass, field

DEFAULT_TARGET_QBER = 0.09  # safety margin below the 11% abort threshold
QBER_PER_INTERCEPT = 0.25   # expected QBER contribution per intercepted qubit


@dataclass
class SmartEveState:
    """Per-qubit decisions and observations made by Smart Eve."""
    intercepts: list[bool] = field(default_factory=list)        # per-qubit intercept decision
    interception_rates: list[float] = field(default_factory=list)  # probability used per qubit
    observed_qber_trace: list[float] = field(default_factory=list)  # running QBER estimate
    total_intercepted: int = 0


def smart_eve_decide(
    n_qubits: int,
    target_qber: float,
    rng,
    initial_rate: float = 0.5,
    learning_rate: float = 0.6,
) -> SmartEveState:
    """
    Run Smart Eve's adaptive policy across `n_qubits`, returning her per-qubit
    intercept decisions and the QBER she expects Bob to observe at each step.

    Args:
        n_qubits:      Total number of qubits Alice transmits.
        target_qber:   Eve's safety margin (e.g. 0.09 → keep observed QBER ≤ 9%).
        rng:           numpy Generator for randomness.
        initial_rate:  Starting interception probability (typically 0.5).
        learning_rate: How aggressively Eve adjusts rate when off target.

    Returns:
        SmartEveState with full per-qubit trace.
    """
    state = SmartEveState()
    rate = initial_rate
    expected_errors = 0.0  # cumulative expected QBER contribution

    for i in range(n_qubits):
        # Decide whether to intercept this qubit
        intercept = rng.random() < rate
        state.intercepts.append(intercept)
        state.interception_rates.append(rate)

        if intercept:
            state.total_intercepted += 1
            expected_errors += QBER_PER_INTERCEPT

        # Estimate running QBER Bob would observe at qubit i+1
        running_qber = expected_errors / (i + 1)
        state.observed_qber_trace.append(running_qber)

        # Adjust rate for next qubit: if we're above target, slow down hard;
        # if below, accelerate. The cap at [0, 1] keeps it well-defined.
        # Δ = learning_rate * (target_qber - running_qber) / target_qber
        # When running_qber == target_qber → Δ = 0 (steady state)
        # When running_qber > target_qber → Δ < 0 (back off)
        if target_qber > 0:
            delta = learning_rate * (target_qber - running_qber) / target_qber
            rate = max(0.0, min(1.0, rate + delta * 0.5))

    return state


def apply_smart_eve(
    bob_results: list[int],
    alice_bases: list[int],
    eve_state: SmartEveState,
    rng,
) -> list[int]:
    """
    Modify Bob's results to reflect Smart Eve's intercept-resend impact.

    For each qubit Eve intercepted: Eve picks a random basis. If it disagrees
    with Alice's basis (50% chance), Bob's measurement becomes random
    regardless of his own basis choice.

    Returns the modified bob_results list.
    """
    new_results = list(bob_results)
    eve_bases = rng.integers(0, 2, len(bob_results)).tolist()

    for i in range(len(bob_results)):
        if eve_state.intercepts[i] and eve_bases[i] != alice_bases[i]:
            # Eve measured in the wrong basis → Bob's bit is random
            new_results[i] = int(rng.integers(0, 2))

    return new_results
