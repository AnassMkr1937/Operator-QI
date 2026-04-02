"""
Test configuration and fixtures.

Uses SQLite in-memory (well, file-based for session scope) database for
isolation from the production PostgreSQL instance.

The ``client`` fixture wires TestClient to the SQLite session via
FastAPI's dependency override mechanism so no real DB is required.
"""

import os

# Override DATABASE_URL BEFORE importing anything from app so the lazy
# engine factory picks up SQLite instead of PostgreSQL.
os.environ["DATABASE_URL"] = "sqlite:///./test.db"

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

from app.db.base_class import Base
from app.api.deps import get_db

# ── Import all models so Base.metadata is populated ─────────────────────────
import app.db.base  # noqa: F401

SQLALCHEMY_TEST_URL = "sqlite:///./test.db"


@pytest.fixture(scope="session")
def engine():
    """Create a SQLite engine and build the schema once per test session."""
    _engine = create_engine(
        SQLALCHEMY_TEST_URL,
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(bind=_engine)
    yield _engine
    Base.metadata.drop_all(bind=_engine)


@pytest.fixture
def db(engine):
    """
    Provide a transactional database session for a single test.

    Uses a nested SAVEPOINT so all changes from the test are rolled back
    regardless of commits inside the test code, giving full isolation.
    """
    connection = engine.connect()
    transaction = connection.begin()

    TestingSessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=connection,
    )
    session = TestingSessionLocal()

    # Patch session.commit() to use SAVEPOINT instead of real commit
    nested = connection.begin_nested()

    @event.listens_for(session, "after_transaction_end")
    def restart_savepoint(sess, trans):
        nonlocal nested
        if not nested.is_active:
            nested = connection.begin_nested()

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def client(db):
    """
    TestClient with the DB dependency overridden to use the test SQLite session.
    """
    # Import here to avoid circular imports at module level
    from app.main import app

    def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app, raise_server_exceptions=False) as c:
        yield c
    app.dependency_overrides.clear()


# ── Auth helper ──────────────────────────────────────────────────────────────

@pytest.fixture
def auth_headers() -> dict[str, str]:
    """Return Authorization headers with a valid admin JWT for test requests."""
    from app.core.security import create_access_token

    token = create_access_token(subject="admin_test")
    return {"Authorization": f"Bearer {token}"}
