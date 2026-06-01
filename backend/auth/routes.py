"""
Authentication endpoints.

Routes:
  POST   /api/v1/auth/register           — create account (email + password)
  POST   /api/v1/auth/login              — sign in with email + password
  POST   /api/v1/auth/logout             — clear all auth cookies
  GET    /api/v1/auth/me                 — return the current user (or 401)
  POST   /api/v1/auth/refresh            — mint a new access token using refresh cookie
  POST   /api/v1/auth/password/forgot    — request a password reset token
  POST   /api/v1/auth/password/reset     — submit a token + new password
  GET    /api/v1/auth/google/login       — start Google OAuth flow
  GET    /api/v1/auth/google/callback    — Google OAuth callback (sets cookies, redirects)
"""
import logging
import os
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from database.db import get_db
from database.models import User, PasswordResetToken
from auth.security import (
    ACCESS_COOKIE, REFRESH_COOKIE, CSRF_COOKIE, COOKIE_SECURE, COOKIE_SAMESITE,
    ACCESS_TOKEN_TTL_MIN, REFRESH_TOKEN_TTL_DAYS,
    hash_password, verify_password,
    create_access_token, create_refresh_token, decode_token,
    new_csrf_token,
    new_reset_token, hash_reset_token, reset_token_expiry,
)
from auth.schemas import (
    RegisterRequest, LoginRequest, ForgotPasswordRequest, ResetPasswordRequest,
    UserPublic, AuthResponse, ForgotPasswordResponse,
)
from auth.dependencies import require_user, require_csrf

log = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])

# Origin the frontend runs on — used for Google OAuth post-login redirect.
FRONTEND_ORIGIN = os.getenv("FRONTEND_ORIGIN", "http://localhost:5173")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _user_to_public(user: User) -> UserPublic:
    return UserPublic(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        avatar_url=user.avatar_url,
        is_email_verified=user.is_email_verified,
        created_at=user.created_at,
        has_google=user.google_id is not None,
        has_password=user.password_hash is not None,
    )


def _set_auth_cookies(response: Response, user: User) -> None:
    """Issue access + refresh + CSRF cookies for the given user."""
    access = create_access_token(user.id, user.email)
    refresh = create_refresh_token(user.id)
    csrf = new_csrf_token()

    common = dict(httponly=True, secure=COOKIE_SECURE, samesite=COOKIE_SAMESITE, path="/")

    response.set_cookie(
        ACCESS_COOKIE, access,
        max_age=ACCESS_TOKEN_TTL_MIN * 60, **common,
    )
    response.set_cookie(
        REFRESH_COOKIE, refresh,
        max_age=REFRESH_TOKEN_TTL_DAYS * 24 * 3600, **common,
    )
    # CSRF cookie must be readable by JS — it's the pair-half of the double-submit.
    response.set_cookie(
        CSRF_COOKIE, csrf,
        max_age=REFRESH_TOKEN_TTL_DAYS * 24 * 3600,
        httponly=False, secure=COOKIE_SECURE, samesite=COOKIE_SAMESITE, path="/",
    )


def _clear_auth_cookies(response: Response) -> None:
    for name in (ACCESS_COOKIE, REFRESH_COOKIE, CSRF_COOKIE):
        response.delete_cookie(name, path="/")


# ---------------------------------------------------------------------------
# Email / password
# ---------------------------------------------------------------------------

@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest, response: Response, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == payload.email.lower()).first()
    if existing:
        raise HTTPException(status.HTTP_409_CONFLICT, detail="Email already registered")

    user = User(
        email=payload.email.lower(),
        full_name=payload.full_name,
        password_hash=hash_password(payload.password),
        is_email_verified=False,
        last_login_at=datetime.utcnow(),
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    _set_auth_cookies(response, user)
    log.info("Registered new user id=%d email=%s", user.id, user.email)
    return AuthResponse(user=_user_to_public(user))


@router.post("/login", response_model=AuthResponse)
def login(payload: LoginRequest, response: Response, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email.lower()).first()
    if not user or not user.password_hash or not verify_password(payload.password, user.password_hash):
        # Same message for both branches — avoid leaking which emails exist.
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")

    user.last_login_at = datetime.utcnow()
    db.commit()
    _set_auth_cookies(response, user)
    return AuthResponse(user=_user_to_public(user))


@router.post("/logout", dependencies=[Depends(require_csrf)])
def logout(response: Response):
    _clear_auth_cookies(response)
    return {"ok": True}


@router.get("/me", response_model=UserPublic)
def me(user: User = Depends(require_user)):
    return _user_to_public(user)


@router.post("/refresh", response_model=AuthResponse)
def refresh(request: Request, response: Response, db: Session = Depends(get_db)):
    token = request.cookies.get(REFRESH_COOKIE)
    payload = decode_token(token, expected_type="refresh") if token else None
    if not payload:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    try:
        user_id = int(payload["sub"])
    except (KeyError, ValueError):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="User no longer exists")

    _set_auth_cookies(response, user)
    return AuthResponse(user=_user_to_public(user))


