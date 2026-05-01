#!/usr/bin/env python3
"""Import operator data from CSV files into the database.

Expected CSV formats:
- operators.csv: operator_id,name,is_active
- operator_skills.csv: operator_id,skill_id,proficiency,certified,last_used_date
- assignments.csv: operator_id,operation_id,assignment_date,shift,category
"""

from __future__ import annotations

import argparse
import csv
from datetime import date
from pathlib import Path

from app.core.config import get_settings
from app.db.base import Base
from app.db.session import create_engine_from_settings, create_session_factory
from app.models.operator import Assignment, Operator, OperatorSkill
from app.models.skill import Skill


def parse_bool(value: str) -> bool:
    return value.strip().lower() in {"1", "true", "yes", "y"}


def parse_date(value: str) -> date | None:
    value = value.strip()
    if not value:
        return None
    return date.fromisoformat(value)


def load_rows(path: Path):
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        return list(reader)


def main() -> None:
    parser = argparse.ArgumentParser(description="Import operator data from CSV files.")
    parser.add_argument("--operators", type=Path, default=Path("data/operators.csv"))
    parser.add_argument("--skills", type=Path, default=Path("data/operator_skills.csv"))
    parser.add_argument("--assignments", type=Path, default=Path("data/assignments.csv"))
    args = parser.parse_args()

    settings = get_settings()
    engine = create_engine_from_settings(settings)
    Base.metadata.create_all(bind=engine)
    session_factory = create_session_factory(engine)

    operators_rows = load_rows(args.operators)
    skills_rows = load_rows(args.skills)
    assignments_rows = load_rows(args.assignments)

    with session_factory() as db:
        for row in operators_rows:
            operator_id = row["operator_id"].strip()
            if db.get(Operator, operator_id):
                continue
            db.add(
                Operator(
                    operator_id=operator_id,
                    name=row["name"].strip(),
                    is_active=parse_bool(row.get("is_active", "true")),
                )
            )

        for row in skills_rows:
            operator_id = row["operator_id"].strip()
            skill_id = row["skill_id"].strip()
            if not db.get(Skill, skill_id):
                db.add(Skill(skill_id=skill_id))
            db.merge(
                OperatorSkill(
                    operator_id=operator_id,
                    skill_id=skill_id,
                    proficiency=int(row["proficiency"]),
                    certified=parse_bool(row.get("certified", "false")),
                    last_used_date=parse_date(row.get("last_used_date", "")),
                )
            )

        for row in assignments_rows:
            db.add(
                Assignment(
                    operator_id=row["operator_id"].strip(),
                    operation_id=row["operation_id"].strip(),
                    assignment_date=date.fromisoformat(row["assignment_date"]),
                    shift=row["shift"].strip(),
                    category=row.get("category") or None,
                )
            )

        db.commit()

    print("Import terminé ✅")


if __name__ == "__main__":
    main()
