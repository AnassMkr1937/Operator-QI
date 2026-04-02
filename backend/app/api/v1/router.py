"""
API v1 router — assembles all endpoint sub-routers under /api/v1.
"""

from fastapi import APIRouter

from app.api.v1.endpoints.assignments import router as assignments_router
from app.api.v1.endpoints.import_export import router as import_export_router
from app.api.v1.endpoints.insights import router as insights_router
from app.api.v1.endpoints.operations import router as operations_router
from app.api.v1.endpoints.operators import router as operators_router
from app.api.v1.endpoints.replacement import router as replacement_router

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(operators_router)
api_router.include_router(operations_router)
api_router.include_router(assignments_router)
api_router.include_router(replacement_router)
api_router.include_router(insights_router)
api_router.include_router(import_export_router)
