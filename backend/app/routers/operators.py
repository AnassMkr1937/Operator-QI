from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, selectinload

from app.db.session import get_db
from app.models.operator import Assignment, Operator, OperatorSkill
from app.models.skill import Skill
from app.schemas.operators import (
    OperatorCreate,
    OperatorListResponse,
    OperatorResponse,
    OperatorUpdate,
)
from app.services.auth import require_roles

router = APIRouter(prefix="/api/v1/operators", tags=["operators"])


def _upsert_skill(db: Session, skill_id: str) -> Skill:
    skill = db.get(Skill, skill_id)
    if skill:
        return skill
    skill = Skill(skill_id=skill_id)
    db.add(skill)
    return skill


def _replace_skills(db: Session, operator: Operator, skills: list) -> None:
    operator.skills.clear()
    for skill_payload in skills:
        _upsert_skill(db, skill_payload.skill_id)
        operator.skills.append(
            OperatorSkill(
                skill_id=skill_payload.skill_id,
                proficiency=skill_payload.proficiency,
                certified=skill_payload.certified,
                last_used_date=skill_payload.last_used_date,
            )
        )


def _replace_assignments(operator: Operator, assignments: list) -> None:
    operator.assignments.clear()
    for assignment in assignments:
        operator.assignments.append(
            Assignment(
                operation_id=assignment.operation_id,
                assignment_date=assignment.assignment_date,
                shift=assignment.shift,
                category=assignment.category,
            )
        )


@router.get(
    "/",
    response_model=OperatorListResponse,
    summary="List operators",
)
def list_operators(
    db: Session = Depends(get_db),
    _: Operator = Depends(require_roles("admin", "manager")),
) -> OperatorListResponse:
    operators = (
        db.query(Operator)
        .options(selectinload(Operator.skills), selectinload(Operator.assignments))
        .order_by(Operator.operator_id)
        .all()
    )
    return OperatorListResponse(items=operators, total=len(operators))


@router.get(
    "/{operator_id}",
    response_model=OperatorResponse,
    summary="Get operator by id",
)
def get_operator(
    operator_id: str,
    db: Session = Depends(get_db),
    _: Operator = Depends(require_roles("admin", "manager", "viewer")),
) -> OperatorResponse:
    operator = (
        db.query(Operator)
        .options(selectinload(Operator.skills), selectinload(Operator.assignments))
        .filter(Operator.operator_id == operator_id)
        .first()
    )
    if not operator:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Operator not found")
    return operator


@router.post(
    "/",
    response_model=OperatorResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create an operator",
)
def create_operator(
    payload: OperatorCreate,
    db: Session = Depends(get_db),
    _: Operator = Depends(require_roles("admin", "manager")),
) -> OperatorResponse:
    if db.get(Operator, payload.operator_id):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Operator already exists",
        )
    operator = Operator(
        operator_id=payload.operator_id,
        name=payload.name,
        is_active=payload.is_active,
    )
    _replace_skills(db, operator, payload.skills)
    _replace_assignments(operator, payload.assignments)
    db.add(operator)
    db.commit()
    db.refresh(operator)
    return operator


@router.put(
    "/{operator_id}",
    response_model=OperatorResponse,
    summary="Update an operator",
)
def update_operator(
    operator_id: str,
    payload: OperatorUpdate,
    db: Session = Depends(get_db),
    _: Operator = Depends(require_roles("admin", "manager")),
) -> OperatorResponse:
    operator = (
        db.query(Operator)
        .options(selectinload(Operator.skills), selectinload(Operator.assignments))
        .filter(Operator.operator_id == operator_id)
        .first()
    )
    if not operator:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Operator not found")
    if payload.name is not None:
        operator.name = payload.name
    if payload.is_active is not None:
        operator.is_active = payload.is_active
    if payload.skills is not None:
        _replace_skills(db, operator, payload.skills)
    if payload.assignments is not None:
        _replace_assignments(operator, payload.assignments)
    db.commit()
    db.refresh(operator)
    return operator


@router.delete(
    "/{operator_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete an operator",
)
def delete_operator(
    operator_id: str,
    db: Session = Depends(get_db),
    _: Operator = Depends(require_roles("admin")),
) -> None:
    operator = db.get(Operator, operator_id)
    if not operator:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Operator not found")
    db.delete(operator)
    db.commit()
