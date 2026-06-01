"""FastAPI dependencies for extracting the current user and enforcing CSRF."""
from typing import Optional
from fastapi import Cookie, Depends, Header, HTTPException, Request, status
from sqlalchemy.orm import Session

from database.db import get_db
from database.models import User
from auth.security import (
    ACCESS_COOKIE, CSRF_COOKIE, CSRF_HEADER, decode_token,
)


def _user_from_token(token: Optional[str], db: Session) -> Optional[User]:
    if not token:
        return None
    payload = decode_token(token, expected_type="access")
    if not payload:
        return None
    try:
        user_id = int(payload["sub"])
    except (KeyError, ValueError):
        return None
    return db.query(User).filter(User.id == user_id).first()


def get_current_user_optional(
    request: Request,
    db: Session = Depends(get_db),
) -> Optional[User]:
    """Return the authenticated user, or None if no/invalid session.

    Used on routes that work for both guests and signed-in users (e.g. the
    simulation endpoints — guests can still run simulations).
    """
    token = request.cookies.get(ACCESS_COOKIE)
    return _user_from_token(token, db)


def require_user(
    request: Request,
    db: Session = Depends(get_db),
) -> User:
    """Return the authenticated user or raise 401."""
    token = request.cookies.get(ACCESS_COOKIE)
    user = _user_from_token(token, db)
    if not user:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    return user


def require_csrf(
    request: Request,
    x_csrf_token: Optional[str] = Header(default=None, alias=CSRF_HEADER),
) -> None:
    """Verify CSRF for state-changing requests.

    The frontend reads the non-httpOnly `sequre_csrf` cookie and echoes it in
    the `X-CSRF-Token` header. We require both sides to match.
    """
    cookie_value = request.cookies.get(CSRF_COOKIE)
    if not cookie_value or not x_csrf_token or cookie_value != x_csrf_token:
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="CSRF token invalid")
