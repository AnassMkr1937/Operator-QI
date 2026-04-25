from app.routers.assignments import router as assignments_router
from app.routers.imports import router as imports_router
from app.routers.operations import router as operations_router
from app.routers.operators import router as operators_router
from app.routers.skills import router as skills_router

__all__ = [
    "operators_router",
    "operations_router",
    "skills_router",
    "assignments_router",
    "imports_router",
]
