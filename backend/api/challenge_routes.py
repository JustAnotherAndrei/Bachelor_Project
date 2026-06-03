"""
Challenge Mode REST API.

Endpoints (all under /api/v1/challenge):

  GET    /levels              — catalog + per-user unlock/completion status
  POST   /level/{n}/start     — roll parameters for a fresh attempt
  POST   /attempts            — submit a completed attempt, get graded
  GET    /progress            — current user's XP, streak, unlocks
  GET    /leaderboard         — global top-N by XP
  GET    /attempts/recent     — current user's recent attempts

Authentication:
  /levels and /progress       — work for guests (return locked/empty data)
  /level/{n}/start            — requires signed-in user (must be unlocked)
  /attempts                   — requires signed-in user + CSRF
  /leaderboard                — public
  /attempts/recent            — requires signed-in user
"""

from __future__ import annotations

import random
import secrets
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from auth.dependencies import (
    get_current_user_optional,
    require_user,
    require_csrf,
)
from database.db import get_db
from database.models import User

from challenge import grader as grader_mod
from challenge import persistence
from challenge.instantiator import instantiate
from challenge.mission_catalog import get_by_id, get_by_level


router = APIRouter(prefix="/api/v1/challenge", tags=["challenge"])

MAX_LEVEL = 15


# ---------------------------------------------------------------------------
# Pydantic schemas
# ---------------------------------------------------------------------------

class StartLevelResponse(BaseModel):
    mission: dict
    instantiated_params: dict
    nonce: str  # opaque token the client echoes back on /attempts (anti-replay)


class SubmitAttemptRequest(BaseModel):
    template_id: str
    instantiated_params: dict
    sim_result: dict
    user_answer: dict
    nonce: Optional[str] = None
    simulation_run_id: Optional[int] = None


class SubmitAttemptResponse(BaseModel):
    correct: bool
    score: int
    xp_earned: int
    breakdown: dict
    explanation: str
    truth: Optional[dict] = None
    progress: dict


class ProgressResponse(BaseModel):
    levels_unlocked: int
    levels_completed: int
    total_xp: int
    current_streak: int
    best_streak: int


# ---------------------------------------------------------------------------
# /levels — catalog with per-user status
# ---------------------------------------------------------------------------

@router.get("/levels")
def list_levels(
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    user_id = current_user.id if current_user else None
    return {"levels": persistence.list_levels_with_status(db, user_id)}


# ---------------------------------------------------------------------------
# /level/{n}/start — instantiate a fresh attempt
# ---------------------------------------------------------------------------

@router.post("/level/{level}/start", response_model=StartLevelResponse)
def start_level(
    level: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_user),
    _csrf: None = Depends(require_csrf),
):
    mission = get_by_level(level)
    if mission is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Unknown level")

    progress = persistence.get_or_create_progress(db, current_user.id)
    if level > progress.levels_unlocked:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            f"Level {level} is locked. Complete level {progress.levels_unlocked} first.",
        )

    rng = random.Random()
    instantiated = instantiate(mission, rng=rng)

    return StartLevelResponse(
        mission=mission.to_public_dict(),
        instantiated_params=instantiated,
        nonce=secrets.token_urlsafe(12),
    )


# ---------------------------------------------------------------------------
# /attempts — submit a completed attempt, grade it
# ---------------------------------------------------------------------------

@router.post("/attempts", response_model=SubmitAttemptResponse)
def submit_attempt(
    body: SubmitAttemptRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_user),
    _csrf: None = Depends(require_csrf),
):
    mission = get_by_id(body.template_id)
    if mission is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Unknown template")

    grading = grader_mod.grade(
        mission=mission,
        instantiated=body.instantiated_params,
        sim_result=body.sim_result,
        user_answer=body.user_answer,
    )

    persistence.record_attempt(
        db=db,
        user_id=current_user.id,
        mission=mission,
        instantiated=body.instantiated_params,
        user_answer=body.user_answer,
        grading_result=grading,
        simulation_run_id=body.simulation_run_id,
    )
    progress = persistence.recompute_progress(db, current_user.id)

    return SubmitAttemptResponse(
        correct=grading["correct"],
        score=grading["score"],
        xp_earned=grading.get("xp_earned", 0),
        breakdown=grading["breakdown"],
        explanation=grading.get("explanation", ""),
        truth=grading.get("truth"),
        progress={
            "levels_unlocked": progress.levels_unlocked,
            "levels_completed": progress.levels_completed,
            "total_xp": progress.total_xp,
            "current_streak": progress.current_streak,
            "best_streak": progress.best_streak,
        },
    )


# ---------------------------------------------------------------------------
# /progress — current user's stats
# ---------------------------------------------------------------------------

@router.get("/progress", response_model=ProgressResponse)
def get_progress(
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    if not current_user:
        return ProgressResponse(
            levels_unlocked=1, levels_completed=0,
            total_xp=0, current_streak=0, best_streak=0,
        )
    p = persistence.get_or_create_progress(db, current_user.id)
    return ProgressResponse(
        levels_unlocked=p.levels_unlocked,
        levels_completed=p.levels_completed,
        total_xp=p.total_xp,
        current_streak=p.current_streak,
        best_streak=p.best_streak,
    )


# ---------------------------------------------------------------------------
# /leaderboard — global top-N
# ---------------------------------------------------------------------------

@router.get("/leaderboard")
def get_leaderboard(
    limit: int = 50,
    db: Session = Depends(get_db),
):
    limit = max(1, min(limit, 100))
    return {"leaderboard": persistence.leaderboard(db, limit=limit)}


# ---------------------------------------------------------------------------
# /attempts/recent — user's history (for the profile / progress panel)
# ---------------------------------------------------------------------------

@router.get("/attempts/recent")
def get_recent_attempts(
    limit: int = 20,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_user),
):
    import json as _json
    limit = max(1, min(limit, 100))
    rows = persistence.list_attempts_for_user(db, current_user.id, limit=limit)
    out = []
    for a in rows:
        try:
            feedback = _json.loads(a.feedback) if a.feedback else {}
        except (ValueError, TypeError):
            feedback = {}
        out.append({
            "id": a.id,
            "template_id": a.template_id,
            "level": a.level_number,
            "correct": a.correct,
            "score": a.score,
            "xp_earned": feedback.get("xp_earned", 0),
            "completed_at": a.completed_at.isoformat() if a.completed_at else None,
        })
    return {"attempts": out}
