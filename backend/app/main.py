from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers.recommendations import router as recommendations_router

app = FastAPI(
    title="OPERATOR-QI API",
    description="Plateforme de matching opérateurs-missions",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(recommendations_router)


@app.get("/health", tags=["system"])
def health() -> dict:
    """Health check endpoint."""
    return {"status": "ok", "version": "0.1.0"}
