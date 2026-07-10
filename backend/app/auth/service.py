"""Auth business logic — register, login, password management, sessions."""

from datetime import datetime, timedelta, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from fastapi import HTTPException, status

from app.models.user import User, UserProfile
from app.models.session import UserSession, EmailVerification, PasswordReset, AuditLog
from app.auth.hashing import hash_password, verify_password
from app.auth.jwt import create_access_token, create_refresh_token, decode_token, create_verification_token
from app.auth.email import send_verification_email, send_password_reset_email
from app.schemas.auth import TokenResponse
from app.config import settings

# Constants
MAX_FAILED_ATTEMPTS = 5
LOCK_DURATION_MINUTES = 15
VERIFICATION_EXPIRY_HOURS = 24
RESET_EXPIRY_MINUTES = 15


async def register_user(
    db: AsyncSession,
    email: str,
    full_name: str,
    password: str,
) -> User:
    """Register a new user with email verification."""
    # Check if email exists
    existing = await db.execute(select(User).where(User.email == email))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

    # Create user
    user = User(
        email=email,
        full_name=full_name,
        hashed_password=hash_password(password),
        is_verified=True,  # Auto-verify to bypass email confirmation
    )
    db.add(user)
    await db.flush()  # Get the user ID

    # Create profile
    profile = UserProfile(user_id=user.id)
    db.add(profile)

    # Create verification token
    token = create_verification_token()
    verification = EmailVerification(
        user_id=user.id,
        token=token,
        expires_at=datetime.now(timezone.utc) + timedelta(hours=VERIFICATION_EXPIRY_HOURS),
    )
    db.add(verification)

    # Audit log
    db.add(AuditLog(user_id=user.id, action="register", resource_type="user", resource_id=user.id))

    await db.commit()
    await db.refresh(user)

    # Send verification email (prints to console in dev mode)
    await send_verification_email(email, token, full_name)

    return user


async def verify_email(db: AsyncSession, token: str) -> bool:
    """Verify a user's email address using the verification token."""
    result = await db.execute(
        select(EmailVerification).where(
            EmailVerification.token == token,
            EmailVerification.used == False,
        )
    )
    verification = result.scalar_one_or_none()

    if not verification:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid verification token")

    if verification.expires_at.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Verification token has expired")

    # Mark token as used
    verification.used = True

    # Activate user
    user_result = await db.execute(select(User).where(User.id == verification.user_id))
    user = user_result.scalar_one()
    user.is_verified = True

    # Audit
    db.add(AuditLog(user_id=user.id, action="verify_email", resource_type="user", resource_id=user.id))

    await db.commit()
    return True


async def login_user(
    db: AsyncSession,
    email: str,
    password: str,
    ip_address: str | None = None,
    user_agent: str | None = None,
) -> TokenResponse:
    """Authenticate user and return JWT tokens."""
    # Find user
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")

    # Check if locked
    if user.is_locked:
        if user.locked_until and user.locked_until.replace(tzinfo=timezone.utc) > datetime.now(timezone.utc):
            raise HTTPException(
                status_code=status.HTTP_423_LOCKED,
                detail=f"Account locked. Try again after {user.locked_until.strftime('%H:%M:%S')}",
            )
        else:
            # Unlock the account
            user.is_locked = False
            user.failed_login_attempts = 0
            user.locked_until = None

    # Verify password
    if not verify_password(password, user.hashed_password):
        user.failed_login_attempts += 1
        if user.failed_login_attempts >= MAX_FAILED_ATTEMPTS:
            user.is_locked = True
            user.locked_until = datetime.now(timezone.utc) + timedelta(minutes=LOCK_DURATION_MINUTES)
            db.add(AuditLog(user_id=user.id, action="account_locked", ip_address=ip_address))

        await db.commit()
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")

    # Check if verified
    if not user.is_verified:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Please verify your email first")

    # Reset failed attempts
    user.failed_login_attempts = 0
    user.is_locked = False
    user.locked_until = None

    # Create tokens
    import uuid
    jti = str(uuid.uuid4())
    access_token, _, access_expires = create_access_token(user.id, user.role, jti)
    refresh_token, _ = create_refresh_token(user.id, jti)

    # Parse user agent
    browser = "Unknown"
    os_name = "Unknown"
    if user_agent:
        if "Chrome" in user_agent:
            browser = "Chrome"
        elif "Firefox" in user_agent:
            browser = "Firefox"
        elif "Safari" in user_agent:
            browser = "Safari"
        if "Windows" in user_agent:
            os_name = "Windows"
        elif "Mac" in user_agent:
            os_name = "macOS"
        elif "Linux" in user_agent:
            os_name = "Linux"

    # Create session
    session = UserSession(
        user_id=user.id,
        jwt_jti=jti,
        device_name=f"{browser} on {os_name}",
        browser=browser,
        os=os_name,
        ip_address=ip_address,
    )
    db.add(session)

    # Audit
    db.add(AuditLog(user_id=user.id, action="login", ip_address=ip_address))

    await db.commit()

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


