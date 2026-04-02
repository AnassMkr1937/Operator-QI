"""
Operation CRUD endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db, require_admin
from app.core.logging import audit_log
from app.models.operation import Operation
from app.schemas.operation import (
    OperationCreate,
    OperationListResponse,
    OperationRead,
    OperationUpdate,
)

router = APIRouter(prefix="/operations", tags=["Operations"])


@router.get("", response_model=OperationListResponse)
def list_operations(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    line: str | None = Query(default=None, description="Filter by production line"),
    criticality: int | None = Query(default=None, ge=1, le=5),
    db: Session = Depends(get_db),
    _current_user: str = Depends(get_current_user),
) -> OperationListResponse:
    """List operations with optional line/criticality filter."""
    query = select(Operation)
    if line:
        query = query.where(Operation.line == line)
    if criticality is not None:
        query = query.where(Operation.criticality == criticality)

    total = db.scalar(select(func.count()).select_from(query.subquery())) or 0
    skip = (page - 1) * page_size
    items = list(db.scalars(query.offset(skip).limit(page_size)).all())
    return OperationListResponse(
        total=total,
        page=page,
        page_size=page_size,
        items=[OperationRead.model_validate(op) for op in items],
    )


@router.get("/{operation_id}", response_model=OperationRead)
def get_operation(
    operation_id: int,
    db: Session = Depends(get_db),
    _current_user: str = Depends(get_current_user),
) -> OperationRead:
    """Retrieve a single operation by ID."""
    op = db.get(Operation, operation_id)
    if not op:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Opération {operation_id} introuvable",
        )
    return OperationRead.model_validate(op)


@router.post("", response_model=OperationRead, status_code=status.HTTP_201_CREATED)
def create_operation(
    data: OperationCreate,
    db: Session = Depends(get_db),
    current_user: str = Depends(require_admin),
) -> OperationRead:
    """Create a new operation (admin only)."""
    existing = db.scalar(select(Operation).where(Operation.code == data.code))
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Une opération avec le code {data.code!r} existe déjà",
        )
    op = Operation(**data.model_dump())
    db.add(op)
    db.commit()
    db.refresh(op)
    audit_log(
        user=current_user,
        action="CREATE_OPERATION",
        resource=f"operation/{op.id}",
        extra={"code": op.code},
    )
    return OperationRead.model_validate(op)


@router.put("/{operation_id}", response_model=OperationRead)
def update_operation(
    operation_id: int,
    data: OperationUpdate,
    db: Session = Depends(get_db),
    current_user: str = Depends(require_admin),
) -> OperationRead:
    """Partially update an operation record (admin only)."""
    op = db.get(Operation, operation_id)
    if not op:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Opération {operation_id} introuvable",
        )
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(op, field, value)
    db.commit()
    db.refresh(op)
    audit_log(user=current_user, action="UPDATE_OPERATION", resource=f"operation/{operation_id}")
    return OperationRead.model_validate(op)


@router.delete("/{operation_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_operation(
    operation_id: int,
    db: Session = Depends(get_db),
    current_user: str = Depends(require_admin),
) -> None:
    """Delete an operation (admin only)."""
    op = db.get(Operation, operation_id)
    if not op:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Opération {operation_id} introuvable",
        )
    db.delete(op)
    db.commit()
    audit_log(user=current_user, action="DELETE_OPERATION", resource=f"operation/{operation_id}")
