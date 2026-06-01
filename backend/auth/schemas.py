"""Pydantic request/response models for the auth endpoints."""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    full_name: Optional[str] = Field(default=None, max_length=120)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str = Field(min_length=10, max_length=200)
    new_password: str = Field(min_length=8, max_length=128)


class UserPublic(BaseModel):
    id: int
    email: EmailStr
    full_name: Optional[str] = None
    avatar_url: Optional[str] = None
    is_email_verified: bool
    created_at: datetime
    has_google: bool = False
    has_password: bool = False


class AuthResponse(BaseModel):
    user: UserPublic


class ForgotPasswordResponse(BaseModel):
    sent: bool
    # In dev mode we surface the token directly so the frontend can show it.
    # In a production deployment the token would only be delivered via email
    # and this field would be omitted.
    dev_reset_token: Optional[str] = None
    dev_reset_url: Optional[str] = None