async def refresh_access_token(db: AsyncSession, refresh_token_str: str) -> TokenResponse:
    """Refresh an access token using a valid refresh token."""
    payload = decode_token(refresh_token_str)

    if not payload or payload.get("type") != "refresh":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    user_id = payload["sub"]
    old_jti = payload["jti"]

    # Verify session exists
    result = await db.execute(
        select(UserSession).where(UserSession.jwt_jti == old_jti, UserSession.is_active == True)
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Session not found or revoked")

    # Get user
    user_result = await db.execute(select(User).where(User.id == user_id))
    user = user_result.scalar_one_or_none()
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found or inactive")

    # Create new tokens with new JTI
    import uuid
    new_jti = str(uuid.uuid4())
    access_token, _, _ = create_access_token(user.id, user.role, new_jti)
    new_refresh, _ = create_refresh_token(user.id, new_jti)

    # Update session with new JTI
    session.jwt_jti = new_jti
    session.last_active_at = datetime.now(timezone.utc)

    await db.commit()

    return TokenResponse(
        access_token=access_token,
        refresh_token=new_refresh,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


async def logout_session(db: AsyncSession, user_id: str, jti: str | None = None) -> None:
    """Revoke a specific session or the current session."""
    if jti:
        await db.execute(
            update(UserSession)
            .where(UserSession.jwt_jti == jti, UserSession.user_id == user_id)
            .values(is_active=False)
        )
    await db.commit()


async def logout_all_sessions(db: AsyncSession, user_id: str) -> None:
    """Revoke all sessions for a user."""
    await db.execute(
        update(UserSession)
        .where(UserSession.user_id == user_id)
        .values(is_active=False)
    )
    db.add(AuditLog(user_id=user_id, action="logout_all"))
    await db.commit()


async def forgot_password(db: AsyncSession, email: str) -> None:
    """Send a password reset token. Always returns success (prevents email enumeration)."""
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()

    if not user:
        return  # Silent — don't reveal if email exists

    # Invalidate previous reset tokens
    prev_tokens = await db.execute(
        select(PasswordReset).where(PasswordReset.user_id == user.id, PasswordReset.used == False)
    )
    for t in prev_tokens.scalars():
        t.used = True

    # Create new token
    token = create_verification_token()
    reset = PasswordReset(
        user_id=user.id,
        token=token,
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=RESET_EXPIRY_MINUTES),
    )
    db.add(reset)
    db.add(AuditLog(user_id=user.id, action="forgot_password"))
    await db.commit()

    await send_password_reset_email(email, token, user.full_name)


async def reset_password(db: AsyncSession, token: str, new_password: str) -> None:
    """Reset password using a valid reset token."""
    result = await db.execute(
        select(PasswordReset).where(PasswordReset.token == token, PasswordReset.used == False)
    )
    reset = result.scalar_one_or_none()

    if not reset:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid reset token")

    if reset.expires_at.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Reset token has expired")

    reset.used = True

    user_result = await db.execute(select(User).where(User.id == reset.user_id))
    user = user_result.scalar_one()
    user.hashed_password = hash_password(new_password)

    # Invalidate all sessions (force re-login)
    await db.execute(
        update(UserSession).where(UserSession.user_id == user.id).values(is_active=False)
    )

    db.add(AuditLog(user_id=user.id, action="password_reset"))
    await db.commit()


async def change_password(db: AsyncSession, user: User, old_password: str, new_password: str) -> None:
    """Change password for authenticated user."""
    if not verify_password(old_password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Current password is incorrect")

    user.hashed_password = hash_password(new_password)
    db.add(AuditLog(user_id=user.id, action="change_password"))
    await db.commit()
