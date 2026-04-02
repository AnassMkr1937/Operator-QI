"""
Import / Export endpoints.

- POST /import/csv      — multipart file upload (CSV)
- POST /import/bulk     — JSON body import
- GET  /export/operators — CSV export of all operators
- GET  /export/skills    — CSV export of skill snapshots with effective mastery
"""

import io

import pandas as pd
from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db, require_admin
from app.core.logging import audit_log, get_logger
from app.models.operator import Operator
from app.models.skill import SkillSnapshot
from app.services.import_csv import (
    import_assignments,
    import_operation_similarities,
    import_operations,
    import_operators,
    import_quality_metrics,
)
from app.services.skill_decay import compute_recency_factor

logger = get_logger(__name__)

router = APIRouter(tags=["Import / Export"])

# Mapping from CSV type discriminator to the import function
_IMPORT_HANDLERS = {
    "operators": import_operators,
    "operations": import_operations,
    "assignments": import_assignments,
    "quality_metrics": import_quality_metrics,
    "operation_similarities": import_operation_similarities,
}


@router.post("/import/csv", status_code=status.HTTP_200_OK)
async def import_csv(
    csv_type: str = Query(
        ...,
        description="Type of data: operators | operations | assignments | "
        "quality_metrics | operation_similarities",
    ),
    file: UploadFile = File(..., description="CSV file to import"),
    db: Session = Depends(get_db),
    current_user: str = Depends(require_admin),
) -> dict:
    """
    Upload and import a CSV file.

    The ``csv_type`` query parameter tells the engine how to parse the file.
    On validation errors the import is rolled back and the errors are returned
    — no partial data is ever committed.
    """
    handler = _IMPORT_HANDLERS.get(csv_type)
    if handler is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Type CSV inconnu: {csv_type!r}. "
            f"Valeurs acceptées: {list(_IMPORT_HANDLERS)}",
        )

    content = await file.read()
    result = handler(db, content)

    audit_log(
        user=current_user,
        action="IMPORT_CSV",
        resource=f"import/{csv_type}",
        extra={"filename": file.filename, **result},
    )
    if result.get("errors"):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"message": "Erreurs d'import", "errors": result["errors"]},
        )
    return result


@router.post("/import/bulk", status_code=status.HTTP_200_OK)
def import_bulk_json(
    payload: dict,
    db: Session = Depends(get_db),
    current_user: str = Depends(require_admin),
) -> dict:
    """
    Import data via JSON body.

    Expected payload::

        {
            "operators": [...],
            "operations": [...],
            "assignments": [...],
            "quality_metrics": [...]
        }

    Each list item must match the corresponding CSV column names.
    """
    results: dict[str, dict] = {}
    for key, handler in _IMPORT_HANDLERS.items():
        rows = payload.get(key)
        if not rows:
            continue
        # Convert list of dicts to CSV bytes
        csv_bytes = pd.DataFrame(rows).to_csv(index=False).encode()
        results[key] = handler(db, csv_bytes)

    audit_log(
        user=current_user,
        action="IMPORT_BULK_JSON",
        resource="import/bulk",
        extra={"keys": list(results.keys())},
    )
    return results


@router.get("/export/operators")
def export_operators(
    db: Session = Depends(get_db),
    _current_user: str = Depends(get_current_user),
) -> StreamingResponse:
    """
    Export all operators as a UTF-8 CSV file.

    The exported file can be re-imported via POST /import/csv?csv_type=operators.
    """
    operators = list(db.scalars(select(Operator)).all())
    rows = [
        {
            "matricule": op.matricule,
            "full_name": op.full_name,
            "team": op.team,
            "shift": op.shift,
            "status": op.status,
        }
        for op in operators
    ]
    df = pd.DataFrame(rows)
    output = io.StringIO()
    df.to_csv(output, index=False)
    output.seek(0)
    return StreamingResponse(
        iter([output.read()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=operators_export.csv"},
    )


@router.get("/export/skills")
def export_skills(
    db: Session = Depends(get_db),
    _current_user: str = Depends(get_current_user),
) -> StreamingResponse:
    """
    Export skill snapshots with effective (decay-adjusted) mastery as CSV.

    Includes the raw mastery, the recency factor, and the effective mastery
    so downstream tools can perform their own analyses.
    """
    snapshots = list(db.scalars(select(SkillSnapshot)).all())
    rows = []
    for snap in snapshots:
        operator = db.get(Operator, snap.operator_id)
        if not operator:
            continue
        if snap.last_practice:
            recency = compute_recency_factor(snap.last_practice, snap.decay_rate or 90.0)
            effective = round(snap.mastery_score * recency, 2)
        else:
            recency = 0.0
            effective = 0.0
        rows.append(
            {
                "operator_id": snap.operator_id,
                "matricule": operator.matricule,
                "operation_id": snap.operation_id,
                "mastery_score": snap.mastery_score,
                "recency_factor": round(recency, 4),
                "effective_mastery": effective,
                "total_hours": snap.total_hours,
                "last_practice": snap.last_practice.isoformat() if snap.last_practice else "",
            }
        )
    df = pd.DataFrame(rows)
    output = io.StringIO()
    df.to_csv(output, index=False)
    output.seek(0)
    return StreamingResponse(
        iter([output.read()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=skills_export.csv"},
    )
