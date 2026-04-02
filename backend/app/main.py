"""
OPERATOR IQ — FastAPI Application Entry Point

Initializes the application with:
- CORS middleware (configurable origins)
- Audit logging middleware
- Security headers middleware
- API v1 router
- Lifespan events (DB connection check on startup)
- Custom exception handlers
- Health check endpoint
"""

from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.logging import get_logger
from app.db.session import check_db_connection
from app.middleware.audit import AuditMiddleware
from app.middleware.security_headers import SecurityHeadersMiddleware

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):  # type: ignore[type-arg]
    """
    Application lifespan handler.

    Startup:
    - Verify the database is reachable (fail fast rather than serving 500s)

    Shutdown:
    - Log graceful shutdown
    """
    logger.info("operator_iq.startup", version=settings.APP_VERSION, debug=settings.DEBUG)
    try:
        check_db_connection()
        logger.info("operator_iq.db_connected")
    except Exception as exc:  # noqa: BLE001
        # Log the problem but don't crash — allows running without a DB in test mode
        logger.warning("operator_iq.db_unavailable", error=str(exc))
    yield
    logger.info("operator_iq.shutdown")


# ── Application factory ───────────────────────────────────────────────────────

app = FastAPI(
    title="Operator IQ API",
    version=settings.APP_VERSION,
    description=(
        "## Operator IQ\n\n"
        "Industrial operator skill management system for Renault / Stellantis.\n\n"
        "### Core features\n"
        "- **Replacement engine**: rank operators by composite compatibility score\n"
        "- **Skill decay model**: exponential mastery decay based on last practice date\n"
        "- **Insights**: fragile operation detection and learning path recommendations\n"
        "- **CSV import**: bulk data ingestion from MES exports\n"
    ),
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# ── Middleware (order matters — outermost runs first) ─────────────────────────

# Security headers on every response
app.add_middleware(SecurityHeadersMiddleware)

# Audit logging (runs before CORS so we capture all requests)
app.add_middleware(AuditMiddleware)

# CORS — restrict to known origins in production
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.DEBUG else ["https://operatoriq.renault.internal"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ──────────────────────────────────────────────────────────────────

app.include_router(api_router)


# ── Exception handlers ────────────────────────────────────────────────────────


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Catch-all exception handler that prevents internal stack traces from leaking
    to API clients in production.
    """
    logger.error(
        "unhandled_exception",
        path=request.url.path,
        error=str(exc),
        exc_info=True,
    )
    message = str(exc) if settings.DEBUG else "Une erreur interne est survenue"
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": message},
    )


# ── Health check ─────────────────────────────────────────────────────────────


@app.get("/health", tags=["Health"], include_in_schema=False)
def health_check() -> dict[str, Any]:
    """
    Lightweight liveness probe for load balancers and container orchestrators.

    Returns 200 OK if the application process is running.
    Does NOT verify database connectivity (use /health/ready for that).
    """
    return {
        "status": "ok",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
    }


@app.get("/health/ready", tags=["Health"], include_in_schema=False)
def readiness_check() -> dict[str, Any]:
    """
    Readiness probe that verifies database connectivity.

    Returns 200 if the DB is reachable, 503 otherwise.
    Used by Kubernetes readinessProbe to prevent routing traffic to a pod
    that has lost its DB connection.
    """
    try:
        check_db_connection()
        return {"status": "ready", "database": "connected"}
    except Exception as exc:  # noqa: BLE001
        return JSONResponse(  # type: ignore[return-value]
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"status": "not_ready", "database": "unreachable", "error": str(exc)},
        )
