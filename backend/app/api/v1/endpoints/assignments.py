"""
Assignment endpoints.

Creating an assignment also updates (or creates) the SkillSnapshot for the
corresponding (operator, operation) pair so the matching engine always has
fresh data.
"""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.core.logging import audit_log
from app.models.assignment import Assignment
from app.models.skill import SkillSnapshot
from app.schemas.assignment import AssignmentCreate, AssignmentListResponse, AssignmentRead
from app.services.skill_decay import mastery_from_hours

router = APIRouter(prefix="/assignments", tags=["Assignments"])


def _update_skill_snapshot(
    db: Session,
    operator_id: int,
    operation_id: int,
    duration_hours: float,
    shift_date: object,
) -> None:
    """
    Increment the SkillSnapshot for (operator, operation) by *duration_hours*.

    Creates the snapshot if it does not yet exist.
    """
    snapshot = db.scalar(
        select(SkillSnapshot).where(
            SkillSnapshot.operator_id == operator_id,
            SkillSnapshot.operation_id == operation_id,
        )
    )
    # Represent the shift date as a UTC datetime for last_practice
    last_practice = datetime(
        shift_date.year, shift_date.month, shift_date.day, tzinfo=timezone.utc
    )

    if snapshot:
        snapshot.total_hours = (snapshot.total_hours or 0.0) + duration_hours
        snapshot.mastery_score = mastery_from_hours(snapshot.total_hours)
        # Only advance last_practice, never regress it
        if snapshot.last_practice is None or last_practice > snapshot.last_practice:
            snapshot.last_practice = last_practice
    else:
        total = duration_hours
        db.add(
            SkillSnapshot(
                operator_id=operator_id,
                operation_id=operation_id,
                mastery_score=mastery_from_hours(total),
                total_hours=total,
                last_practice=last_practice,
                decay_rate=90.0,
            )
        )


@router.get("", response_model=AssignmentListResponse)
def list_assignments(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    operator_id: int | None = Query(default=None),
    operation_id: int | None = Query(default=None),
    db: Session = Depends(get_db),
    _current_user: str = Depends(get_current_user),
) -> AssignmentListResponse:
    """List assignments with optional operator/operation filter."""
    query = select(Assignment)
    if operator_id is not None:
        query = query.where(Assignment.operator_id == operator_id)
    if operation_id is not None:
        query = query.where(Assignment.operation_id == operation_id)

    total = db.scalar(select(func.count()).select_from(query.subquery())) or 0
    skip = (page - 1) * page_size
    items = list(db.scalars(query.order_by(Assignment.shift_date.desc()).offset(skip).limit(page_size)).all())
    return AssignmentListResponse(
        total=total,
        page=page,
        page_size=page_size,
        items=[AssignmentRead.model_validate(a) for a in items],
    )


@router.post("", response_model=AssignmentRead, status_code=status.HTTP_201_CREATED)
def create_assignment(
    data: AssignmentCreate,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user),
) -> AssignmentRead:
    """
    Record an assignment and update the operator's skill snapshot.

    This is the primary data ingestion endpoint for live production data.
    """
    assignment = Assignment(**data.model_dump())
    db.add(assignment)

    # Update skill snapshot immediately so matching engine is always current
    _update_skill_snapshot(
        db,
        operator_id=data.operator_id,
        operation_id=data.operation_id,
        duration_hours=data.duration_hours,
        shift_date=data.shift_date,
    )

    db.commit()
    db.refresh(assignment)
    audit_log(
        user=current_user,
        action="CREATE_ASSIGNMENT",
        resource=f"assignment/{assignment.id}",
        extra={
            "operator_id": data.operator_id,
            "operation_id": data.operation_id,
            "hours": data.duration_hours,
        },
    )
    return AssignmentRead.model_validate(assignment)
