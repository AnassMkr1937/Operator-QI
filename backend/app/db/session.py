"""
Database session management.

Provides:
- ``get_engine``          — Lazy engine factory (creates once, reuses)
- ``get_session_factory`` — Lazy session factory
- ``get_db``              — FastAPI dependency that yields a scoped session
- ``check_db_connection`` — Startup health check

The engine and session factory are created lazily on first use so that
importing this module in test environments (which may use SQLite) does NOT
immediately attempt a PostgreSQL connection.
"""

from collections.abc import Generator

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings

# ── Lazy singletons ───────────────────────────────────────────────────────────
_engine: Engine | None = None
_SessionLocal: sessionmaker | None = None  # type: ignore[type-arg]


def get_engine() -> Engine:
    """Return (and lazily create) the shared SQLAlchemy engine."""
    global _engine
    if _engine is None:
        kwargs: dict = {
            "pool_pre_ping": True,
            "echo": settings.DEBUG,
        }
        # SQLite (used in tests) does not support pool_size / max_overflow
        if not settings.DATABASE_URL.startswith("sqlite"):
            kwargs["pool_size"] = 10
            kwargs["max_overflow"] = 20
        else:
            kwargs["connect_args"] = {"check_same_thread": False}
        _engine = create_engine(settings.DATABASE_URL, **kwargs)
    return _engine


def get_session_factory() -> sessionmaker:  # type: ignore[type-arg]
    """Return (and lazily create) the shared session factory."""
    global _SessionLocal
    if _SessionLocal is None:
        _SessionLocal = sessionmaker(
            bind=get_engine(),
            autocommit=False,
            autoflush=False,
            expire_on_commit=False,
        )
    return _SessionLocal


def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency that opens a DB session for the duration of one request.

    Usage::

        @router.get("/example")
        def example(db: Session = Depends(get_db)):
            ...

    The session is always closed in the ``finally`` block regardless of
    whether the request succeeds or raises.
    """
    db = get_session_factory()()
    try:
        yield db
    finally:
        db.close()


def check_db_connection() -> bool:
    """
    Verify the database is reachable.

    Called during application startup to fail fast if the DB is unavailable.
    Returns ``True`` on success, raises on failure.
    """
    with get_engine().connect() as conn:
        conn.execute(text("SELECT 1"))
    return True
