"""
Axon by NeuroVexon - Authentication API
"""

import re
import logging

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from db.database import get_db
from db.models import User
from core.config import settings
from core.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    create_refresh_token,
    decode_token,
)
from core.dependencies import get_current_active_user
from core.i18n import t

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])

EMAIL_RE = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")


# --- Schemas ---


class RegisterRequest(BaseModel):
    email: str
    password: str
    display_name: str | None = None


class RefreshRequest(BaseModel):
    refresh_token: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: dict


class AuthStatusResponse(BaseModel):
    has_users: bool
    registration_enabled: bool


# --- Helpers ---


def _user_dict(user: User) -> dict:
    return {
        "id": user.id,
        "email": user.email,
        "display_name": user.display_name,
        "role": user.role,
        "is_active": user.is_active,
        "created_at": user.created_at.isoformat() if user.created_at else None,
    }


def _create_tokens(user: User) -> dict:
    data = {"sub": user.id}
    return {
        "access_token": create_access_token(data),
        "refresh_token": create_refresh_token(data),
        "token_type": "bearer",
        "user": _user_dict(user),
    }


# --- Endpoints ---


@router.get("/status")
async def auth_status(db: AsyncSession = Depends(get_db)) -> AuthStatusResponse:
    """Public: Check if users exist and if registration is enabled"""
    result = await db.execute(select(func.count(User.id)))
    user_count = result.scalar() or 0
    return AuthStatusResponse(
        has_users=user_count > 0,
        registration_enabled=settings.registration_enabled,
    )


@router.post("/register")
async def register(data: RegisterRequest, db: AsyncSession = Depends(get_db)):
    """Register a new user. First user becomes admin."""
    # Check registration enabled
    result = await db.execute(select(func.count(User.id)))
    user_count = result.scalar() or 0

    if user_count > 0 and not settings.registration_enabled:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=t("auth.registration_disabled"),
        )

    # Validate email
    if not EMAIL_RE.match(data.email):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=t("auth.invalid_email"),
        )

    # Validate password
    if len(data.password) < 8:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=t("auth.password_too_short"),
        )

    # Check email unique
    existing = await db.execute(select(User).where(User.email == data.email))
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=t("auth.email_exists"),
        )

    # Create user - first user is admin
    role = "admin" if user_count == 0 else "user"
    user = User(
        email=data.email,
        password_hash=get_password_hash(data.password),
        display_name=data.display_name or data.email.split("@")[0],
        role=role,
    )
    db.add(user)
    await db.flush()

    logger.info(f"User registered: {user.email} (role={role})")
    return _create_tokens(user)


@router.post("/login")
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
):
    """OAuth2-compatible login (form data: username=email, password)"""
    result = await db.execute(select(User).where(User.email == form_data.username))
    user = result.scalar_one_or_none()

    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=t("auth.invalid_credentials"),
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=t("auth.account_disabled"),
        )

    logger.info(f"User logged in: {user.email}")
    return _create_tokens(user)


@router.post("/refresh")
async def refresh_token(data: RefreshRequest, db: AsyncSession = Depends(get_db)):
    """Get new token pair using a valid refresh token"""
    payload = decode_token(data.refresh_token)
    if payload is None or payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=t("auth.invalid_refresh_token"),
        )

    user_id = payload.get("sub")
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=t("auth.invalid_refresh_token"),
        )

    return _create_tokens(user)


@router.get("/me")
async def get_me(current_user: User = Depends(get_current_active_user)):
    """Get current authenticated user"""
    return _user_dict(current_user)


@router.post("/logout")
async def logout():
    """Stateless logout — client should discard tokens"""
    return {"detail": t("auth.logout_success")}
