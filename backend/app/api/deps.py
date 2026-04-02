"""
FastAPI dependencies — reusable dependency-injection components.

Usage in endpoint handlers::

    @router.get("/me")
    def get_me(current_user: str = Depends(get_current_user)):
        ...
"""

from fastapi import Depends, HTTPException, status
from jose import JWTError
from sqlalchemy.orm import Session

from app.core.security import oauth2_scheme, verify_token
from app.db.session import get_db

# Re-export get_db so endpoint files only need to import from app.api.deps
__all__ = ["get_db", "get_current_user", "require_admin"]


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> str:
    """
    Validate the Bearer JWT and return the subject (user identifier).

    Raises HTTP 401 if the token is missing, expired, or invalid.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token invalide ou expiré",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = verify_token(token)
        subject: str | None = payload.get("sub")
        if subject is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    return subject


def require_admin(current_user: str = Depends(get_current_user)) -> str:
    """
    Restrict an endpoint to admin users.

    In the current implementation admins are identified by the ``admin`` prefix
    in their subject claim.  Replace with a role lookup in production.

    Raises HTTP 403 if the user is not an admin.
    """
    if not current_user.startswith("admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Accès réservé aux administrateurs",
        )
    return current_user