# ---------------------------------------------------------------------------
# Password reset
# ---------------------------------------------------------------------------

@router.post("/password/forgot", response_model=ForgotPasswordResponse)
def password_forgot(payload: ForgotPasswordRequest, db: Session = Depends(get_db)):
    """
    Issue a password reset token. In dev mode the plaintext token is returned
    so the UI can display it; a real deployment would email it and the
    `dev_reset_token` field would be omitted.
    """
    user = db.query(User).filter(User.email == payload.email.lower()).first()
    # We do NOT leak whether the email exists — always respond as if successful.
    if not user:
        return ForgotPasswordResponse(sent=True)

    plain, hashed = new_reset_token()
    db.add(PasswordResetToken(
        user_id=user.id,
        token_hash=hashed,
        expires_at=reset_token_expiry(),
    ))
    db.commit()

    log.info("Issued password reset token for user id=%d", user.id)
    # ---------------------------------------------------------------------
    # In production, the line below would be replaced with:
    #     send_password_reset_email(user.email, plain)
    # and `dev_reset_token` would NOT be returned.
    # ---------------------------------------------------------------------
    reset_url = f"{FRONTEND_ORIGIN}/reset-password?token={plain}"
    return ForgotPasswordResponse(sent=True, dev_reset_token=plain, dev_reset_url=reset_url)


@router.post("/password/reset", response_model=AuthResponse)
def password_reset(payload: ResetPasswordRequest, response: Response, db: Session = Depends(get_db)):
    token_hash = hash_reset_token(payload.token)
    record = (
        db.query(PasswordResetToken)
        .filter(PasswordResetToken.token_hash == token_hash)
        .first()
    )
    if not record or record.used_at is not None or record.expires_at < datetime.utcnow():
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Token invalid or expired")

    user = db.query(User).filter(User.id == record.user_id).first()
    if not user:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="User no longer exists")

    user.password_hash = hash_password(payload.new_password)
    user.last_login_at = datetime.utcnow()
    record.used_at = datetime.utcnow()
    db.commit()

    _set_auth_cookies(response, user)
    log.info("Password reset completed for user id=%d", user.id)
    return AuthResponse(user=_user_to_public(user))


# ---------------------------------------------------------------------------
# Google OAuth
# ---------------------------------------------------------------------------

@router.get("/google/login")
async def google_login(request: Request):
    from auth.oauth import oauth, GOOGLE_CONFIGURED
    if not GOOGLE_CONFIGURED:
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Google OAuth is not configured on the server",
        )
    redirect_uri = str(request.url_for("google_callback"))
    return await oauth.google.authorize_redirect(request, redirect_uri)


@router.get("/google/callback", name="google_callback")
async def google_callback(request: Request, db: Session = Depends(get_db)):
    from auth.oauth import oauth, GOOGLE_CONFIGURED
    if not GOOGLE_CONFIGURED:
        return RedirectResponse(f"{FRONTEND_ORIGIN}/?auth_error=google_not_configured")

    try:
        token = await oauth.google.authorize_access_token(request)
    except Exception as exc:
        log.warning("Google OAuth failed: %s", exc)
        return RedirectResponse(f"{FRONTEND_ORIGIN}/?auth_error=google_failed")

    userinfo = token.get("userinfo") or {}
    google_id = userinfo.get("sub")
    email = (userinfo.get("email") or "").lower()
    if not google_id or not email:
        return RedirectResponse(f"{FRONTEND_ORIGIN}/?auth_error=google_no_profile")

    user = db.query(User).filter(User.google_id == google_id).first()
    if not user:
        # Either link an existing email-only account or create a new one.
        user = db.query(User).filter(User.email == email).first()
        if user:
            user.google_id = google_id
        else:
            user = User(
                email=email,
                full_name=userinfo.get("name"),
                google_id=google_id,
                avatar_url=userinfo.get("picture"),
                is_email_verified=bool(userinfo.get("email_verified", True)),
            )
            db.add(user)
        db.flush()

    user.last_login_at = datetime.utcnow()
    db.commit()
    db.refresh(user)

    response = RedirectResponse(f"{FRONTEND_ORIGIN}/?auth=google_success")
    _set_auth_cookies(response, user)
    return response
