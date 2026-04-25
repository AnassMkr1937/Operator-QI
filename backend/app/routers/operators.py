from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db import get_db
from app.models.base import new_uuid
from app.models.operator import Operator
from app.schemas.operator import OperatorCreate, OperatorRead, OperatorUpdate

router = APIRouter(prefix="/operators", tags=["operators"])


@router.get("", response_model=list[OperatorRead])
def list_operators(
    skip: int = 0,
    limit: int = 100,
    active_only: bool = False,
    db: Session = Depends(get_db),
) -> list[Operator]:
    q = db.query(Operator)
    if active_only:
        q = q.filter(Operator.is_active)
    return q.offset(skip).limit(limit).all()


@router.post("", response_model=OperatorRead, status_code=status.HTTP_201_CREATED)
def create_operator(payload: OperatorCreate, db: Session = Depends(get_db)) -> Operator:
    existing = db.query(Operator).filter(Operator.employee_id == payload.employee_id).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Operator with employee_id '{payload.employee_id}' already exists.",
        )
    operator = Operator(id=new_uuid(), **payload.model_dump())
    db.add(operator)
    db.commit()
    db.refresh(operator)
    return operator


@router.get("/{operator_id}", response_model=OperatorRead)
def get_operator(operator_id: str, db: Session = Depends(get_db)) -> Operator:
    operator = db.query(Operator).filter(Operator.id == operator_id).first()
    if not operator:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Operator not found.")
    return operator


@router.patch("/{operator_id}", response_model=OperatorRead)
def update_operator(
    operator_id: str, payload: OperatorUpdate, db: Session = Depends(get_db)
) -> Operator:
    operator = db.query(Operator).filter(Operator.id == operator_id).first()
    if not operator:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Operator not found.")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(operator, field, value)
    db.commit()
    db.refresh(operator)
    return operator


@router.delete("/{operator_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_operator(operator_id: str, db: Session = Depends(get_db)) -> None:
    operator = db.query(Operator).filter(Operator.id == operator_id).first()
    if not operator:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Operator not found.")
    db.delete(operator)
    db.commit()
