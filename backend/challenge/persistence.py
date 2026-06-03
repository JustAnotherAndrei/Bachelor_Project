"""
Persistence layer for Challenge Mode.

Two responsibilities:
  1. Recording mission attempts and (re)computing per-user progress.
  2. Aggregating progress across users for the global leaderboard.

Progress is recomputed from attempts on every write — this is O(N) per user
but N is tiny (~hundreds of attempts max) and avoids drift between the
attempts table and the cached progress row.
"""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any, Optional

from sqlalchemy import func, case
from sqlalchemy.orm import Session

from database.models import MissionAttempt, User, UserProgress
from challenge.mission_catalog import Mission, MISSION_BY_ID, get_by_id


MAX_LEVEL = 15


# ---------------------------------------------------------------------------
# Attempts
# ---------------------------------------------------------------------------

def record_attempt(
    db: Session,
    user_id: int,
    mission: Mission,
    instantiated: dict,
    user_answer: dict,
    grading_result: dict,
    simulation_run_id: Optional[int] = None,
) -> MissionAttempt:
    """Insert a new MissionAttempt row and commit."""
    now = datetime.utcnow()
    attempt = MissionAttempt(
        user_id=user_id,
        template_id=mission.id,
        level_number=mission.level,
        instantiated_params=json.dumps(instantiated, default=_json_default),
        user_answer=json.dumps(user_answer, default=_json_default),
        correct=bool(grading_result["correct"]),
        score=int(grading_result["score"]),
        feedback=json.dumps(grading_result, default=_json_default),
        simulation_run_id=simulation_run_id,
        started_at=now,
        completed_at=now,
    )
    db.add(attempt)
    db.commit()
    db.refresh(attempt)
    return attempt


def list_attempts_for_user(db: Session, user_id: int, limit: int = 100
                           ) -> list[MissionAttempt]:
    return (
        db.query(MissionAttempt)
        .filter(MissionAttempt.user_id == user_id)
        .order_by(MissionAttempt.id.desc())
        .limit(limit)
        .all()
    )


# ---------------------------------------------------------------------------
# Progress
# ---------------------------------------------------------------------------

def get_or_create_progress(db: Session, user_id: int) -> UserProgress:
    progress = (
        db.query(UserProgress)
        .filter(UserProgress.user_id == user_id)
        .first()
    )
    if progress is None:
        progress = UserProgress(user_id=user_id, levels_unlocked=1)
        db.add(progress)
        db.commit()
        db.refresh(progress)
    return progress


def recompute_progress(db: Session, user_id: int) -> UserProgress:
    """
    Walk every attempt for this user and rebuild the UserProgress row.

    - levels_unlocked  = max(level completed) + 1, capped at 15
    - levels_completed = count of distinct levels with at least one correct attempt
    - total_xp         = sum of xp_earned over best correct attempt per level
                         (so re-playing a level doesn't farm XP)
    - current_streak   = consecutive correct attempts ending at the latest one
    - best_streak      = longest run of consecutive correct attempts ever
    """
    progress = get_or_create_progress(db, user_id)

    attempts = (
        db.query(MissionAttempt)
        .filter(MissionAttempt.user_id == user_id)
        .order_by(MissionAttempt.id.asc())
        .all()
    )

    completed_levels: set[int] = set()
    xp_per_level: dict[int, int] = {}
    current_streak = 0
    best_streak = 0
    longest = 0

    for a in attempts:
        if a.correct:
            completed_levels.add(a.level_number)
            xp = _xp_from_feedback(a.feedback)
            xp_per_level[a.level_number] = max(xp_per_level.get(a.level_number, 0), xp)
            current_streak += 1
            longest = max(longest, current_streak)
        else:
            current_streak = 0

    best_streak = longest
    max_completed = max(completed_levels, default=0)

    progress.levels_completed = len(completed_levels)
    progress.levels_unlocked = min(max_completed + 1, MAX_LEVEL) if max_completed else 1
    progress.total_xp = sum(xp_per_level.values())
    progress.current_streak = current_streak
    progress.best_streak = best_streak
    progress.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(progress)
    return progress


def _xp_from_feedback(feedback_json: Optional[str]) -> int:
    if not feedback_json:
        return 0
    try:
        d = json.loads(feedback_json)
        return int(d.get("xp_earned", 0))
    except (ValueError, TypeError):
        return 0


# ---------------------------------------------------------------------------
# Level catalog + completion status (for the LevelGrid UI)
# ---------------------------------------------------------------------------

def list_levels_with_status(db: Session, user_id: Optional[int]) -> list[dict]:
    """
    Return all 15 missions with per-user unlock/completion status.

    For guest users (user_id=None), only level 1 is unlocked and nothing is
    completed — gates the rest of the catalog behind sign-in.
    """
    from challenge.mission_catalog import all_missions

    if user_id is None:
        unlocked = 1
        completed_levels: set[int] = set()
        best_scores: dict[int, int] = {}
    else:
        progress = get_or_create_progress(db, user_id)
        unlocked = progress.levels_unlocked
        completed_levels, best_scores = _completed_and_best(db, user_id)

    out = []
    for m in all_missions():
        out.append({
            **m.to_public_dict(),
            "unlocked": m.level <= unlocked,
            "completed": m.level in completed_levels,
            "best_score": best_scores.get(m.level, 0),
        })
    return out


def _completed_and_best(db: Session, user_id: int
                        ) -> tuple[set[int], dict[int, int]]:
    rows = (
        db.query(
            MissionAttempt.level_number,
            func.max(MissionAttempt.score).label("best"),
            func.sum(case((MissionAttempt.correct == True, 1), else_=0)).label("n_correct"),
        )
        .filter(MissionAttempt.user_id == user_id)
        .group_by(MissionAttempt.level_number)
        .all()
    )
    completed = {r.level_number for r in rows if (r.n_correct or 0) > 0}
    best = {r.level_number: int(r.best or 0) for r in rows}
    return completed, best


# ---------------------------------------------------------------------------
# Leaderboard
# ---------------------------------------------------------------------------

def leaderboard(db: Session, limit: int = 50) -> list[dict]:
    """
    Top users by total_xp, with display name + avatar.

    A user must have at least one row in user_progress to appear — i.e.
    must have completed at least one attempt.
    """
    rows = (
        db.query(UserProgress, User)
        .join(User, User.id == UserProgress.user_id)
        .order_by(UserProgress.total_xp.desc(),
                  UserProgress.levels_completed.desc(),
                  UserProgress.best_streak.desc())
        .limit(limit)
        .all()
    )
    out = []
    for rank, (prog, user) in enumerate(rows, start=1):
        out.append({
            "rank": rank,
            "user_id": user.id,
            "display_name": _display_name(user),
            "avatar_url": user.avatar_url,
            "total_xp": prog.total_xp,
            "levels_completed": prog.levels_completed,
            "best_streak": prog.best_streak,
        })
    return out


def _display_name(user: User) -> str:
    if user.full_name:
        return user.full_name
    if user.email:
        return user.email.split("@")[0]
    return f"User #{user.id}"


# ---------------------------------------------------------------------------
# JSON helpers
# ---------------------------------------------------------------------------

def _json_default(o: Any):
    if isinstance(o, datetime):
        return o.isoformat()
    return str(o)
