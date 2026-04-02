"""
Replacement engine endpoint.

🎯 Core business endpoint: given an operation, returns the ranked list of
operators best suited to perform it right now.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.schemas.replacement import ReplacementResponse
from app.services.matching import compute_replacements

router = APIRouter(tags=["Matching"])


@router.get("/replacement", response_model=ReplacementResponse)
def get_replacement_candidates(
    operation_id: int = Query(..., description="ID of the operation needing coverage"),
    shift: str = Query(
        default="all",
        description="Filter candidates by shift label, or 'all' for no filter",
    ),
    db: Session = Depends(get_db),
    _current_user: str = Depends(get_current_user),
) -> ReplacementResponse:
    """
    🎯 Core endpoint: Get ranked replacement candidates for an operation.

    Returns top candidates sorted by composite score with full explanations.
    Target: response in < 200ms.

    The composite score combines:
    - Base mastery (from training history)
    - Skill recency / decay factor
    - Quality penalty (defect history)
    - Adjacency bonus (transferable skills from similar operations)
    """
    try:
        result = compute_replacements(db, operation_id=operation_id, shift=shift)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    return result
