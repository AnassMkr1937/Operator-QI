"""
Tests for the matching engine (app.services.matching).

Covers:
- Score computation with known inputs
- Recency factor for the skill decay model
- Adjacency bonus contribution
- Quality penalty capping
- Candidate sorting order
- Edge cases: no candidates, operator with no skill data
"""

from datetime import datetime, timedelta, timezone

import pytest

from app.services.skill_decay import (
    compute_effective_mastery,
    compute_recency_factor,
    days_since,
    mastery_from_hours,
)


class TestRecencyFactor:
    """Unit tests for the exponential skill decay formula."""

    def test_practiced_today_returns_one(self):
        """Freshly practiced skill should have recency ≈ 1.0."""
        now = datetime.now(timezone.utc)
        factor = compute_recency_factor(now, half_life_days=90)
        assert 0.99 <= factor <= 1.0

    def test_half_life_point(self):
        """At exactly half_life_days the factor should be ≈ 0.5."""
        past = datetime.now(timezone.utc) - timedelta(days=90)
        factor = compute_recency_factor(past, half_life_days=90)
        assert abs(factor - 0.5) < 0.01

    def test_double_half_life(self):
        """At 2× half_life_days the factor should be ≈ 0.25."""
        past = datetime.now(timezone.utc) - timedelta(days=180)
        factor = compute_recency_factor(past, half_life_days=90)
        assert abs(factor - 0.25) < 0.02

    def test_very_old_skill_approaches_zero(self):
        """A skill not practiced in 5 years should be near zero."""
        ancient = datetime.now(timezone.utc) - timedelta(days=5 * 365)
        factor = compute_recency_factor(ancient, half_life_days=90)
        assert factor < 0.01

    def test_naive_datetime_handled(self):
        """Naive datetimes (no tzinfo) should be treated as UTC without error."""
        naive = datetime.utcnow() - timedelta(days=30)
        factor = compute_recency_factor(naive, half_life_days=90)
        assert 0 < factor < 1

    def test_different_half_lives(self):
        """A shorter half-life should decay faster than a longer one."""
        past = datetime.now(timezone.utc) - timedelta(days=45)
        fast = compute_recency_factor(past, half_life_days=30)
        slow = compute_recency_factor(past, half_life_days=180)
        assert fast < slow


class TestEffectiveMastery:
    """Tests for compute_effective_mastery."""

    def test_full_mastery_today(self):
        """100% mastery practiced today should remain 100%."""
        now = datetime.now(timezone.utc)
        effective = compute_effective_mastery(100.0, now, half_life_days=90)
        assert effective >= 99.0

    def test_decay_reduces_mastery(self):
        """Mastery should be lower after half_life_days of inactivity."""
        past = datetime.now(timezone.utc) - timedelta(days=90)
        effective = compute_effective_mastery(100.0, past, half_life_days=90)
        assert abs(effective - 50.0) < 1.0

    def test_zero_mastery_stays_zero(self):
        """An operator with 0 mastery should stay at 0 regardless of recency."""
        now = datetime.now(timezone.utc)
        effective = compute_effective_mastery(0.0, now, half_life_days=90)
        assert effective == 0.0


class TestDaysSince:
    """Tests for the days_since helper."""

    def test_today_returns_zero(self):
        now = datetime.now(timezone.utc)
        assert days_since(now) == 0

    def test_yesterday_returns_one(self):
        yesterday = datetime.now(timezone.utc) - timedelta(days=1, hours=1)
        assert days_since(yesterday) == 1

    def test_future_returns_zero(self):
        """A future datetime should never return a negative count."""
        future = datetime.now(timezone.utc) + timedelta(days=5)
        assert days_since(future) == 0


class TestMasteryFromHours:
    """Tests for the learning-curve mastery calculator."""

    def test_zero_hours_zero_mastery(self):
        assert mastery_from_hours(0) == 0.0

    def test_mastery_increases_with_hours(self):
        assert mastery_from_hours(50) < mastery_from_hours(100)
        assert mastery_from_hours(100) < mastery_from_hours(200)

    def test_saturation_approaches_100(self):
        """Very high hours should approach but not exceed 100."""
        score = mastery_from_hours(10_000)
        assert 95 <= score <= 100

    def test_half_saturation_gives_significant_mastery(self):
        """At half saturation hours, mastery should be in a reasonable range."""
        score = mastery_from_hours(100)  # half of default 200h saturation
        assert 40 < score < 60


