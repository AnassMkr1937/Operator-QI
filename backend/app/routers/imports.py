from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.db import get_db
from app.services.csv_import import (
    ImportReport,
    import_assignments,
    import_operations,
    import_operators,
)

router = APIRouter(prefix="/import", tags=["import"])

MAX_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB


async def _read_upload(file: UploadFile) -> bytes:
    content = await file.read()
    if len(content) > MAX_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="File too large (max 10 MB).",
        )
    return content


@router.post("/operators", status_code=status.HTTP_200_OK)
async def import_operators_csv(
    file: UploadFile = File(..., description="CSV file with operators"),
    db: Session = Depends(get_db),
) -> dict:
    """Import operators from a CSV file.

    Required columns: employee_id, name
    Optional columns: email, department, hire_date, is_active
    """
    content = await _read_upload(file)
    report: ImportReport = import_operators(content, db)
    return report.to_dict()


@router.post("/operations", status_code=status.HTTP_200_OK)
async def import_operations_csv(
    file: UploadFile = File(..., description="CSV file with operations"),
    db: Session = Depends(get_db),
) -> dict:
    """Import operations from a CSV file.

    Required columns: code, name
    Optional columns: description, required_skills (pipe-separated), duration_minutes, is_active
    """
    content = await _read_upload(file)
    report: ImportReport = import_operations(content, db)
    return report.to_dict()


@router.post("/assignments", status_code=status.HTTP_200_OK)
async def import_assignments_csv(
    file: UploadFile = File(..., description="CSV file with assignments"),
    db: Session = Depends(get_db),
) -> dict:
    """Import assignments from a CSV file.

    Required columns: operator_employee_id, operation_code
    Optional columns: scheduled_date, status, notes
    """
    content = await _read_upload(file)
    report: ImportReport = import_assignments(content, db)
    return report.to_dict()
