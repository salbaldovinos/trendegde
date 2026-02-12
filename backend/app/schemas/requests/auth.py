"""Pydantic request models for authentication endpoints."""

from __future__ import annotations

import re

from pydantic import BaseModel, EmailStr, Field, field_validator


class SignupRequest(BaseModel):
    """User registration request."""

    email: EmailStr
    password: str = Field(min_length=8)

    @field_validator("email", mode="after")
    @classmethod
    def lowercase_email(cls, v: str) -> str:
        return v.lower()

    @field_validator("password")
    @classmethod
    def validate_password_complexity(cls, v: str) -> str:
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain at least 1 uppercase letter.")
        if not re.search(r"[a-z]", v):
            raise ValueError("Password must contain at least 1 lowercase letter.")
        if not re.search(r"\d", v):
            raise ValueError("Password must contain at least 1 digit.")
        if not re.search(r"[!@#$%^&*]", v):
            raise ValueError(
                "Password must contain at least 1 special character (!@#$%^&*)."
            )
        return v


class LoginRequest(BaseModel):
    """User login request."""

    email: EmailStr
    password: str = Field(min_length=1)

    @field_validator("email", mode="after")
    @classmethod
    def lowercase_email(cls, v: str) -> str:
        return v.lower()


class RefreshRequest(BaseModel):
    """Token refresh request."""

    refresh_token: str = Field(min_length=1)
