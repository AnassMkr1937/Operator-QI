from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import Settings
from app.core.security import hash_password
from app.db.base import Base
from app.db.session import get_db
from app.main import create_app
from app.models.user import User, UserRole

TEST_DB_URL = "sqlite+pysqlite:///:memory:"

engine = create_engine(
    TEST_DB_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
)


@pytest.fixture
def client():
    settings = Settings(
        app_env="test",
        secret_key="test-secret",
        database_url=TEST_DB_URL,
        allowed_origins=["http://testserver"],
        rate_limit_enabled=False,
        auto_create_schema=False,
        admin_email="admin@example.com",
        admin_password="adminpass",
    )
    app = create_app(settings)
    app.state.engine = engine
    app.state.session_factory = TestingSessionLocal

    Base.metadata.create_all(bind=engine)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as client:
        yield client

    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db_session():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


def _make_user(db, email: str, password: str, role: UserRole) -> User:
    user = User(email=email, hashed_password=hash_password(password), role=role, is_active=True)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def manager_headers(client, db_session):
    _make_user(db_session, "manager@example.com", "managerpass", UserRole.manager)
    resp = client.post(
        "/api/v1/auth/login",
        json={"email": "manager@example.com", "password": "managerpass"},
    )
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def admin_headers(client, db_session):
    _make_user(db_session, "admin@example.com", "adminpass", UserRole.admin)
    resp = client.post(
        "/api/v1/auth/login",
        json={"email": "admin@example.com", "password": "adminpass"},
    )
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
