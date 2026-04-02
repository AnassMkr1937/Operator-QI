"""
CSV import pipeline with validation, rollback on error, and update support.

Supports importing:
- operators.csv        (matricule, full_name, team, shift, status)
- operations.csv       (code, name, line, criticality, nominal_cycle_time_s)
- assignments.csv      (matricule, operation_code, shift_date, duration_hours, shift_label)
- quality_metrics.csv  (matricule, operation_code, defects_per_100, pieces_produced,
                         period_start, period_end)
- operation_similarities.csv (operation_code_a, operation_code_b, similarity)

All imports are transactional — any validation error causes a full rollback
and returns the error list without committing partial data.
"""

from __future__ import annotations

import io
from datetime import date, datetime, timezone
from typing import Any

import pandas as pd
from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.models.assignment import Assignment
from app.models.operation import Operation
from app.models.operator import Operator
from app.models.quality import QualityMetric
from app.models.skill import OperationSimilarity, SkillSnapshot
from app.services.skill_decay import mastery_from_hours

logger = get_logger(__name__)


# ── Helpers ──────────────────────────────────────────────────────────────────


def _read_csv(source: str | io.IOBase | bytes) -> pd.DataFrame:
    """Read CSV from a file path, file-like object, or raw bytes."""
    if isinstance(source, bytes):
        source = io.BytesIO(source)
    return pd.read_csv(source, dtype=str, keep_default_na=False)


def _validate_columns(df: pd.DataFrame, required: list[str], context: str) -> list[str]:
    """Return a list of error messages if required columns are missing."""
    missing = [c for c in required if c not in df.columns]
    if missing:
        return [f"[{context}] Colonnes manquantes : {missing}"]
    return []


def _parse_date(val: str) -> date:
    """Parse an ISO date string (YYYY-MM-DD) into a :class:`datetime.date`."""
    return datetime.strptime(val.strip(), "%Y-%m-%d").date()


# ── Public import functions ──────────────────────────────────────────────────


def import_operators(db: Session, source: str | io.IOBase | bytes) -> dict[str, Any]:
    """
    Import operators from CSV. Upserts on ``matricule``.

    Expected columns: matricule, full_name, team, shift, status (optional)

    Returns a summary dict with keys: created, updated, errors.
    """
    df = _read_csv(source)
    errors = _validate_columns(df, ["matricule", "full_name", "team", "shift"], "operators")
    if errors:
        return {"created": 0, "updated": 0, "errors": errors}

    created = updated = 0
    row_errors: list[str] = []

    for idx, row in df.iterrows():
        try:
            matricule = row["matricule"].strip()
            if not matricule:
                row_errors.append(f"Row {idx}: matricule vide")
                continue

            existing = db.query(Operator).filter(Operator.matricule == matricule).first()
            if existing:
                existing.full_name = row["full_name"].strip()
                existing.team = row["team"].strip()
                existing.shift = row["shift"].strip()
                if "status" in row and row["status"].strip():
                    existing.status = row["status"].strip()
                updated += 1
            else:
                op = Operator(
                    matricule=matricule,
                    full_name=row["full_name"].strip(),
                    team=row["team"].strip(),
                    shift=row["shift"].strip(),
                    status=row.get("status", "present").strip() or "present",
                )
                db.add(op)
                created += 1
        except Exception as exc:  # noqa: BLE001
            row_errors.append(f"Row {idx}: {exc}")

    if row_errors:
        db.rollback()
        logger.warning("import_operators.errors", count=len(row_errors))
        return {"created": 0, "updated": 0, "errors": row_errors}

    db.commit()
    logger.info("import_operators.done", created=created, updated=updated)
    return {"created": created, "updated": updated, "errors": []}


def import_operations(db: Session, source: str | io.IOBase | bytes) -> dict[str, Any]:
    """
    Import operations from CSV. Upserts on ``code``.

    Expected columns: code, name, line, criticality (optional), nominal_cycle_time_s (optional)
    """
    df = _read_csv(source)
    errors = _validate_columns(df, ["code", "name", "line"], "operations")
    if errors:
        return {"created": 0, "updated": 0, "errors": errors}

    created = updated = 0
    row_errors: list[str] = []

    for idx, row in df.iterrows():
        try:
            code = row["code"].strip()
            if not code:
                row_errors.append(f"Row {idx}: code vide")
                continue

            existing = db.query(Operation).filter(Operation.code == code).first()
            criticality = int(row["criticality"]) if row.get("criticality", "").strip() else 3
            cycle_time = (
                float(row["nominal_cycle_time_s"])
                if row.get("nominal_cycle_time_s", "").strip()
                else None
            )

            if existing:
                existing.name = row["name"].strip()
                existing.line = row["line"].strip()
                existing.criticality = criticality
                existing.nominal_cycle_time_s = cycle_time
                updated += 1
            else:
                op = Operation(
                    code=code,
                    name=row["name"].strip(),
                    line=row["line"].strip(),
                    criticality=criticality,
                    nominal_cycle_time_s=cycle_time,
                )
                db.add(op)
                created += 1
        except Exception as exc:  # noqa: BLE001
            row_errors.append(f"Row {idx}: {exc}")

    if row_errors:
        db.rollback()
        return {"created": 0, "updated": 0, "errors": row_errors}

    db.commit()
    logger.info("import_operations.done", created=created, updated=updated)
    return {"created": created, "updated": updated, "errors": []}


