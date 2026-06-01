"""
Auth primitives: password hashing, JWT issuance, CSRF helpers.

Tokens are issued as two JWTs:
  - access_token: short-lived (30 min), used for request auth
  - refresh_token: long-lived (7 days), used to mint new access tokens

Both are placed in httpOnly cookies. A separate non-httpOnly `csrf_token`
cookie pairs with an X-CSRF-Token header (double-submit pattern) to prevent
CSRF on state-changing requests.
"""
import os
import secrets
import hashlib
from datetime import datetime, timedelta, timezone
from typing import Literal, Optional

import bcrypt
from jose import jwt, JWTError


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

JWT_SECRET = os.getenv("JWT_SECRET", "dev-secret-change-me-in-production-please-please")
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_TTL_MIN = 30
REFRESH_TOKEN_TTL_DAYS = 7
RESET_TOKEN_TTL_MIN = 15

# Cookie names — referenced from routes
ACCESS_COOKIE = "sequre_access"
REFRESH_COOKIE = "sequre_refresh"
CSRF_COOKIE = "sequre_csrf"
CSRF_HEADER = "X-CSRF-Token"

# Set Secure=True in production (HTTPS). Local dev runs over plain HTTP.
COOKIE_SECURE = os.getenv("COOKIE_SECURE", "false").lower() == "true"
COOKIE_SAMESITE: Literal["lax", "strict", "none"] = "lax"


# bcrypt has a 72-byte input limit. Anything longer is silently truncated by
# the native bindings on hash but not on verify (which raises). We pre-truncate
# on both sides for consistency. UTF-8 is encoded first because bcrypt operates
# on bytes — multi-byte chars count as their full byte length.
def _prep(password: str) -> bytes:
    return password.encode("utf-8")[:72]


def hash_password(password: str) -> str:
    return bcrypt.hashpw(_prep(password), bcrypt.gensalt()).decode("ascii")


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(_prep(plain), hashed.encode("ascii"))
    except Exception:
        return False


# ---------------------------------------------------------------------------
# JWT — access & refresh tokens
# ---------------------------------------------------------------------------

def _encode(payload: dict, ttl: timedelta) -> str:
    now = datetime.now(timezone.utc)
    payload = {**payload, "iat": now, "exp": now + ttl}
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def create_access_token(user_id: int, email: str) -> str:
    return _encode(
        {"sub": str(user_id), "email": email, "type": "access"},
        timedelta(minutes=ACCESS_TOKEN_TTL_MIN),
    )


def create_refresh_token(user_id: int) -> str:
    return _encode(
        {"sub": str(user_id), "type": "refresh"},
        timedelta(days=REFRESH_TOKEN_TTL_DAYS),
    )


def decode_token(token: str, expected_type: str) -> Optional[dict]:
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except JWTError:
        return None
    if payload.get("type") != expected_type:
        return None
    return payload


# ---------------------------------------------------------------------------
# CSRF — double-submit cookie pattern
# ---------------------------------------------------------------------------

def new_csrf_token() -> str:
    return secrets.token_urlsafe(32)


# ---------------------------------------------------------------------------
# Password reset tokens
# ---------------------------------------------------------------------------

def new_reset_token() -> tuple[str, str]:
    """Return (plaintext token to email/show, sha256 hash to store)."""
    plain = secrets.token_urlsafe(32)
    hashed = hashlib.sha256(plain.encode()).hexdigest()
    return plain, hashed


def hash_reset_token(plain: str) -> str:
    return hashlib.sha256(plain.encode()).hexdigest()


def reset_token_expiry() -> datetime:
    return datetime.utcnow() + timedelta(minutes=RESET_TOKEN_TTL_MIN)
