"""
Operator CRUD endpoints.

All endpoints require a valid Bearer token.  Write operations (POST, PUT, DELETE)
additionally enforce the ``require_admin`` dependency.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db, require_admin
from app.core.logging import audit_log
from app.schemas.operator import (
    OperatorCreate,
    OperatorListResponse,
    OperatorRead,
    OperatorUpdate,
)
from app.services import operator_service

router = APIRouter(prefix="/operators", tags=["Operators"])


@router.get("", response_model=OperatorListResponse)
def list_operators(
    page: int = Query(default=1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(default=20, ge=1, le=100),
    team: str | None = Query(default=None),
    shift: str | None = Query(default=None),
    status: str | None = Query(default=None),
    db: Session = Depends(get_db),
    _current_user: str = Depends(get_current_user),
) -> OperatorListResponse:
    """
    List operators with optional filtering by team, shift, and status.

    Returns a paginated result with total count for UI pagination.
    """
    skip = (page - 1) * page_size
    total, items = operator_service.get_multi(
        db, skip=skip, limit=page_size, team=team, shift=shift, status=status
    )
    return OperatorListResponse(
        total=total,
        page=page,
        page_size=page_size,
        items=[OperatorRead.model_validate(op) for op in items],
    )


@router.get("/{operator_id}", response_model=OperatorRead)
def get_operator(
    operator_id: int,
    db: Session = Depends(get_db),
    _current_user: str = Depends(get_current_user),
) -> OperatorRead:
    """Retrieve a single operator by ID."""
    operator = operator_service.get(db, operator_id)
    if not operator:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Opérateur {operator_id} introuvable",
        )
    return OperatorRead.model_validate(operator)


@router.post("", response_model=OperatorRead, status_code=status.HTTP_201_CREATED)
def create_operator(
    data: OperatorCreate,
    db: Session = Depends(get_db),
    current_user: str = Depends(require_admin),
) -> OperatorRead:
    """Create a new operator (admin only)."""
    try:
        operator = operator_service.create(db, data=data)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))
    audit_log(
        user=current_user,
        action="CREATE_OPERATOR",
        resource=f"operator/{operator.id}",
        extra={"matricule": operator.matricule},
    )
    return OperatorRead.model_validate(operator)


@router.put("/{operator_id}", response_model=OperatorRead)
def update_operator(
    operator_id: int,
    data: OperatorUpdate,
    db: Session = Depends(get_db),
    current_user: str = Depends(require_admin),
) -> OperatorRead:
    """Partially update an operator record (admin only)."""
    operator = operator_service.get(db, operator_id)
    if not operator:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Opérateur {operator_id} introuvable",
        )
    operator = operator_service.update(db, operator=operator, data=data)
    audit_log(
        user=current_user,
        action="UPDATE_OPERATOR",
        resource=f"operator/{operator_id}",
    )
    return OperatorRead.model_validate(operator)


@router.delete("/{operator_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_operator(
    operator_id: int,
    db: Session = Depends(get_db),
    current_user: str = Depends(require_admin),
) -> None:
    """Delete an operator and all their related records (admin only)."""
    deleted = operator_service.delete(db, operator_id=operator_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Opérateur {operator_id} introuvable",
        )
    audit_log(
        user=current_user,
        action="DELETE_OPERATOR",
        resource=f"operator/{operator_id}",
    )
