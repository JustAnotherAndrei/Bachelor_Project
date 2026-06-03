"""
Mission grading — converts a (Mission, instantiated_params, sim_result,
user_answer) tuple into a structured verdict + score + breakdown.

Two grader strategies:
  - DetectiveGrader : compares user's declared verdict + attack_type against
                      the ground truth derived from instantiated_params
  - EngineerGrader  : evaluates each constraint in mission.objective against
                      the metrics in sim_result, all-or-nothing pass

Both return the same dict shape so the frontend can render uniformly.
"""

from __future__ import annotations

from typing import Any

from challenge.mission_catalog import Mission


# ---------------------------------------------------------------------------
# Truth derivation — used by Detective grading and by feedback messages
# ---------------------------------------------------------------------------

_EVE_TO_ATTACK = {
    "none": None,
    "weak": "intercept_resend",
    "strong": "intercept_resend",
    "smart": "smart",
    "pns": "pns",
}


def derive_truth(instantiated: dict) -> dict:
    """Compute the ground-truth verdict + attack type from rolled params."""
    eve_mode = instantiated.get("eve_mode", "none")
    attack = _EVE_TO_ATTACK.get(eve_mode)
    return {
        "verdict": "secure" if attack is None else "compromised",
        "attack_type": attack,
        "eve_mode": eve_mode,
    }


# ---------------------------------------------------------------------------
# Detective grader
# ---------------------------------------------------------------------------

class DetectiveGrader:
    """Score a verdict + attack-type declaration against ground truth."""

    def grade(self, mission: Mission, instantiated: dict,
              sim_result: dict, user_answer: dict) -> dict:
        truth = derive_truth(instantiated)
        user_verdict = user_answer.get("verdict")
        user_attack = user_answer.get("attack_type")

        verdict_ok = user_verdict == truth["verdict"]
        # Attack type only matters when channel is actually compromised. If
        # the user correctly says "secure", attack_type is moot.
        if truth["verdict"] == "secure":
            attack_ok = True
        else:
            attack_ok = user_attack == truth["attack_type"]

        score = 0
        if verdict_ok:
            score += 50
        if attack_ok and verdict_ok:
            score += 50

        correct = verdict_ok and attack_ok
        return {
            "correct": correct,
            "score": score,
            "xp_earned": mission.xp_reward if correct else 0,
            "breakdown": {
                "verdict": {
                    "user": user_verdict,
                    "truth": truth["verdict"],
                    "ok": verdict_ok,
                },
                "attack_type": {
                    "user": user_attack,
                    "truth": truth["attack_type"],
                    "ok": attack_ok,
                },
            },
            "truth": truth,
            "explanation": self._explain(truth, sim_result),
        }

    def _explain(self, truth: dict, sim_result: dict) -> str:
        qber = sim_result.get("qber")
        qber_pct = f"{qber * 100:.1f}%" if isinstance(qber, (int, float)) else "—"
        if truth["verdict"] == "secure":
            return (
                f"Eve was absent. The observed QBER ({qber_pct}) was generated "
                f"by channel noise and detector imperfections only."
            )
        attack = truth["attack_type"]
        if attack == "intercept_resend":
            return (
                f"Eve ran an intercept-resend attack — she measured every "
                f"intercepted photon in a random basis, doubling the noise on "
                f"the basis-matched positions. Observed QBER: {qber_pct}."
            )
        if attack == "smart":
            return (
                f"Eve throttled her intercept rate to keep QBER just below the "
                f"security threshold ({qber_pct}). Without the LSTM panel, you "
                f"would have called this run secure."
            )
        if attack == "pns":
            return (
                "Eve ran a Photon-Number-Splitting attack: she blocked single-"
                "photon pulses and split multi-photon pulses, learning their "
                "bits with zero QBER cost. The decoy-state Y1 bound is the "
                "only thing that exposes her."
            )
        return f"Truth verdict: {truth['verdict']}."


# ---------------------------------------------------------------------------
# Engineer grader
# ---------------------------------------------------------------------------

class EngineerGrader:
    """Evaluate sim_result against the mission's constraint list."""

    def grade(self, mission: Mission, instantiated: dict,
              sim_result: dict, user_answer: dict) -> dict:
        constraints = mission.objective.get("constraints", [])
        evaluated = []
        n_passed = 0
        for c in constraints:
            metric = c["metric"]
            actual = _extract(sim_result, metric)
            ok = _compare(actual, c["op"], c["value"])
            if ok:
                n_passed += 1
            evaluated.append({
                "metric": metric,
                "op": c["op"],
                "value": c["value"],
                "actual": actual,
                "ok": ok,
            })

        n_total = max(len(constraints), 1)
        correct = n_passed == n_total
        score = int(round(100 * n_passed / n_total))
        return {
            "correct": correct,
            "score": score,
            "xp_earned": mission.xp_reward if correct else 0,
            "breakdown": {
                "constraints": evaluated,
                "n_passed": n_passed,
                "n_total": n_total,
            },
            "explanation": self._explain(evaluated, correct),
        }

    def _explain(self, evaluated: list[dict], correct: bool) -> str:
        if correct:
            return "All constraints satisfied — well configured."
        failed = [e for e in evaluated if not e["ok"]]
        if not failed:
            return ""
        first = failed[0]
        return (
            f"Constraint '{first['metric']} {first['op']} {first['value']}' "
            f"failed — actual value was {first['actual']}."
        )


# ---------------------------------------------------------------------------
# Generic metric extraction + comparison
# ---------------------------------------------------------------------------

_MISSING = object()


def _extract(obj: Any, dotted_key: str) -> Any:
    """Navigate a nested dict using dot notation: 'finite_key.finite_length'."""
    cur: Any = obj
    for part in dotted_key.split("."):
        if isinstance(cur, dict) and part in cur:
            cur = cur[part]
        else:
            return _MISSING
    return cur


def _compare(actual: Any, op: str, expected: Any) -> bool:
    if actual is _MISSING or actual is None:
        return False
    try:
        if op == "==":
            return actual == expected
        if op == "!=":
            return actual != expected
        if op == "<":
            return actual < expected
        if op == "<=":
            return actual <= expected
        if op == ">":
            return actual > expected
        if op == ">=":
            return actual >= expected
    except TypeError:
        return False
    return False


# ---------------------------------------------------------------------------
# Dispatcher
# ---------------------------------------------------------------------------

_DETECTIVE = DetectiveGrader()
_ENGINEER = EngineerGrader()


def grade(mission: Mission, instantiated: dict, sim_result: dict,
          user_answer: dict) -> dict:
    """Route to the appropriate grader for the mission type."""
    if mission.type == "detective":
        return _DETECTIVE.grade(mission, instantiated, sim_result, user_answer)
    if mission.type == "engineer":
        return _ENGINEER.grade(mission, instantiated, sim_result, user_answer)
    raise ValueError(f"Unknown mission type: {mission.type}")
