"""
Mission catalog — 15 hardcoded levels for Challenge Mode.

Each Mission declares:
  - `param_ranges`  : numeric or categorical ranges to roll from on each attempt
  - `fixed`         : parameters held constant for that level
  - `user_chooses`  : (Engineer missions) which parameters the user supplies
  - `objective`     : structured success criteria, interpreted by grader.py
  - `xp_reward`     : XP granted on a correct attempt

Difficulty banding:
  Levels  1–3  : Detective easy   (obvious — None vs Strong Eve)
  Levels  4–6  : Detective medium (gray zone — noise vs Weak Eve)
  Levels  7–9  : Detective hard   (Smart/PNS — needs LSTM or decoy bounds)
  Levels 10–12 : Engineer easy    (configure to meet a simple constraint)
  Levels 13–15 : Engineer hard    (tough finite-key / PNS-resistant setups)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal


MissionType = Literal["detective", "engineer"]
Difficulty = Literal["easy", "medium", "hard"]


@dataclass(frozen=True)
class Mission:
    id: str
    level: int
    type: MissionType
    difficulty: Difficulty
    scenario: str          # short title shown on the level card
    briefing: str          # paragraph shown on the briefing screen
    param_ranges: dict[str, Any] = field(default_factory=dict)
    fixed: dict[str, Any] = field(default_factory=dict)
    user_chooses: list[str] = field(default_factory=list)
    objective: dict[str, Any] = field(default_factory=dict)
    xp_reward: int = 100

    def to_public_dict(self) -> dict:
        """Serialise for the frontend — excludes internal grading hints."""
        return {
            "id": self.id,
            "level": self.level,
            "type": self.type,
            "difficulty": self.difficulty,
            "scenario": self.scenario,
            "briefing": self.briefing,
            "user_chooses": list(self.user_chooses),
            "objective": dict(self.objective),
            "xp_reward": self.xp_reward,
        }


# ---------------------------------------------------------------------------
# Levels 1–3 — Detective easy: obvious Eve vs no Eve
# ---------------------------------------------------------------------------

MISSIONS: list[Mission] = [
    Mission(
        id="detective_l01_first_contact",
        level=1, type="detective", difficulty="easy",
        scenario="First contact",
        briefing=(
            "A standard BB84 link with an ideal source. Run the simulation, "
            "look at the QBER and the photon grid, then declare: is Eve "
            "listening? If yes, which attack is she using?"
        ),
        param_ranges={
            "n_qubits": [250, 350],
            "depolarizing_prob": [0.005, 0.015],
            "measurement_error_prob": [0.01, 0.02],
            "eve_mode": ["none", "strong"],
        },
        fixed={"protocol": "bb84", "source_type": "ideal", "ec_method": "cascade"},
        objective={"type": "verdict_plus_attack"},
        xp_reward=80,
    ),
    Mission(
        id="detective_l02_lab_bench",
        level=2, type="detective", difficulty="easy",
        scenario="Lab bench",
        briefing=(
            "Low-noise lab setup. QBER will be small if the channel is honest "
            "and large if Eve resends every photon. Read the panels and decide."
        ),
        param_ranges={
            "n_qubits": [200, 300],
            "depolarizing_prob": [0.002, 0.01],
            "eve_mode": ["none", "strong"],
        },
        fixed={"protocol": "bb84", "source_type": "ideal", "measurement_error_prob": 0.015},
        objective={"type": "verdict_plus_attack"},
        xp_reward=80,
    ),
    Mission(
        id="detective_l03_noisy_room",
        level=3, type="detective", difficulty="easy",
        scenario="Noisy room",
        briefing=(
            "The room is electrically noisy but Eve, if present, is loud. "
            "Distinguish background noise from a full intercept-resend attack."
        ),
        param_ranges={
            "n_qubits": [250, 400],
            "depolarizing_prob": [0.015, 0.03],
            "eve_mode": ["none", "strong"],
        },
        fixed={"protocol": "bb84", "source_type": "ideal", "measurement_error_prob": 0.02},
        objective={"type": "verdict_plus_attack"},
        xp_reward=80,
    ),

    # -----------------------------------------------------------------------
    # Levels 4–6 — Detective medium: weak Eve, gray-zone QBER
    # -----------------------------------------------------------------------
    Mission(
        id="detective_l04_subtle_listener",
        level=4, type="detective", difficulty="medium",
        scenario="Subtle listener",
        briefing=(
            "Eve, if she's there, only intercepts a fraction of photons. The "
            "QBER alone may fall inside the honest noise floor — read the LSTM "
            "panel too before declaring."
        ),
        param_ranges={
            "n_qubits": [400, 600],
            "depolarizing_prob": [0.01, 0.025],
            "eve_mode": ["none", "weak"],
        },
        fixed={"protocol": "bb84", "source_type": "ideal", "measurement_error_prob": 0.02},
        objective={"type": "verdict_plus_attack"},
        xp_reward=120,
    ),
    Mission(
        id="detective_l05_noise_or_eve",
        level=5, type="detective", difficulty="medium",
        scenario="Noise or Eve?",
        briefing=(
            "QBER is elevated. Is it the channel, or is it Eve? Compare what "
            "the LSTM thinks against the raw QBER number."
        ),
        param_ranges={
            "n_qubits": [400, 600],
            "depolarizing_prob": [0.025, 0.05],
            "eve_mode": ["none", "weak"],
        },
        fixed={"protocol": "bb84", "source_type": "ideal", "measurement_error_prob": 0.03},
        objective={"type": "verdict_plus_attack"},
        xp_reward=120,
    ),
    Mission(
        id="detective_l06_alt_protocol",
        level=6, type="detective", difficulty="medium",
        scenario="Alternative protocol",
        briefing=(
            "This run uses an alternative protocol — B92 or SARG04. The same "
            "rules apply: decide whether Eve is on the wire."
        ),
        param_ranges={
            "n_qubits": [400, 600],
            "protocol": ["b92", "sarg04"],
            "depolarizing_prob": [0.01, 0.025],
            "eve_mode": ["none", "weak"],
        },
        fixed={"source_type": "ideal", "measurement_error_prob": 0.02},
        objective={"type": "verdict_plus_attack"},
        xp_reward=120,
    ),

    # -----------------------------------------------------------------------
    # Levels 7–9 — Detective hard: Smart / PNS — needs LSTM or decoy bounds
    # -----------------------------------------------------------------------
    Mission(
        id="detective_l07_long_distance",
        level=7, type="detective", difficulty="hard",
        scenario="Long-distance channel",
        briefing=(
            "A 70-100 km fiber link. The key rate is already low; a weak Eve "
            "hiding in the channel loss is hard to spot from QBER alone."
        ),
        param_ranges={
            "n_qubits": [600, 800],
            "channel_distance_km": [70, 100],
            "depolarizing_prob": [0.01, 0.03],
            "eve_mode": ["none", "weak"],
        },
        fixed={"protocol": "bb84", "source_type": "ideal", "measurement_error_prob": 0.02},
        objective={"type": "verdict_plus_attack"},
        xp_reward=180,
    ),
    Mission(
        id="detective_l08_smart_eve",
        level=8, type="detective", difficulty="hard",
        scenario="Adaptive adversary",
        briefing=(
            "Eve, if she's present, throttles her intercept rate to keep QBER "
            "near the security threshold. The LSTM panel is your best friend."
        ),
        param_ranges={
            "n_qubits": [600, 800],
            "eve_mode": ["none", "smart"],
            "smart_target_qber": [0.07, 0.095],
        },
        fixed={
            "protocol": "bb84", "source_type": "ideal",
            "depolarizing_prob": 0.015, "measurement_error_prob": 0.02,
        },
        objective={"type": "verdict_plus_attack"},
        xp_reward=200,
    ),
    Mission(
        id="detective_l09_pns_threat",
        level=9, type="detective", difficulty="hard",
        scenario="Multi-photon pulses",
        briefing=(
            "The source emits weak coherent pulses (WCP) — not single photons. "
            "If Eve runs a Photon-Number-Splitting attack, QBER stays flat but "
            "the decoy-state Y1 bound collapses. Read the PNS panel."
        ),
        param_ranges={
            "n_qubits": [800, 1200],
            "eve_mode": ["none", "pns"],
        },
        fixed={
            "protocol": "bb84", "source_type": "wcp",
            "mu_signal": 0.5, "mu_decoy": 0.1,
            "p_signal": 0.7, "p_decoy": 0.15,
            "depolarizing_prob": 0.01, "measurement_error_prob": 0.02,
        },
        objective={"type": "verdict_plus_attack"},
        xp_reward=220,
    ),

    # -----------------------------------------------------------------------
    # Levels 10–12 — Engineer easy: configure to meet a simple target
    # -----------------------------------------------------------------------
    Mission(
        id="engineer_l10_office_link",
        level=10, type="engineer", difficulty="easy",
        scenario="Office-to-office link",
        briefing=(
            "Set up a short office link. Goal: at least 64 bits of finite-key "
            "secure output. Pick the protocol, EC method and qubit count."
        ),
        param_ranges={"channel_distance_km": [8, 15]},
        fixed={
            "eve_mode": "none",
            "depolarizing_prob": 0.01, "measurement_error_prob": 0.02,
            "source_type": "ideal",
        },
        user_chooses=["protocol", "ec_method", "n_qubits"],
        objective={"constraints": [
            {"metric": "finite_key.finite_length", "op": ">=", "value": 64},
            {"metric": "is_secure", "op": "==", "value": True},
        ]},
        xp_reward=120,
    ),
    Mission(
        id="engineer_l11_noisy_lab",
        level=11, type="engineer", difficulty="easy",
        scenario="Noisy lab — pick EC",
        briefing=(
            "QBER will be in the 4-6% range. Choose an error-correction method "
            "that survives this noise, and a qubit count that yields >= 32 bits "
            "of secure key."
        ),
        param_ranges={"depolarizing_prob": [0.03, 0.05]},
        fixed={
            "eve_mode": "none", "measurement_error_prob": 0.03,
            "protocol": "bb84", "source_type": "ideal", "channel_distance_km": 0,
        },
        user_chooses=["ec_method", "n_qubits"],
        objective={"constraints": [
            {"metric": "finite_key.finite_length", "op": ">=", "value": 32},
            {"metric": "is_secure", "op": "==", "value": True},
        ]},
        xp_reward=140,
    ),
    Mission(
        id="engineer_l12_e91_demo",
        level=12, type="engineer", difficulty="easy",
        scenario="Prove entanglement",
        briefing=(
            "Use the E91 protocol over a clean lab link. Goal: produce a Bell "
            "violation (S > 2) and yield at least 24 bits of secure key."
        ),
        param_ranges={"depolarizing_prob": [0.005, 0.015]},
        fixed={
            "eve_mode": "none", "measurement_error_prob": 0.015,
            "protocol": "e91", "source_type": "ideal", "channel_distance_km": 0,
        },
        user_chooses=["ec_method", "n_qubits"],
        objective={"constraints": [
            {"metric": "bell_test.S", "op": ">", "value": 2.0},
            {"metric": "finite_key.finite_length", "op": ">=", "value": 24},
        ]},
        xp_reward=160,
    ),

    # -----------------------------------------------------------------------
    # Levels 13–15 — Engineer hard: long distance, decoy, PNS resistance
    # -----------------------------------------------------------------------
    Mission(
        id="engineer_l13_metro_link",
        level=13, type="engineer", difficulty="hard",
        scenario="Metropolitan link",
        briefing=(
            "An 80 km metropolitan fiber. Target: >= 100 bits of finite-key "
            "secure output. The qubit budget is yours to choose."
        ),
        param_ranges={"channel_distance_km": [75, 90]},
        fixed={
            "eve_mode": "none",
            "depolarizing_prob": 0.015, "measurement_error_prob": 0.02,
            "source_type": "ideal",
        },
        user_chooses=["protocol", "ec_method", "n_qubits"],
        objective={"constraints": [
            {"metric": "finite_key.finite_length", "op": ">=", "value": 100},
            {"metric": "is_secure", "op": "==", "value": True},
        ]},
        xp_reward=220,
    ),
    Mission(
        id="engineer_l14_decoy_calibration",
        level=14, type="engineer", difficulty="hard",
        scenario="Decoy-state calibration",
        briefing=(
            "Weak-coherent source on a 50 km link. Pick signal/decoy "
            "intensities and probabilities so that Y1 >= 0.05 and you still "
            "yield >= 64 bits of secure key."
        ),
        param_ranges={},
        fixed={
            "eve_mode": "none", "channel_distance_km": 50,
            "depolarizing_prob": 0.01, "measurement_error_prob": 0.02,
            "protocol": "bb84", "source_type": "wcp", "n_qubits": 4000,
            "ec_method": "cascade",
        },
        user_chooses=["mu_signal", "mu_decoy", "p_signal", "p_decoy"],
        objective={"constraints": [
            {"metric": "decoy_state.Y1", "op": ">=", "value": 0.05},
            {"metric": "finite_key.finite_length", "op": ">=", "value": 64},
            {"metric": "is_secure", "op": "==", "value": True},
        ]},
        xp_reward=260,
    ),
    Mission(
        id="engineer_l15_pns_paranoia",
        level=15, type="engineer", difficulty="hard",
        scenario="Satellite uplink under PNS",
        briefing=(
            "A long-haul WCP link with a Photon-Number-Splitting attacker on "
            "the wire. Pick signal/decoy intensities so the decoy bounds catch "
            "her (Y1 collapses) and still get >= 32 bits of secure key."
        ),
        param_ranges={"channel_distance_km": [120, 150]},
        fixed={
            "eve_mode": "pns",
            "depolarizing_prob": 0.01, "measurement_error_prob": 0.02,
            "protocol": "bb84", "source_type": "wcp", "n_qubits": 5000,
            "ec_method": "cascade",
        },
        user_chooses=["mu_signal", "mu_decoy", "p_signal", "p_decoy"],
        objective={"constraints": [
            {"metric": "decoy_state.Y1", "op": "<", "value": 0.05},
            {"metric": "finite_key.finite_length", "op": ">=", "value": 32},
        ]},
        xp_reward=300,
    ),
]


# Lookup helpers -------------------------------------------------------------

MISSION_BY_ID: dict[str, Mission] = {m.id: m for m in MISSIONS}
MISSION_BY_LEVEL: dict[int, Mission] = {m.level: m for m in MISSIONS}

assert len(MISSIONS) == 15, "Catalog must contain exactly 15 missions"
assert sorted(m.level for m in MISSIONS) == list(range(1, 16)), \
    "Levels must be 1..15 contiguous"


def get_by_level(level: int) -> Mission | None:
    return MISSION_BY_LEVEL.get(level)


def get_by_id(template_id: str) -> Mission | None:
    return MISSION_BY_ID.get(template_id)


def all_missions() -> list[Mission]:
    return list(MISSIONS)
