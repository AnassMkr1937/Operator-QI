from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.rate_limit import limiter
from app.db.session import get_db
from app.schemas.auth import LoginRequest, TokenResponse, UserPublic
from app.services.auth import authenticate_user, get_current_user, issue_token

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Authenticate and receive a JWT token",
)
@limiter.limit("10/minute")
def login(body: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    user = authenticate_user(db, email=body.email, password=body.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )
    token = issue_token(user)
    settings = get_settings()
    return TokenResponse(
        access_token=token,
        expires_in=settings.access_token_expire_minutes * 60,
        user=UserPublic(id=user.id, email=user.email, role=user.role.value),
    )


@router.get("/me", response_model=UserPublic, summary="Get current user profile")
def me(user=Depends(get_current_user)) -> UserPublic:
    return UserPublic(id=user.id, email=user.email, role=user.role.value)