def import_assignments(db: Session, source: str | io.IOBase | bytes) -> dict[str, Any]:
    """
    Import historical assignments from CSV and recalculate SkillSnapshots.

    Expected columns: matricule, operation_code, shift_date, duration_hours,
                      shift_label (optional), notes (optional)
    """
    df = _read_csv(source)
    errors = _validate_columns(
        df, ["matricule", "operation_code", "shift_date", "duration_hours"], "assignments"
    )
    if errors:
        return {"created": 0, "errors": errors}

    created = 0
    row_errors: list[str] = []

    for idx, row in df.iterrows():
        try:
            operator = (
                db.query(Operator).filter(Operator.matricule == row["matricule"].strip()).first()
            )
            if not operator:
                row_errors.append(f"Row {idx}: opérateur {row['matricule']!r} introuvable")
                continue

            operation = (
                db.query(Operation)
                .filter(Operation.code == row["operation_code"].strip())
                .first()
            )
            if not operation:
                row_errors.append(
                    f"Row {idx}: opération {row['operation_code']!r} introuvable"
                )
                continue

            shift_date = _parse_date(row["shift_date"])
            duration = float(row["duration_hours"])

            assignment = Assignment(
                operator_id=operator.id,
                operation_id=operation.id,
                shift_date=shift_date,
                duration_hours=duration,
                shift_label=row.get("shift_label", "").strip() or None,
                notes=row.get("notes", "").strip() or None,
            )
            db.add(assignment)
            created += 1
        except Exception as exc:  # noqa: BLE001
            row_errors.append(f"Row {idx}: {exc}")

    if row_errors:
        db.rollback()
        return {"created": 0, "errors": row_errors}

    db.commit()

    # Recalculate snapshots after bulk import
    updated_snapshots = recalculate_skill_snapshots(db)
    logger.info(
        "import_assignments.done", created=created, snapshots_updated=updated_snapshots
    )
    return {"created": created, "snapshots_updated": updated_snapshots, "errors": []}


def import_quality_metrics(db: Session, source: str | io.IOBase | bytes) -> dict[str, Any]:
    """
    Import quality metrics from CSV. Upserts on (operator, operation, period_start).

    Expected columns: matricule, operation_code, defects_per_100, pieces_produced,
                      period_start, period_end
    """
    df = _read_csv(source)
    errors = _validate_columns(
        df,
        ["matricule", "operation_code", "defects_per_100", "pieces_produced",
         "period_start", "period_end"],
        "quality_metrics",
    )
    if errors:
        return {"created": 0, "updated": 0, "errors": errors}

    created = updated = 0
    row_errors: list[str] = []

    for idx, row in df.iterrows():
        try:
            operator = (
                db.query(Operator).filter(Operator.matricule == row["matricule"].strip()).first()
            )
            if not operator:
                row_errors.append(f"Row {idx}: opérateur {row['matricule']!r} introuvable")
                continue

            operation = (
                db.query(Operation)
                .filter(Operation.code == row["operation_code"].strip())
                .first()
            )
            if not operation:
                row_errors.append(
                    f"Row {idx}: opération {row['operation_code']!r} introuvable"
                )
                continue

            period_start = _parse_date(row["period_start"])
            period_end = _parse_date(row["period_end"])

            existing = (
                db.query(QualityMetric)
                .filter(
                    QualityMetric.operator_id == operator.id,
                    QualityMetric.operation_id == operation.id,
                    QualityMetric.period_start == period_start,
                )
                .first()
            )

            if existing:
                existing.defects_per_100 = float(row["defects_per_100"])
                existing.pieces_produced = int(row["pieces_produced"])
                existing.period_end = period_end
                updated += 1
            else:
                metric = QualityMetric(
                    operator_id=operator.id,
                    operation_id=operation.id,
                    defects_per_100=float(row["defects_per_100"]),
                    pieces_produced=int(row["pieces_produced"]),
                    period_start=period_start,
                    period_end=period_end,
                )
                db.add(metric)
                created += 1
        except Exception as exc:  # noqa: BLE001
            row_errors.append(f"Row {idx}: {exc}")

    if row_errors:
        db.rollback()
        return {"created": 0, "updated": 0, "errors": row_errors}

    db.commit()
    logger.info("import_quality_metrics.done", created=created, updated=updated)
    return {"created": created, "updated": updated, "errors": []}


