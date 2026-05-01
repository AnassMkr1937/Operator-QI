from __future__ import annotations

from app.core.security import hash_password
from app.models.user import User, UserRole


def test_login_success(client, db_session) -> None:
    user = User(
        email="login@example.com",
        hashed_password=hash_password("goodpass"),
        role=UserRole.manager,
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()

    resp = client.post(
        "/api/v1/auth/login",
        json={"email": "login@example.com", "password": "goodpass"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert data["user"]["email"] == "login@example.com"


def test_login_invalid_password(client, db_session) -> None:
    user = User(
        email="login2@example.com",
        hashed_password=hash_password("goodpass"),
        role=UserRole.manager,
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()

    resp = client.post(
        "/api/v1/auth/login",
        json={"email": "login2@example.com", "password": "badpass"},
    )
    assert resp.status_code == 401


def test_me_requires_auth(client) -> None:
    resp = client.get("/api/v1/auth/me")
    assert resp.status_code == 403
