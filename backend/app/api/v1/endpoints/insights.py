"""
Insights endpoints — strategic workforce analytics.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.schemas.insights import InsightsResponse, LearningPath, OperationFragility
from app.services.insights import (
    compute_polyvalence_index,
    get_fragile_operations,
    get_full_insights,
    get_learning_paths,
)

router = APIRouter(prefix="/insights", tags=["Insights"])


@router.get("", response_model=InsightsResponse)
def get_all_insights(
    db: Session = Depends(get_db),
    _current_user: str = Depends(get_current_user),
) -> InsightsResponse:
    """
    Return the full insights dashboard payload in a single call.

    Aggregates fragile operations, learning paths, and the polyvalence index.
    This is what the frontend dashboard should use; more granular endpoints
    below are available for selective refreshes.
    """
    return get_full_insights(db)


@router.get("/fragilities", response_model=list[OperationFragility])
def get_fragilities(
    db: Session = Depends(get_db),
    _current_user: str = Depends(get_current_user),
) -> list[OperationFragility]:
    """
    List operations with dangerously few qualified operators.

    Sorted by risk level (CRITIQUE first) then by qualified operator count.
    """
    return get_fragile_operations(db)


@router.get("/learning-paths", response_model=list[LearningPath])
def get_learning_paths_endpoint(
    db: Session = Depends(get_db),
    _current_user: str = Depends(get_current_user),
) -> list[LearningPath]:
    """
    Recommend operator → operation training assignments based on skill adjacency.

    Identifies operators who are highly skilled on similar operations but
    haven't yet qualified on the target.
    """
    return get_learning_paths(db)


@router.get("/polyvalence")
def get_polyvalence(
    db: Session = Depends(get_db),
    _current_user: str = Depends(get_current_user),
) -> dict:
    """
    Return the workforce polyvalence index.

    A higher value indicates a more flexible, resilient workforce.
    """
    index = compute_polyvalence_index(db)
    return {"polyvalence_index": index}
