from __future__ import annotations

import csv
import io
import logging
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

OPERATOR_REQUIRED_HEADERS = {"employee_id", "name"}
OPERATION_REQUIRED_HEADERS = {"code", "name"}
ASSIGNMENT_REQUIRED_HEADERS = {"operator_employee_id", "operation_code"}


@dataclass
class ImportReport:
    inserted: int = 0
    updated: int = 0
    errors: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "inserted": self.inserted,
            "updated": self.updated,
            "errors": self.errors,
            "total_errors": len(self.errors),
        }


def _parse_bool(value: str) -> bool:
    """Return False for common falsy string values, True otherwise."""
    return value.strip().lower() not in ("false", "0", "no")


def _serialize_skills(required_skills: list[str] | None) -> str | None:
    """Serialize a list of skill names to a JSON string for DB storage."""
    import json

    if required_skills is None:
        return None
    return json.dumps(required_skills)


def _deserialize_skills(raw: str | None) -> list[str] | None:
    """Deserialize a JSON string from DB to a list of skill names."""
    import json

    if raw is None:
        return None
    try:
        return json.loads(raw)
    except (ValueError, TypeError):
        return None


def _read_csv(content: bytes) -> tuple[list[str], list[dict]]:
    """Parse CSV bytes; return (headers, rows)."""
    text = content.decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(text))
    headers = list(reader.fieldnames or [])
    rows = list(reader)
    return headers, rows


def import_operators(content: bytes, db: Session) -> ImportReport:
    """Import operators from CSV content."""
    from app.models.base import new_uuid
    from app.models.operator import Operator

    report = ImportReport()
    try:
        headers, rows = _read_csv(content)
    except Exception:
        logger.exception("Could not parse operators CSV")
        report.errors.append("Could not parse CSV: invalid format or encoding.")
        return report

    missing = OPERATOR_REQUIRED_HEADERS - {h.lower().strip() for h in headers}
    if missing:
        report.errors.append(f"Missing required columns: {sorted(missing)}")
        return report

    for i, row in enumerate(rows, start=2):
        try:
            employee_id = row.get("employee_id", "").strip()
            name = row.get("name", "").strip()
            if not employee_id or not name:
                report.errors.append(f"Row {i}: 'employee_id' and 'name' are required.")
                continue

            existing = db.query(Operator).filter(Operator.employee_id == employee_id).first()
            if existing:
                existing.name = name
                existing.email = row.get("email", "").strip() or None
                existing.department = row.get("department", "").strip() or None
                existing.hire_date = row.get("hire_date", "").strip() or None
                existing.is_active = _parse_bool(row.get("is_active", "true"))
                report.updated += 1
            else:
                operator = Operator(
                    id=new_uuid(),
                    employee_id=employee_id,
                    name=name,
                    email=row.get("email", "").strip() or None,
                    department=row.get("department", "").strip() or None,
                    hire_date=row.get("hire_date", "").strip() or None,
                    is_active=_parse_bool(row.get("is_active", "true")),
                )
                db.add(operator)
                report.inserted += 1
        except Exception:
            logger.exception("Error processing operators CSV row %d", i)
            report.errors.append(f"Row {i}: could not process this row.")

    try:
        db.commit()
    except Exception:
        logger.exception("DB commit failed for operators import")
        db.rollback()
        report.errors.append("Import aborted: database error during commit.")

    return report


def import_operations(content: bytes, db: Session) -> ImportReport:
    """Import operations from CSV content."""
    from app.models.base import new_uuid
    from app.models.operation import Operation

    report = ImportReport()
    try:
        headers, rows = _read_csv(content)
    except Exception:
        logger.exception("Could not parse operations CSV")
        report.errors.append("Could not parse CSV: invalid format or encoding.")
        return report

    missing = OPERATION_REQUIRED_HEADERS - {h.lower().strip() for h in headers}
    if missing:
        report.errors.append(f"Missing required columns: {sorted(missing)}")
        return report

    for i, row in enumerate(rows, start=2):
        try:
            code = row.get("code", "").strip()
            name = row.get("name", "").strip()
            if not code or not name:
                report.errors.append(f"Row {i}: 'code' and 'name' are required.")
                continue

            raw_skills = row.get("required_skills", "").strip()
            skills_json: str | None = None
            if raw_skills:
                skills_list = [s.strip() for s in raw_skills.split("|") if s.strip()]
                skills_json = _serialize_skills(skills_list)

            duration_raw = row.get("duration_minutes", "").strip()
            duration = int(duration_raw) if duration_raw.isdigit() else None

            existing = db.query(Operation).filter(Operation.code == code).first()
            if existing:
                existing.name = name
                existing.description = row.get("description", "").strip() or None
                existing.required_skills = skills_json
                existing.duration_minutes = duration
                existing.is_active = _parse_bool(row.get("is_active", "true"))
                report.updated += 1
            else:
                op = Operation(
                    id=new_uuid(),
                    code=code,
                    name=name,
                    description=row.get("description", "").strip() or None,
                    required_skills=skills_json,
                    duration_minutes=duration,
                    is_active=_parse_bool(row.get("is_active", "true")),
                )
                db.add(op)
                report.inserted += 1
        except Exception:
            logger.exception("Error processing operations CSV row %d", i)
            report.errors.append(f"Row {i}: could not process this row.")

    try:
        db.commit()
    except Exception:
        logger.exception("DB commit failed for operations import")
        db.rollback()
        report.errors.append("Import aborted: database error during commit.")

    return report


def import_assignments(content: bytes, db: Session) -> ImportReport:
    """Import assignments from CSV content (lookup by employee_id and operation code)."""
    from app.models.assignment import Assignment
    from app.models.base import new_uuid
    from app.models.operation import Operation
    from app.models.operator import Operator

    report = ImportReport()
    try:
        headers, rows = _read_csv(content)
    except Exception:
        logger.exception("Could not parse assignments CSV")
        report.errors.append("Could not parse CSV: invalid format or encoding.")
        return report

    missing = ASSIGNMENT_REQUIRED_HEADERS - {h.lower().strip() for h in headers}
    if missing:
        report.errors.append(f"Missing required columns: {sorted(missing)}")
        return report

    for i, row in enumerate(rows, start=2):
        try:
            employee_id = row.get("operator_employee_id", "").strip()
            op_code = row.get("operation_code", "").strip()
            if not employee_id or not op_code:
                report.errors.append(
                    f"Row {i}: 'operator_employee_id' and 'operation_code' are required."
                )
                continue

            operator = db.query(Operator).filter(Operator.employee_id == employee_id).first()
            if not operator:
                report.errors.append(f"Row {i}: Operator '{employee_id}' not found.")
                continue

            operation = db.query(Operation).filter(Operation.code == op_code).first()
            if not operation:
                report.errors.append(f"Row {i}: Operation '{op_code}' not found.")
                continue

            assignment_status = row.get("status", "pending").strip() or "pending"
            scheduled_date = row.get("scheduled_date", "").strip() or None
            notes = row.get("notes", "").strip() or None

            assignment = Assignment(
                id=new_uuid(),
                operator_id=operator.id,
                operation_id=operation.id,
                scheduled_date=scheduled_date,
                status=assignment_status,
                notes=notes,
            )
            db.add(assignment)
            report.inserted += 1
        except Exception:
            logger.exception("Error processing assignments CSV row %d", i)
            report.errors.append(f"Row {i}: could not process this row.")

    try:
        db.commit()
    except Exception:
        logger.exception("DB commit failed for assignments import")
        db.rollback()
        report.errors.append("Import aborted: database error during commit.")

    return report
