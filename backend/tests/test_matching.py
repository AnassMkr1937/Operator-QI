"""Unit tests for the matching service scoring algorithm."""

from __future__ import annotations

from datetime import date, timedelta

import pytest

from app.schemas.recommendation import (
    CandidateOperator,
    OperationContext,
    OperatorSkill,
    PastAssignment,
    RequiredSkill,
)
from app.services.matching import (
    WEIGHT_AVAILABILITY,
    WEIGHT_HISTORY,
    WEIGHT_SKILLS,
    compute_score,
    hard_filter,
    rank_candidates,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

TODAY = date(2024, 6, 15)


def make_operation(
    *,
    operation_id: str = "OP-001",
    required_skills: list[RequiredSkill] | None = None,
    assignment_date: date = TODAY,
    shift: str = "morning",
    category: str | None = None,
) -> OperationContext:
    return OperationContext(
        operation_id=operation_id,
        name="Test Operation",
        required_skills=required_skills or [],
        assignment_date=assignment_date,
        shift=shift,
        category=category,
    )


def make_candidate(
    *,
    operator_id: str = "OP-A",
    is_active: bool = True,
    skills: list[OperatorSkill] | None = None,
    assignments: list[PastAssignment] | None = None,
) -> CandidateOperator:
    return CandidateOperator(
        operator_id=operator_id,
        name=f"Operator {operator_id}",
        is_active=is_active,
        skills=skills or [],
        assignments=assignments or [],
    )


def make_skill(
    skill_id: str,
    proficiency: int = 3,
    certified: bool = False,
    last_used_date: date | None = None,
) -> OperatorSkill:
    return OperatorSkill(
        skill_id=skill_id,
        proficiency=proficiency,
        certified=certified,
        last_used_date=last_used_date,
    )


def make_assignment(
    operation_id: str = "OP-001",
    assignment_date: date = date(2024, 1, 1),
    shift: str = "morning",
    category: str | None = None,
) -> PastAssignment:
    return PastAssignment(
        operation_id=operation_id,
        assignment_date=assignment_date,
        shift=shift,
        category=category,
    )


# ---------------------------------------------------------------------------
# Hard filter tests
# ---------------------------------------------------------------------------


class TestHardFilter:
    def test_inactive_operator_is_filtered(self) -> None:
        op = make_operation()
        candidate = make_candidate(is_active=False)
        result = hard_filter(candidate, op)
        assert not result.eligible
        assert "inactive" in result.reason

    def test_active_operator_passes(self) -> None:
        op = make_operation()
        candidate = make_candidate()
        result = hard_filter(candidate, op)
        assert result.eligible
        assert result.reason is None

    def test_conflicting_assignment_same_date_and_shift(self) -> None:
        op = make_operation(assignment_date=TODAY, shift="morning")
        conflict = make_assignment(
            operation_id="OTHER-OP", assignment_date=TODAY, shift="morning"
        )
        candidate = make_candidate(assignments=[conflict])
        result = hard_filter(candidate, op)
        assert not result.eligible
        assert "conflicting" in result.reason

    def test_assignment_different_shift_is_ok(self) -> None:
        op = make_operation(assignment_date=TODAY, shift="morning")
        candidate = make_candidate(
            assignments=[make_assignment(assignment_date=TODAY, shift="afternoon")]
        )
        result = hard_filter(candidate, op)
        assert result.eligible

    def test_assignment_different_date_is_ok(self) -> None:
        op = make_operation(assignment_date=TODAY, shift="morning")
        candidate = make_candidate(
            assignments=[make_assignment(assignment_date=date(2024, 6, 16), shift="morning")]
        )
        result = hard_filter(candidate, op)
        assert result.eligible

    def test_missing_mandatory_skill_filtered(self) -> None:
        op = make_operation(
            required_skills=[RequiredSkill(skill_id="welding", min_proficiency=2, mandatory=True)]
        )
        candidate = make_candidate()  # no skills
        result = hard_filter(candidate, op)
        assert not result.eligible
        assert "welding" in result.reason

    def test_below_threshold_mandatory_skill_filtered(self) -> None:
        op = make_operation(
            required_skills=[RequiredSkill(skill_id="welding", min_proficiency=4, mandatory=True)]
        )
        candidate = make_candidate(skills=[make_skill("welding", proficiency=2)])
        result = hard_filter(candidate, op)
        assert not result.eligible
        assert "welding" in result.reason

    def test_missing_non_mandatory_skill_not_filtered(self) -> None:
        op = make_operation(
            required_skills=[RequiredSkill(skill_id="welding", min_proficiency=2, mandatory=False)]
        )
        candidate = make_candidate()  # no skills
        result = hard_filter(candidate, op)
        assert result.eligible

    def test_meets_mandatory_skill_threshold_passes(self) -> None:
        op = make_operation(
            required_skills=[RequiredSkill(skill_id="welding", min_proficiency=3, mandatory=True)]
        )
        candidate = make_candidate(skills=[make_skill("welding", proficiency=3)])
        result = hard_filter(candidate, op)
        assert result.eligible


# ---------------------------------------------------------------------------
# Scoring component tests
# ---------------------------------------------------------------------------


class TestComputeScore:
    def test_no_required_skills_full_skills_score(self) -> None:
        op = make_operation()
        candidate = make_candidate()
        total, breakdown, unmet = compute_score(candidate, op, evaluation_date=TODAY)
        assert breakdown.raw_skills == 1.0
        assert breakdown.skills_score == pytest.approx(WEIGHT_SKILLS)
        assert unmet == []

    def test_perfect_skill_match(self) -> None:
        op = make_operation(
            required_skills=[RequiredSkill(skill_id="welding", min_proficiency=3)]
        )
        candidate = make_candidate(skills=[make_skill("welding", proficiency=5)])
        total, breakdown, unmet = compute_score(candidate, op, evaluation_date=TODAY)
        assert breakdown.raw_skills == pytest.approx(1.0)  # 5/5 = 1.0, capped

    def test_certified_skill_bonus(self) -> None:
        op = make_operation(
            required_skills=[RequiredSkill(skill_id="welding", min_proficiency=1)]
        )
        candidate_cert = make_candidate(
            operator_id="cert",
            skills=[make_skill("welding", proficiency=3, certified=True)],
        )
        candidate_no_cert = make_candidate(
            operator_id="no_cert",
            skills=[make_skill("welding", proficiency=3, certified=False)],
        )
        _, bd_cert, _ = compute_score(candidate_cert, op, evaluation_date=TODAY)
        _, bd_no_cert, _ = compute_score(candidate_no_cert, op, evaluation_date=TODAY)
        assert bd_cert.raw_skills > bd_no_cert.raw_skills

    def test_recent_skill_bonus(self) -> None:
        op = make_operation(
            required_skills=[RequiredSkill(skill_id="welding", min_proficiency=1)]
        )
        recent_date = TODAY - timedelta(days=10)
        old_date = TODAY - timedelta(days=180)
        candidate_recent = make_candidate(
            operator_id="recent",
            skills=[make_skill("welding", proficiency=3, last_used_date=recent_date)],
        )
        candidate_old = make_candidate(
            operator_id="old",
            skills=[make_skill("welding", proficiency=3, last_used_date=old_date)],
        )
        _, bd_recent, _ = compute_score(candidate_recent, op, evaluation_date=TODAY)
        _, bd_old, _ = compute_score(candidate_old, op, evaluation_date=TODAY)
        assert bd_recent.raw_skills > bd_old.raw_skills

    def test_moderate_recency_bonus(self) -> None:
        op = make_operation(
            required_skills=[RequiredSkill(skill_id="welding", min_proficiency=1)]
        )
        moderate_date = TODAY - timedelta(days=60)
        candidate = make_candidate(
            skills=[make_skill("welding", proficiency=3, last_used_date=moderate_date)]
        )
        _, bd, _ = compute_score(candidate, op, evaluation_date=TODAY)
        # proficiency score 3/5=0.6 + moderate_bonus 0.05 = 0.65
        assert bd.raw_skills == pytest.approx(0.65)

    def test_availability_always_one_after_hard_filter(self) -> None:
        op = make_operation()
        candidate = make_candidate()
        _, breakdown, _ = compute_score(candidate, op, evaluation_date=TODAY)
        assert breakdown.raw_availability == 1.0
        assert breakdown.availability_score == pytest.approx(WEIGHT_AVAILABILITY)

    def test_history_same_operation(self) -> None:
        op = make_operation(operation_id="OP-001")
        candidate = make_candidate(
            assignments=[
                make_assignment(operation_id="OP-001", assignment_date=date(2024, 1, 1)),
                make_assignment(operation_id="OP-001", assignment_date=date(2024, 2, 1)),
            ]
        )
        _, breakdown, _ = compute_score(candidate, op, evaluation_date=TODAY)
        # 2 × 0.5 = 1.0 capped
        assert breakdown.raw_history == 1.0
        assert breakdown.history_score == pytest.approx(WEIGHT_HISTORY)

    def test_history_same_category(self) -> None:
        op = make_operation(operation_id="OP-002", category="assembly")
        candidate = make_candidate(
            assignments=[
                make_assignment(operation_id="OP-999", category="assembly"),
            ]
        )
        _, breakdown, _ = compute_score(candidate, op, evaluation_date=TODAY)
        assert breakdown.raw_history == pytest.approx(0.25)

    def test_history_same_op_takes_precedence_over_category(self) -> None:
        op = make_operation(operation_id="OP-001", category="assembly")
        candidate = make_candidate(
            assignments=[
                make_assignment(operation_id="OP-001"),  # same op
                make_assignment(operation_id="OP-999", category="assembly"),  # same cat
            ]
        )
        _, breakdown, _ = compute_score(candidate, op, evaluation_date=TODAY)
        # same_op_score = 0.5, same_cat_score = 0.25 → total 0.75
        assert breakdown.raw_history == pytest.approx(0.75)

    def test_no_history_zero_score(self) -> None:
        op = make_operation(operation_id="OP-001")
        candidate = make_candidate()
        _, breakdown, _ = compute_score(candidate, op, evaluation_date=TODAY)
        assert breakdown.raw_history == 0.0

    def test_experience_no_skills(self) -> None:
        op = make_operation()
        candidate = make_candidate()
        _, breakdown, _ = compute_score(candidate, op, evaluation_date=TODAY)
        assert breakdown.raw_experience == 0.0

    def test_experience_normalised(self) -> None:
        op = make_operation()
        # 5 skills at proficiency 5 → raw_experience = (5*5) / 25 = 1.0
        candidate = make_candidate(
            skills=[make_skill(f"skill_{i}", proficiency=5) for i in range(5)]
        )
        _, breakdown, _ = compute_score(candidate, op, evaluation_date=TODAY)
        assert breakdown.raw_experience == pytest.approx(1.0)

    def test_experience_capped_at_one(self) -> None:
        op = make_operation()
        candidate = make_candidate(
            skills=[make_skill(f"skill_{i}", proficiency=5) for i in range(20)]
        )
        _, breakdown, _ = compute_score(candidate, op, evaluation_date=TODAY)
        assert breakdown.raw_experience == pytest.approx(1.0)

    def test_weights_sum_to_total_score(self) -> None:
        op = make_operation(
            required_skills=[RequiredSkill(skill_id="welding", min_proficiency=2)]
        )
        candidate = make_candidate(skills=[make_skill("welding", proficiency=4)])
        total, breakdown, _ = compute_score(candidate, op, evaluation_date=TODAY)
        computed_total = (
            breakdown.skills_score
            + breakdown.availability_score
            + breakdown.history_score
            + breakdown.experience_score
        )
        assert total == pytest.approx(computed_total, abs=1e-4)

    def test_unmet_non_mandatory_skill_recorded(self) -> None:
        op = make_operation(
            required_skills=[RequiredSkill(skill_id="grinding", mandatory=False)]
        )
        candidate = make_candidate()  # no skills
        _, _, unmet = compute_score(candidate, op, evaluation_date=TODAY)
        assert any("grinding" in u for u in unmet)

    def test_unmet_below_recommended_proficiency(self) -> None:
        op = make_operation(
            required_skills=[
                RequiredSkill(skill_id="welding", min_proficiency=4, mandatory=False)
            ]
        )
        candidate = make_candidate(skills=[make_skill("welding", proficiency=2)])
        _, _, unmet = compute_score(candidate, op, evaluation_date=TODAY)
        assert any("welding" in u for u in unmet)


# ---------------------------------------------------------------------------
# rank_candidates tests
# ---------------------------------------------------------------------------


class TestRankCandidates:
    def test_returns_top_n(self) -> None:
        op = make_operation()
        candidates = [make_candidate(operator_id=f"OP-{i}") for i in range(10)]
        recs, _ = rank_candidates(op, candidates, top_n=3, evaluation_date=TODAY)
        assert len(recs) <= 3

    def test_inactive_operator_not_in_results(self) -> None:
        op = make_operation()
        candidates = [
            make_candidate(operator_id="inactive", is_active=False),
            make_candidate(operator_id="active"),
        ]
        recs, filtered = rank_candidates(op, candidates, evaluation_date=TODAY)
        ids = [r.operator_id for r in recs]
        assert "inactive" not in ids
        assert "inactive" in filtered

    def test_no_eligible_candidates(self) -> None:
        op = make_operation()
        candidates = [make_candidate(is_active=False)]
        recs, filtered = rank_candidates(op, candidates, evaluation_date=TODAY)
        assert recs == []
        assert len(filtered) == 1

    def test_ranks_are_sequential(self) -> None:
        op = make_operation()
        candidates = [make_candidate(operator_id=f"OP-{i}") for i in range(5)]
        recs, _ = rank_candidates(op, candidates, evaluation_date=TODAY)
        ranks = [r.rank for r in recs]
        assert ranks == list(range(1, len(recs) + 1))

    def test_higher_score_ranked_first(self) -> None:
        op = make_operation(
            required_skills=[RequiredSkill(skill_id="welding", min_proficiency=1)]
        )
        good = make_candidate(
            operator_id="good",
            skills=[make_skill("welding", proficiency=5, certified=True)],
            assignments=[make_assignment(operation_id=op.operation_id)],
        )
        poor = make_candidate(
            operator_id="poor",
            skills=[make_skill("welding", proficiency=1)],
        )
        recs, _ = rank_candidates(op, [good, poor], evaluation_date=TODAY)
        assert recs[0].operator_id == "good"
        assert recs[1].operator_id == "poor"

    def test_tie_broken_by_operator_id_lexicographic(self) -> None:
        op = make_operation()
        # Both candidates have no skills, no history → identical scores
        a = make_candidate(operator_id="b_operator")
        b = make_candidate(operator_id="a_operator")
        recs, _ = rank_candidates(op, [a, b], evaluation_date=TODAY)
        assert recs[0].operator_id == "a_operator"
        assert recs[1].operator_id == "b_operator"

    def test_conflicting_assignment_excluded(self) -> None:
        op = make_operation(assignment_date=TODAY, shift="morning")
        conflict_assignment = make_assignment(
            operation_id="OTHER", assignment_date=TODAY, shift="morning"
        )
        conflicting = make_candidate(
            operator_id="conflict",
            assignments=[conflict_assignment],
        )
        recs, filtered = rank_candidates(op, [conflicting], evaluation_date=TODAY)
        assert recs == []
        assert "conflict" in filtered

    def test_score_breakdown_present(self) -> None:
        op = make_operation()
        candidate = make_candidate()
        recs, _ = rank_candidates(op, [candidate], evaluation_date=TODAY)
        assert len(recs) == 1
        bd = recs[0].breakdown
        assert hasattr(bd, "skills_score")
        assert hasattr(bd, "availability_score")
        assert hasattr(bd, "history_score")
        assert hasattr(bd, "experience_score")

    def test_explanation_non_empty(self) -> None:
        op = make_operation()
        candidate = make_candidate()
        recs, _ = rank_candidates(op, [candidate], evaluation_date=TODAY)
        assert recs[0].explanation != ""

    def test_filtered_out_ids_returned(self) -> None:
        op = make_operation()
        inactive = make_candidate(operator_id="inactive-1", is_active=False)
        active = make_candidate(operator_id="active-1")
        _, filtered = rank_candidates(op, [inactive, active], evaluation_date=TODAY)
        assert "inactive-1" in filtered
        assert "active-1" not in filtered

    def test_missing_mandatory_skill_in_filtered_out(self) -> None:
        op = make_operation(
            required_skills=[RequiredSkill(skill_id="welding", mandatory=True)]
        )
        no_skill = make_candidate(operator_id="no-skill")
        has_skill = make_candidate(
            operator_id="has-skill",
            skills=[make_skill("welding", proficiency=3)],
        )
        recs, filtered = rank_candidates(op, [no_skill, has_skill], evaluation_date=TODAY)
        assert "no-skill" in filtered
        assert recs[0].operator_id == "has-skill"
