from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db import get_db
from app.models.assignment import Assignment
from app.models.base import new_uuid
from app.schemas.assignment import AssignmentCreate, AssignmentRead, AssignmentUpdate

router = APIRouter(prefix="/assignments", tags=["assignments"])


@router.get("", response_model=list[AssignmentRead])
def list_assignments(
    operator_id: str | None = None,
    operation_id: str | None = None,
    status: str | None = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
) -> list[Assignment]:
    q = db.query(Assignment)
    if operator_id:
        q = q.filter(Assignment.operator_id == operator_id)
    if operation_id:
        q = q.filter(Assignment.operation_id == operation_id)
    if status:
        q = q.filter(Assignment.status == status)
    return q.offset(skip).limit(limit).all()


@router.post("", response_model=AssignmentRead, status_code=status.HTTP_201_CREATED)
def create_assignment(payload: AssignmentCreate, db: Session = Depends(get_db)) -> Assignment:
    assignment = Assignment(id=new_uuid(), **payload.model_dump())
    db.add(assignment)
    db.commit()
    db.refresh(assignment)
    return assignment


@router.get("/{assignment_id}", response_model=AssignmentRead)
def get_assignment(assignment_id: str, db: Session = Depends(get_db)) -> Assignment:
    assignment = db.query(Assignment).filter(Assignment.id == assignment_id).first()
    if not assignment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Assignment not found."
        )
    return assignment


@router.patch("/{assignment_id}", response_model=AssignmentRead)
def update_assignment(
    assignment_id: str, payload: AssignmentUpdate, db: Session = Depends(get_db)
) -> Assignment:
    assignment = db.query(Assignment).filter(Assignment.id == assignment_id).first()
    if not assignment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Assignment not found."
        )
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(assignment, field, value)
    db.commit()
    db.refresh(assignment)
    return assignment


@router.delete("/{assignment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_assignment(assignment_id: str, db: Session = Depends(get_db)) -> None:
    assignment = db.query(Assignment).filter(Assignment.id == assignment_id).first()
    if not assignment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Assignment not found."
        )
    db.delete(assignment)
    db.commit()
