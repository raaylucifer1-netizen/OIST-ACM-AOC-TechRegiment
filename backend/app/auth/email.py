"""Email service — console mode for local dev (prints to terminal)."""

from app.config import settings


async def send_verification_email(email: str, token: str, full_name: str) -> None:
    """Send email verification link. In console mode, prints to terminal."""
    verification_url = f"http://localhost:3000/verify-email?token={token}"

    if settings.EMAIL_MODE == "console":
        print("\n" + "=" * 60)
        print("📧 EMAIL VERIFICATION")
        print("=" * 60)
        print(f"To: {email}")
        print(f"Name: {full_name}")
        print(f"Verification URL: {verification_url}")
        print(f"Token: {token}")
        print("=" * 60 + "\n")
    else:
        # Future: SMTP implementation
        pass


async def send_password_reset_email(email: str, token: str, full_name: str) -> None:
    """Send password reset link. In console mode, prints to terminal."""
    reset_url = f"http://localhost:3000/reset-password?token={token}"

    if settings.EMAIL_MODE == "console":
        print("\n" + "=" * 60)
        print("🔑 PASSWORD RESET")
        print("=" * 60)
        print(f"To: {email}")
        print(f"Name: {full_name}")
        print(f"Reset URL: {reset_url}")
        print(f"Token: {token}")
        print(f"Expires in: 15 minutes")
        print("=" * 60 + "\n")
    else:
        # Future: SMTP implementation
        pass