def import_operation_similarities(
    db: Session, source: str | io.IOBase | bytes
) -> dict[str, Any]:
    """
    Import operation similarity pairs from CSV. Upserts on (operation_code_a, operation_code_b).

    Expected columns: operation_code_a, operation_code_b, similarity
    """
    df = _read_csv(source)
    errors = _validate_columns(
        df, ["operation_code_a", "operation_code_b", "similarity"], "operation_similarities"
    )
    if errors:
        return {"created": 0, "updated": 0, "errors": errors}

    created = updated = 0
    row_errors: list[str] = []

    for idx, row in df.iterrows():
        try:
            op_a = (
                db.query(Operation)
                .filter(Operation.code == row["operation_code_a"].strip())
                .first()
            )
            op_b = (
                db.query(Operation)
                .filter(Operation.code == row["operation_code_b"].strip())
                .first()
            )
            if not op_a or not op_b:
                row_errors.append(
                    f"Row {idx}: opération introuvable "
                    f"({row['operation_code_a']!r} / {row['operation_code_b']!r})"
                )
                continue

            similarity = float(row["similarity"])
            if not (0.0 <= similarity <= 1.0):
                row_errors.append(f"Row {idx}: similarity hors plage [0,1]: {similarity}")
                continue

            # Normalize ordering: always store the lower id first
            id_a, id_b = (op_a.id, op_b.id) if op_a.id < op_b.id else (op_b.id, op_a.id)

            existing = (
                db.query(OperationSimilarity)
                .filter(
                    OperationSimilarity.operation_id_a == id_a,
                    OperationSimilarity.operation_id_b == id_b,
                )
                .first()
            )

            if existing:
                existing.similarity = similarity
                updated += 1
            else:
                sim = OperationSimilarity(
                    operation_id_a=id_a,
                    operation_id_b=id_b,
                    similarity=similarity,
                )
                db.add(sim)
                created += 1
        except Exception as exc:  # noqa: BLE001
            row_errors.append(f"Row {idx}: {exc}")

    if row_errors:
        db.rollback()
        return {"created": 0, "updated": 0, "errors": row_errors}

    db.commit()
    logger.info("import_similarities.done", created=created, updated=updated)
    return {"created": created, "updated": updated, "errors": []}


def recalculate_skill_snapshots(db: Session) -> int:
    """
    Recompute all SkillSnapshot records from the full assignment history.

    Called after any bulk import of assignments to ensure snapshots are
    consistent with the underlying data.

    Algorithm:
    1. GROUP BY (operator_id, operation_id): SUM(duration_hours), MAX(shift_date)
    2. Convert total_hours → mastery_score using the learning curve
    3. Upsert into skill_snapshots

    Returns the number of snapshots created or updated.
    """
    # Aggregate assignment data
    from sqlalchemy import func as sqlfunc
    from sqlalchemy import select

    rows = db.execute(
        select(
            Assignment.operator_id,
            Assignment.operation_id,
            sqlfunc.sum(Assignment.duration_hours).label("total_hours"),
            sqlfunc.max(Assignment.shift_date).label("last_date"),
        ).group_by(Assignment.operator_id, Assignment.operation_id)
    ).all()

    count = 0
    for row in rows:
        total_hours = float(row.total_hours or 0.0)
        last_date: date = row.last_date
        last_practice = datetime(
            last_date.year, last_date.month, last_date.day, tzinfo=timezone.utc
        ) if last_date else None

        mastery = mastery_from_hours(total_hours)

        existing = (
            db.query(SkillSnapshot)
            .filter(
                SkillSnapshot.operator_id == row.operator_id,
                SkillSnapshot.operation_id == row.operation_id,
            )
            .first()
        )
        if existing:
            existing.mastery_score = mastery
            existing.total_hours = total_hours
            existing.last_practice = last_practice
        else:
            snap = SkillSnapshot(
                operator_id=row.operator_id,
                operation_id=row.operation_id,
                mastery_score=mastery,
                total_hours=total_hours,
                last_practice=last_practice,
                decay_rate=float(90),
            )
            db.add(snap)
        count += 1

    db.commit()
    logger.info("recalculate_snapshots.done", updated=count)
    return count
