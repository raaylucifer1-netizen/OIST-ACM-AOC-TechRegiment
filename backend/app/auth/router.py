"""Auth API endpoints — register, login, verify, password management, sessions."""

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.auth.service import (
    register_user, verify_email, login_user, refresh_access_token,
    logout_session, logout_all_sessions, forgot_password, reset_password, change_password,
)
from app.auth.dependencies import get_current_user
from app.auth.jwt import decode_token
from app.models.user import User
from app.models.session import UserSession
from app.schemas.auth import (
    RegisterRequest, LoginRequest, TokenResponse, RefreshRequest,
    ForgotPasswordRequest, ResetPasswordRequest, ChangePasswordRequest,
    VerifyEmailRequest, MessageResponse,
)
from app.schemas.user import UserResponse, SessionResponse

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=MessageResponse, status_code=201)
async def register(req: RegisterRequest, db: AsyncSession = Depends(get_db)):
    """Register a new user account."""
    user = await register_user(db, req.email, req.full_name, req.password)
    return MessageResponse(
        message="Registration successful. Please check your email to verify your account.",
        detail=f"Verification email sent to {req.email}",
    )


@router.post("/verify-email", response_model=MessageResponse)
async def verify(req: VerifyEmailRequest, db: AsyncSession = Depends(get_db)):
    """Verify email address using the token from the verification email."""
    await verify_email(db, req.token)
    return MessageResponse(message="Email verified successfully. You can now log in.")


@router.post("/login", response_model=TokenResponse)
async def login(req: LoginRequest, request: Request, db: AsyncSession = Depends(get_db)):
    """Authenticate user and return JWT tokens."""
    ip = request.client.host if request.client else None
    ua = request.headers.get("user-agent", "")
    return await login_user(db, req.email, req.password, ip_address=ip, user_agent=ua)


@router.post("/refresh", response_model=TokenResponse)
async def refresh(req: RefreshRequest, db: AsyncSession = Depends(get_db)):
    """Refresh access token using a valid refresh token."""
    return await refresh_access_token(db, req.refresh_token)


@router.post("/forgot-password", response_model=MessageResponse)
async def forgot_pw(req: ForgotPasswordRequest, db: AsyncSession = Depends(get_db)):
    """Request a password reset link."""
    await forgot_password(db, req.email)
    return MessageResponse(message="If the email exists, a reset link has been sent.")


@router.post("/reset-password", response_model=MessageResponse)
async def reset_pw(req: ResetPasswordRequest, db: AsyncSession = Depends(get_db)):
    """Reset password using the token from the reset email."""
    await reset_password(db, req.token, req.new_password)
    return MessageResponse(message="Password has been reset successfully. Please log in again.")


@router.post("/change-password", response_model=MessageResponse)
async def change_pw(
    req: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Change password for the authenticated user."""
    await change_password(db, current_user, req.old_password, req.new_password)
    return MessageResponse(message="Password changed successfully.")


@router.post("/logout", response_model=MessageResponse)
async def logout(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Logout current session."""
    auth_header = request.headers.get("authorization", "")
    token = auth_header.replace("Bearer ", "")
    payload = decode_token(token)
    if payload:
        await logout_session(db, current_user.id, payload.get("jti"))
    return MessageResponse(message="Logged out successfully.")


@router.post("/logout-all", response_model=MessageResponse)
async def logout_all(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Logout all sessions for the current user."""
    await logout_all_sessions(db, current_user.id)
    return MessageResponse(message="All sessions have been revoked.")


@router.get("/sessions", response_model=list[SessionResponse])
async def list_sessions(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all active sessions for the current user."""
    result = await db.execute(
        select(UserSession).where(
            UserSession.user_id == current_user.id,
            UserSession.is_active == True,
        ).order_by(UserSession.login_at.desc())
    )
    sessions = result.scalars().all()
    return [SessionResponse.model_validate(s) for s in sessions]


@router.delete("/sessions/{session_id}", response_model=MessageResponse)
async def revoke_session(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Revoke a specific session."""
    result = await db.execute(
        select(UserSession).where(
            UserSession.id == session_id,
            UserSession.user_id == current_user.id,
        )
    )
    session = result.scalar_one_or_none()
    if not session:
        from fastapi import HTTPException, status
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    session.is_active = False
    await db.commit()
    return MessageResponse(message="Session revoked.")


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    """Get current authenticated user info."""
    return UserResponse.model_validate(current_user)
