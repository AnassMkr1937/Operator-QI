from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi.middleware import SlowAPIMiddleware
from starlette.middleware.httpsredirect import HTTPSRedirectMiddleware

from app.core.config import Settings, get_settings
from app.core.rate_limit import limiter
from app.db.base import Base
from app.db.session import create_engine_from_settings, create_session_factory
from app.middleware.audit import AuditLogMiddleware
from app.routers import audit, auth, operators, recommendations
from app.services.auth import ensure_default_admin

APP_VERSION = "1.0.0"


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()

    engine = create_engine_from_settings(settings)
    session_factory = create_session_factory(engine)

    app = FastAPI(
        title="OPERATOR-QI API",
        description="Plateforme de matching opérateurs-missions",
        version=APP_VERSION,
    )

    if settings.https_only:
        app.add_middleware(HTTPSRedirectMiddleware)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    limiter.enabled = settings.rate_limit_enabled
    app.state.limiter = limiter
    if settings.rate_limit_enabled:
        app.add_middleware(SlowAPIMiddleware)

    app.state.engine = engine
    app.state.session_factory = session_factory

    app.add_middleware(AuditLogMiddleware, settings=settings)

    app.include_router(auth.router)
    app.include_router(recommendations.router)
    app.include_router(operators.router)
    app.include_router(audit.router)

    @app.on_event("startup")
    def startup() -> None:
        if settings.auto_create_schema:
            Base.metadata.create_all(bind=engine)
        if settings.app_env != "test":
            with session_factory() as db:
                ensure_default_admin(db)

    @app.get("/health", tags=["system"])
    def health() -> dict:
        """Health check endpoint."""
        return {"status": "ok", "version": APP_VERSION}

    return app


app = create_app()
