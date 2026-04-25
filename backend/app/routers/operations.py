from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db import get_db
from app.models.base import new_uuid
from app.models.operation import Operation
from app.schemas.operation import OperationCreate, OperationRead, OperationUpdate
from app.services.csv_import import _deserialize_skills, _serialize_skills

router = APIRouter(prefix="/operations", tags=["operations"])


def _to_read(op: Operation) -> OperationRead:
    return OperationRead(
        id=op.id,
        code=op.code,
        name=op.name,
        description=op.description,
        required_skills=_deserialize_skills(op.required_skills),
        duration_minutes=op.duration_minutes,
        is_active=op.is_active,
        created_at=op.created_at,
        updated_at=op.updated_at,
    )


@router.get("", response_model=list[OperationRead])
def list_operations(
    skip: int = 0,
    limit: int = 100,
    active_only: bool = False,
    db: Session = Depends(get_db),
) -> list[OperationRead]:
    q = db.query(Operation)
    if active_only:
        q = q.filter(Operation.is_active)
    return [_to_read(o) for o in q.offset(skip).limit(limit).all()]


@router.post("", response_model=OperationRead, status_code=status.HTTP_201_CREATED)
def create_operation(payload: OperationCreate, db: Session = Depends(get_db)) -> OperationRead:
    existing = db.query(Operation).filter(Operation.code == payload.code).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Operation with code '{payload.code}' already exists.",
        )
    data = payload.model_dump()
    data["required_skills"] = _serialize_skills(data["required_skills"])
    op = Operation(id=new_uuid(), **data)
    db.add(op)
    db.commit()
    db.refresh(op)
    return _to_read(op)


@router.get("/{operation_id}", response_model=OperationRead)
def get_operation(operation_id: str, db: Session = Depends(get_db)) -> OperationRead:
    op = db.query(Operation).filter(Operation.id == operation_id).first()
    if not op:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Operation not found.")
    return _to_read(op)


@router.patch("/{operation_id}", response_model=OperationRead)
def update_operation(
    operation_id: str, payload: OperationUpdate, db: Session = Depends(get_db)
) -> OperationRead:
    op = db.query(Operation).filter(Operation.id == operation_id).first()
    if not op:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Operation not found.")
    update_data = payload.model_dump(exclude_unset=True)
    if "required_skills" in update_data:
        update_data["required_skills"] = _serialize_skills(update_data["required_skills"])
    for field, value in update_data.items():
        setattr(op, field, value)
    db.commit()
    db.refresh(op)
    return _to_read(op)


@router.delete("/{operation_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_operation(operation_id: str, db: Session = Depends(get_db)) -> None:
    op = db.query(Operation).filter(Operation.id == operation_id).first()
    if not op:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Operation not found.")
    db.delete(op)
    db.commit()
