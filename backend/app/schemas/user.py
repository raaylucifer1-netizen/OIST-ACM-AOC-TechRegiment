"""User profile schemas."""

from pydantic import BaseModel, EmailStr
from datetime import datetime


class UserResponse(BaseModel):
    id: str
    email: str
    full_name: str
    role: str
    is_verified: bool
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class UserProfileResponse(BaseModel):
    id: str
    user_id: str
    bio: str | None = None
    company: str | None = None
    country: str | None = None
    language: str | None = None
    timezone: str | None = None
    profile_picture_url: str | None = None

    model_config = {"from_attributes": True}


class UserProfileUpdate(BaseModel):
    full_name: str | None = None
    bio: str | None = None
    company: str | None = None
    country: str | None = None
    language: str | None = None
    timezone: str | None = None


class SessionResponse(BaseModel):
    id: str
    device_name: str | None = None
    browser: str | None = None
    os: str | None = None
    ip_address: str | None = None
    is_active: bool
    login_at: datetime
    last_active_at: datetime

    model_config = {"from_attributes": True}
