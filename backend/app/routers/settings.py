"""Settings API endpoints — user preferences and platform configuration."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import Optional

from app.database import get_db
from app.auth.dependencies import get_current_user
from app.models.user import User, UserProfile

router = APIRouter(prefix="/settings", tags=["Settings"])


class ProfileUpdate(BaseModel):
    full_name: Optional[str] = None
    bio: Optional[str] = None
    company: Optional[str] = None
    country: Optional[str] = None
    language: Optional[str] = None
    timezone: Optional[str] = None


class ProfileResponse(BaseModel):
    id: str
    email: str
    full_name: str
    role: str
    is_verified: bool
    bio: Optional[str] = None
    company: Optional[str] = None
    country: Optional[str] = None
    language: Optional[str] = None
    timezone: Optional[str] = None
    profile_picture_url: Optional[str] = None

    model_config = {"from_attributes": True}


@router.get("/profile", response_model=ProfileResponse)
async def get_profile(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get user profile with settings."""
    profile_result = await db.execute(
        select(UserProfile).where(UserProfile.user_id == current_user.id)
    )
    profile = profile_result.scalar_one_or_none()

    return ProfileResponse(
        id=current_user.id,
        email=current_user.email,
        full_name=current_user.full_name,
        role=current_user.role,
        is_verified=current_user.is_verified,
        bio=profile.bio if profile else None,
        company=profile.company if profile else None,
        country=profile.country if profile else None,
        language=profile.language if profile else None,
        timezone=profile.timezone if profile else None,
        profile_picture_url=profile.profile_picture_url if profile else None,
    )


@router.patch("/profile", response_model=ProfileResponse)
async def update_profile(
    req: ProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update user profile."""
    if req.full_name is not None:
        current_user.full_name = req.full_name

    profile_result = await db.execute(
        select(UserProfile).where(UserProfile.user_id == current_user.id)
    )
    profile = profile_result.scalar_one_or_none()

    if not profile:
        profile = UserProfile(user_id=current_user.id)
        db.add(profile)

    if req.bio is not None:
        profile.bio = req.bio
    if req.company is not None:
        profile.company = req.company
    if req.country is not None:
        profile.country = req.country
    if req.language is not None:
        profile.language = req.language
    if req.timezone is not None:
        profile.timezone = req.timezone

    await db.commit()
    await db.refresh(current_user)

    return ProfileResponse(
        id=current_user.id,
        email=current_user.email,
        full_name=current_user.full_name,
        role=current_user.role,
        is_verified=current_user.is_verified,
        bio=profile.bio,
        company=profile.company,
        country=profile.country,
        language=profile.language,
        timezone=profile.timezone,
        profile_picture_url=profile.profile_picture_url,
    )


@router.get("/system-info")
async def get_system_info(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get system configuration info."""
    from app.config import settings as cfg
    from sqlalchemy import text
    import os

    # Get DB file size if SQLite
    db_size_mb = 0
    db_url = cfg.DATABASE_URL
    if "sqlite" in db_url:
        db_path = db_url.replace("sqlite+aiosqlite:///", "").replace("sqlite:///", "")
        if os.path.exists(db_path):
            db_size_mb = round(os.path.getsize(db_path) / (1024 * 1024), 2)

    return {
        "app_name": cfg.APP_NAME,
        "app_version": cfg.APP_VERSION,
        "gemini_model": cfg.GEMINI_MODEL,
        "database_type": "SQLite" if "sqlite" in cfg.DATABASE_URL else "PostgreSQL",
        "database_size_mb": db_size_mb,
        "email_mode": cfg.EMAIL_MODE,
        "debug_mode": cfg.DEBUG,
    }
