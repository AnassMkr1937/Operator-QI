from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.audit import AuditLog
from app.schemas.audit import AuditLogListResponse
from app.services.auth import require_roles

router = APIRouter(prefix="/api/v1/audit", tags=["audit"])


@router.get(
    "/logs",
    response_model=AuditLogListResponse,
    summary="List audit logs",
)
def list_audit_logs(
    db: Session = Depends(get_db),
    _: object = Depends(require_roles("admin")),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
) -> AuditLogListResponse:
    total = db.query(AuditLog).count()
    items = (
        db.query(AuditLog)
        .order_by(AuditLog.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    return AuditLogListResponse(items=items, total=total)
