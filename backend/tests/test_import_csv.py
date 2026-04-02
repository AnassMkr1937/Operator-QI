"""
Tests for the CSV import pipeline (app.services.import_csv).

Uses in-memory CSV data (via io.StringIO / bytes) so no actual files
are needed on disk.
"""

import io

import pytest


def _csv_bytes(header: str, *rows: str) -> bytes:
    """Build CSV bytes from a header string and row strings."""
    content = "\n".join([header, *rows])
    return content.encode("utf-8")


class TestImportOperators:
    def test_import_creates_new_operators(self, db):
        from app.services.import_csv import import_operators

        csv = _csv_bytes(
            "matricule,full_name,team,shift,status",
            "OP-100,Alice Martin,A,matin,present",
            "OP-101,Bob Dupont,B,apres-midi,present",
        )
        result = import_operators(db, csv)
        assert result["created"] == 2
        assert result["updated"] == 0
        assert result["errors"] == []

    def test_import_upserts_existing_operator(self, db):
        from app.services.import_csv import import_operators

        csv1 = _csv_bytes(
            "matricule,full_name,team,shift",
            "OP-200,Original Name,A,matin",
        )
        import_operators(db, csv1)

        csv2 = _csv_bytes(
            "matricule,full_name,team,shift",
            "OP-200,Updated Name,B,nuit",
        )
        result = import_operators(db, csv2)
        assert result["updated"] == 1
        assert result["created"] == 0

        from app.models.operator import Operator
        op = db.query(Operator).filter(Operator.matricule == "OP-200").first()
        assert op.full_name == "Updated Name"
        assert op.team == "B"

    def test_missing_column_returns_error(self, db):
        from app.services.import_csv import import_operators

        csv = _csv_bytes(
            "matricule,full_name",  # Missing team and shift
            "OP-999,Nobody",
        )
        result = import_operators(db, csv)
        assert len(result["errors"]) > 0
        assert result["created"] == 0


class TestImportOperations:
    def test_import_creates_operations(self, db):
        from app.services.import_csv import import_operations

        csv = _csv_bytes(
            "code,name,line,criticality,nominal_cycle_time_s",
            "OP-A-001,Assemblage Moteur,L1,4,45.0",
            "OP-A-002,Vissage Carter,L1,3,30.0",
        )
        result = import_operations(db, csv)
        assert result["created"] == 2
        assert result["errors"] == []

    def test_import_upserts_operations(self, db):
        from app.services.import_csv import import_operations

        csv1 = _csv_bytes("code,name,line", "OP-B-001,Old Name,L2")
        import_operations(db, csv1)

        csv2 = _csv_bytes("code,name,line,criticality", "OP-B-001,New Name,L2,5")
        result = import_operations(db, csv2)
        assert result["updated"] == 1

        from app.models.operation import Operation
        op = db.query(Operation).filter(Operation.code == "OP-B-001").first()
        assert op.name == "New Name"
        assert op.criticality == 5


class TestImportAssignments:
    def test_import_creates_assignments_and_snapshots(self, db):
        from app.services.import_csv import import_assignments, import_operations, import_operators
        from app.models.skill import SkillSnapshot

        import_operators(
            db,
            _csv_bytes("matricule,full_name,team,shift", "OP-300,Worker A,A,matin"),
        )
        import_operations(
            db,
            _csv_bytes("code,name,line", "AS-001,Assembly,L1"),
        )

        csv = _csv_bytes(
            "matricule,operation_code,shift_date,duration_hours,shift_label",
            "OP-300,AS-001,2024-01-15,8.0,matin",
            "OP-300,AS-001,2024-01-16,7.5,matin",
        )
        result = import_assignments(db, csv)
        assert result["created"] == 2
        assert result["errors"] == []
        assert result["snapshots_updated"] >= 1

        snap = (
            db.query(SkillSnapshot)
            .join(SkillSnapshot.operator)
            .filter_by(matricule="OP-300")
            .first()
        )
        assert snap is not None
        assert snap.total_hours == pytest.approx(15.5, abs=0.01)

    def test_unknown_matricule_returns_error(self, db):
        from app.services.import_csv import import_assignments, import_operations

        import_operations(db, _csv_bytes("code,name,line", "AS-002,Op,L1"))

        csv = _csv_bytes(
            "matricule,operation_code,shift_date,duration_hours",
            "UNKNOWN-MATRICULE,AS-002,2024-01-01,8.0",
        )
        result = import_assignments(db, csv)
        assert len(result["errors"]) > 0
        assert result["created"] == 0


class TestImportQualityMetrics:
    def test_import_creates_metrics(self, db):
        from app.services.import_csv import import_operations, import_operators, import_quality_metrics

        import_operators(db, _csv_bytes("matricule,full_name,team,shift", "OP-400,Worker Q,A,matin"))
        import_operations(db, _csv_bytes("code,name,line", "QM-001,Quality Op,L1"))

        csv = _csv_bytes(
            "matricule,operation_code,defects_per_100,pieces_produced,period_start,period_end",
            "OP-400,QM-001,1.5,200,2024-01-01,2024-01-31",
        )
        result = import_quality_metrics(db, csv)
        assert result["created"] == 1
        assert result["errors"] == []

    def test_missing_columns_error(self, db):
        from app.services.import_csv import import_quality_metrics

        csv = _csv_bytes("matricule,operation_code", "OP-400,QM-001")
        result = import_quality_metrics(db, csv)
        assert len(result["errors"]) > 0


class TestRecalculateSnapshots:
    def test_recalculate_updates_mastery(self, db):
        from app.services.import_csv import (
            import_assignments,
            import_operations,
            import_operators,
            recalculate_skill_snapshots,
        )
        from app.models.skill import SkillSnapshot

        import_operators(db, _csv_bytes("matricule,full_name,team,shift", "OP-500,Recalc Worker,A,matin"))
        import_operations(db, _csv_bytes("code,name,line", "RC-001,Recalc Op,L1"))

        import_assignments(
            db,
            _csv_bytes(
                "matricule,operation_code,shift_date,duration_hours",
                "OP-500,RC-001,2024-02-01,50.0",
            ),
        )

        count = recalculate_skill_snapshots(db)
        assert count >= 1

        snap = (
            db.query(SkillSnapshot)
            .join(SkillSnapshot.operator)
            .filter_by(matricule="OP-500")
            .first()
        )
        assert snap is not None
        assert snap.total_hours == pytest.approx(50.0, abs=0.01)
        assert snap.mastery_score > 0
