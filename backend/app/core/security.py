"""
JWT-based authentication and password hashing utilities.

Token lifecycle:
  1. Client POSTs credentials to /auth/token
  2. Server returns a signed JWT (HS256 by default)
  3. Client sends ``Authorization: Bearer <token>`` on subsequent requests
  4. ``verify_token`` validates the signature and expiry
"""

from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings

# ── Password hashing ─────────────────────────────────────────────────────────

_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(plain_password: str) -> str:
    """Return the bcrypt hash of *plain_password*."""
    return _pwd_context.hash(plain_password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Return ``True`` if *plain_password* matches *hashed_password*."""
    return _pwd_context.verify(plain_password, hashed_password)


# ── JWT ──────────────────────────────────────────────────────────────────────

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token")
"""FastAPI dependency that extracts the Bearer token from the Authorization header."""


def create_access_token(
    subject: str | int,
    expires_delta: timedelta | None = None,
    additional_claims: dict[str, Any] | None = None,
) -> str:
    """
    Create a signed JWT access token.

    Args:
        subject:          The token's ``sub`` claim (typically user ID or matricule).
        expires_delta:    Override for the default expiry window.
        additional_claims: Extra claims merged into the payload (e.g. ``{"role": "admin"}``).

    Returns:
        A signed JWT string.
    """
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    payload: dict[str, Any] = {
        "sub": str(subject),
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        **(additional_claims or {}),
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def verify_token(token: str) -> dict[str, Any]:
    """
    Decode and validate a JWT.

    Raises:
        jose.JWTError: if the token is invalid, expired, or tampered with.

    Returns:
        The decoded payload dictionary.
    """
    return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])


def decode_token_subject(token: str) -> str | None:
    """
    Safely extract the ``sub`` claim from *token*.

    Returns ``None`` instead of raising if the token is invalid.
    Useful in middleware where a hard failure is undesired.
    """
    try:
        payload = verify_token(token)
        return payload.get("sub")
    except JWTError:
        return None
