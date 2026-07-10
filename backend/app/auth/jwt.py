"""JWT token creation and verification."""

import uuid
from datetime import datetime, timedelta, timezone
from jose import jwt, JWTError
from app.config import settings


def create_access_token(user_id: str, role: str, jti: str | None = None) -> tuple[str, str, datetime]:
    """Create a JWT access token. Returns (token, jti, expires_at)."""
    jti = jti or str(uuid.uuid4())
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        "sub": user_id,
        "role": role,
        "jti": jti,
        "type": "access",
        "exp": expires_at,
        "iat": datetime.now(timezone.utc),
    }
    token = jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return token, jti, expires_at


def create_refresh_token(user_id: str, jti: str) -> tuple[str, datetime]:
    """Create a JWT refresh token. Returns (token, expires_at)."""
    expires_at = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    payload = {
        "sub": user_id,
        "jti": jti,
        "type": "refresh",
        "exp": expires_at,
        "iat": datetime.now(timezone.utc),
    }
    token = jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return token, expires_at


def decode_token(token: str) -> dict | None:
    """Decode and verify a JWT token. Returns payload or None if invalid."""
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        return payload
    except JWTError:
        return None


def create_verification_token() -> str:
    """Create a random token for email verification or password reset."""
    return str(uuid.uuid4())
