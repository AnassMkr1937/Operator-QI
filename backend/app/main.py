from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.routers import (
    assignments_router,
    imports_router,
    operations_router,
    operators_router,
    skills_router,
)

settings = get_settings()

app = FastAPI(
    title="OPERATOR-QI API",
    description="Plateforme de matching opérateurs-missions",
    version=settings.version,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

API_PREFIX = "/api/v1"

app.include_router(operators_router, prefix=API_PREFIX)
app.include_router(operations_router, prefix=API_PREFIX)
app.include_router(skills_router, prefix=API_PREFIX)
app.include_router(assignments_router, prefix=API_PREFIX)
app.include_router(imports_router, prefix=API_PREFIX)


@app.get("/health", tags=["system"])
def health() -> dict:
    """Health check endpoint."""
    return {"status": "ok", "version": settings.version}


@app.get("/readiness", tags=["system"])
def readiness() -> dict:
    """Readiness probe — verifies DB connection."""
    from sqlalchemy import text

    from app.db import engine

    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return {"status": "ready"}
    except Exception as exc:
        from fastapi import HTTPException, status

        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Database not reachable: {exc}",
        ) from exc