class TestMatchingIntegration:
    """Integration tests for the full matching engine using an in-memory DB."""

    def test_compute_replacements_no_candidates(self, db):
        """With no present operators for the given shift, candidate list should be empty."""
        from app.models.operation import Operation
        from app.services.matching import compute_replacements

        op = Operation(code="T-001", name="Test Op", line="L1", criticality=3)
        db.add(op)
        db.commit()
        db.refresh(op)

        # Use a non-existent shift so no operators are returned
        result = compute_replacements(db, operation_id=op.id, shift="nonexistent_shift_xyz")
        assert result.operation_id == op.id
        assert result.candidates == []

    def test_compute_replacements_invalid_operation(self, db):
        """An invalid operation_id should raise ValueError."""
        from app.services.matching import compute_replacements

        with pytest.raises(ValueError, match="introuvable"):
            compute_replacements(db, operation_id=99999, shift="all")

    def test_compute_replacements_scores_sorted(self, db):
        """Candidates should be returned in descending score order."""
        from datetime import date

        from app.models.assignment import Assignment
        from app.models.operation import Operation
        from app.models.operator import Operator
        from app.models.skill import SkillSnapshot
        from app.services.matching import compute_replacements

        # Create operation
        operation = Operation(code="SORT-001", name="Sort Op", line="L1", criticality=3)
        db.add(operation)

        # Create two operators
        op1 = Operator(matricule="OP-001", full_name="Alice", team="A", shift="matin", status="present")
        op2 = Operator(matricule="OP-002", full_name="Bob", team="A", shift="matin", status="present")
        db.add_all([op1, op2])
        db.flush()

        # Alice has higher mastery
        db.add(SkillSnapshot(
            operator_id=op1.id,
            operation_id=operation.id,
            mastery_score=90.0,
            total_hours=100.0,
            last_practice=datetime.now(timezone.utc) - timedelta(days=5),
            decay_rate=90.0,
        ))
        # Bob has lower mastery
        db.add(SkillSnapshot(
            operator_id=op2.id,
            operation_id=operation.id,
            mastery_score=40.0,
            total_hours=20.0,
            last_practice=datetime.now(timezone.utc) - timedelta(days=5),
            decay_rate=90.0,
        ))
        db.commit()
        db.refresh(operation)

        result = compute_replacements(db, operation_id=operation.id, shift="all")
        assert len(result.candidates) == 2
        scores = [c.score for c in result.candidates]
        assert scores == sorted(scores, reverse=True), "Candidates must be sorted by score desc"
        assert result.candidates[0].matricule == "OP-001"

    def test_quality_penalty_reduces_score(self, db):
        """An operator with high defect rate should have a lower score."""
        from app.models.operation import Operation
        from app.models.operator import Operator
        from app.models.quality import QualityMetric
        from app.models.skill import SkillSnapshot
        from app.services.matching import compute_replacements
        from datetime import date

        operation = Operation(code="QUAL-001", name="Quality Op", line="L1", criticality=3)
        db.add(operation)

        op_clean = Operator(
            matricule="CLEAN-01", full_name="Clean Worker", team="A", shift="matin", status="present"
        )
        op_bad = Operator(
            matricule="BAD-01", full_name="Bad Worker", team="A", shift="matin", status="present"
        )
        db.add_all([op_clean, op_bad])
        db.flush()

        now = datetime.now(timezone.utc)
        for op_obj in [op_clean, op_bad]:
            db.add(SkillSnapshot(
                operator_id=op_obj.id,
                operation_id=operation.id,
                mastery_score=80.0,
                total_hours=80.0,
                last_practice=now - timedelta(days=1),
                decay_rate=90.0,
            ))

        db.add(QualityMetric(
            operator_id=op_bad.id,
            operation_id=operation.id,
            defects_per_100=10.0,
            pieces_produced=500,
            period_start=date(2024, 1, 1),
            period_end=date(2024, 1, 31),
        ))
        db.commit()
        db.refresh(operation)

        result = compute_replacements(db, operation_id=operation.id, shift="all")
        scores = {c.matricule: c.score for c in result.candidates}
        assert scores["CLEAN-01"] > scores["BAD-01"]
