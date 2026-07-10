"""Argon2id password hashing — memory-hard and side-channel resistant."""

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError, InvalidHashError

_hasher = PasswordHasher(
    time_cost=3,       # iterations
    memory_cost=65536,  # 64MB
    parallelism=4,
    hash_len=32,
    salt_len=16,
)


def hash_password(password: str) -> str:
    """Hash a password using Argon2id."""
    return _hasher.hash(password)


def verify_password(password: str, hashed: str) -> bool:
    """Verify a password against an Argon2id hash."""
    try:
        return _hasher.verify(hashed, password)
    except (VerifyMismatchError, InvalidHashError):
        return False


def needs_rehash(hashed: str) -> bool:
    """Check if a hash needs to be updated to current parameters."""
    return _hasher.check_needs_rehash(hashed)
