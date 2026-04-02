"""
Operator CRUD service.

All database interactions for the Operator domain go through this service layer
rather than being embedded in endpoint handlers. This keeps the API thin and
makes testing easier (inject a mock DB session).
"""

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.models.operator import Operator
from app.schemas.operator import OperatorCreate, OperatorUpdate

logger = get_logger(__name__)


def get(db: Session, operator_id: int) -> Operator | None:
    """Fetch a single operator by primary key. Returns ``None`` if not found."""
    return db.get(Operator, operator_id)


def get_by_matricule(db: Session, matricule: str) -> Operator | None:
    """Fetch a single operator by their anonymized matricule."""
    return db.scalar(select(Operator).where(Operator.matricule == matricule))


def get_multi(
    db: Session,
    *,
    skip: int = 0,
    limit: int = 50,
    team: str | None = None,
    shift: str | None = None,
    status: str | None = None,
) -> tuple[int, list[Operator]]:
    """
    Return a paginated list of operators with optional filters.

    Args:
        db:     SQLAlchemy session.
        skip:   Number of records to skip (offset).
        limit:  Maximum number of records to return.
        team:   Filter by team name (exact match).
        shift:  Filter by shift label (exact match).
        status: Filter by status (present / absent / conge).

    Returns:
        A tuple of (total_count, items) where total_count reflects the count
        *before* pagination so the client can compute page counts.
    """
    query = select(Operator)
    if team:
        query = query.where(Operator.team == team)
    if shift:
        query = query.where(Operator.shift == shift)
    if status:
        query = query.where(Operator.status == status)

    total = db.scalar(select(func.count()).select_from(query.subquery())) or 0
    items = list(db.scalars(query.offset(skip).limit(limit)).all())
    return total, items


def create(db: Session, *, data: OperatorCreate) -> Operator:
    """
    Create a new operator record.

    Raises:
        ValueError: if the matricule already exists.
    """
    if get_by_matricule(db, data.matricule):
        raise ValueError(f"Un opérateur avec le matricule {data.matricule!r} existe déjà")

    operator = Operator(**data.model_dump())
    db.add(operator)
    db.commit()
    db.refresh(operator)
    logger.info("operator.created", id=operator.id, matricule=operator.matricule)
    return operator


def update(db: Session, *, operator: Operator, data: OperatorUpdate) -> Operator:
    """
    Apply partial updates to an operator record.

    Only non-``None`` fields in *data* are written, preserving existing values
    for unspecified fields.
    """
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(operator, field, value)
    db.commit()
    db.refresh(operator)
    logger.info("operator.updated", id=operator.id, fields=list(update_data.keys()))
    return operator


def delete(db: Session, *, operator_id: int) -> bool:
    """
    Delete an operator by ID.

    Returns ``True`` if deleted, ``False`` if the operator was not found.
    Cascade rules on the DB ensure related assignments/skills are removed.
    """
    operator = get(db, operator_id)
    if not operator:
        return False
    db.delete(operator)
    db.commit()
    logger.info("operator.deleted", id=operator_id)
    return True
