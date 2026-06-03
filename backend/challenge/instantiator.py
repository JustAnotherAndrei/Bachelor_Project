"""
Mission instantiator — rolls concrete parameter values from a Mission's
`param_ranges` and merges them with the `fixed` block.

Range encoding:
  - [low, high]                  numeric range (uniform); int if both ints
  - ["opt_a", "opt_b", ...]     categorical (rng.choice)
  - non-list value               passed through unchanged
"""

from __future__ import annotations

import random
from typing import Any

from challenge.mission_catalog import Mission


def instantiate(mission: Mission, rng: random.Random | None = None) -> dict[str, Any]:
    """
    Roll a concrete parameter set for one attempt of `mission`.

    The returned dict contains the rolled `param_ranges` keys plus all
    `fixed` keys — but NOT the keys the user will choose themselves
    (Engineer missions). Use `merge_user_choices` to add those on submit.
    """
    rng = rng or random.Random()
    rolled: dict[str, Any] = {}

    for key, spec in mission.param_ranges.items():
        rolled[key] = _roll(spec, rng)

    # Fixed params take precedence (defensive: catalog should not declare
    # the same key in both blocks, but make the override explicit anyway).
    rolled.update(mission.fixed)
    return rolled


def _roll(spec: Any, rng: random.Random) -> Any:
    if not isinstance(spec, (list, tuple)):
        return spec

    # Numeric [lo, hi]
    if (len(spec) == 2
            and all(isinstance(v, (int, float)) and not isinstance(v, bool) for v in spec)):
        lo, hi = spec
        if isinstance(lo, int) and isinstance(hi, int):
            return rng.randint(lo, hi)
        return round(rng.uniform(lo, hi), 4)

    # Categorical
    return rng.choice(list(spec))


def merge_user_choices(instantiated: dict, user_choices: dict) -> dict:
    """
    Compose the final simulation config from the rolled scenario plus the
    user's Engineer-mode choices. User choices win on key conflict.
    """
    merged = dict(instantiated)
    merged.update({k: v for k, v in user_choices.items() if v is not None})
    return merged
