"""Auth dependencies — JWT extraction and user resolution."""

from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.auth.jwt import decode_token
from app.models.user import User
from app.models.session import UserSession

security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Extract and validate JWT, return the authenticated user."""
    token = credentials.credentials
    payload = decode_token(token)

    if payload is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")

    if payload.get("type") != "access":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token type")

    user_id = payload.get("sub")
    jti = payload.get("jti")

    if not user_id or not jti:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload")

    # Verify session is still active
    session_result = await db.execute(
        select(UserSession).where(UserSession.jwt_jti == jti, UserSession.is_active == True)
    )
    session = session_result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Session has been revoked")

    # Get user
    user_result = await db.execute(select(User).where(User.id == user_id))
    user = user_result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is deactivated")

    if user.is_locked:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is locked")

    if not user.is_verified:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Email not verified")

    return user


def require_role(role: str):
    """Dependency factory to enforce role-based access."""
    async def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role != role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Requires {role} role",
            )
        return current_user
    return role_checker


require_admin = require_role("admin")
