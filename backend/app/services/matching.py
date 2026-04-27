"""Deterministic operator matching / scoring engine (v1).

Algorithm overview
------------------
Candidates are evaluated against an :class:`OperationContext` in two phases:

1. **Hard filters** (any failing filter → candidate excluded):
   - Operator is not active.
   - Operator has a conflicting assignment on the same date + shift.
   - Operator is missing a skill marked as *mandatory* in the operation.
   - Operator's proficiency for a mandatory skill is below the required minimum.

2. **Weighted scoring** (all components in [0, 1], weights sum to 1.0):

   +--------------+--------+-----------------------------------------------+
   | Component    | Weight | Description                                   |
   +==============+========+===============================================+
   | skills       |  0.40  | Skill coverage × average proficiency ratio,   |
   |              |        | with bonuses for certification (+0.10) and    |
   |              |        | recency (last_used_date ≤ 30 days: +0.10,     |
   |              |        | ≤ 90 days: +0.05).                            |
   +--------------+--------+-----------------------------------------------+
   | availability |  0.30  | 1.0 if no shift conflict, 0.0 otherwise       |
   |              |        | (conflict → hard filter, so always 1.0 here). |
   +--------------+--------+-----------------------------------------------+
   | history      |  0.20  | Previous assignments on the *same* operation  |
   |              |        | (+0.50 each, capped at 1.0) plus similar      |
   |              |        | category assignments (+0.25 each, capped at   |
   |              |        | 0.50); total capped at 1.0.                   |
   +--------------+--------+-----------------------------------------------+
   | experience   |  0.10  | Normalised total-skills × mean-proficiency    |
   |              |        | (max reference: 5 skills at proficiency 5).   |
   +--------------+--------+-----------------------------------------------+

Ties are broken deterministically by operator_id (lexicographic ascending).
"""

from __future__ import annotations

from datetime import date
from typing import NamedTuple

from app.schemas.recommendation import (
    CandidateOperator,
    CandidateRecommendation,
    OperationContext,
    ScoreBreakdown,
)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

WEIGHT_SKILLS: float = 0.40
WEIGHT_AVAILABILITY: float = 0.30
WEIGHT_HISTORY: float = 0.20
WEIGHT_EXPERIENCE: float = 0.10

# Max raw score reference for experience normalisation:
# 5 distinct skills each at proficiency level 5
_EXPERIENCE_MAX_REF: float = 5.0 * 5.0  # 25.0

# Proficiency scale maximum
_PROFICIENCY_MAX: float = 5.0

# Recency thresholds (days)
_RECENCY_RECENT_DAYS: int = 30
_RECENCY_MODERATE_DAYS: int = 90

# Bonuses applied to a single skill score component (before capping at 1.0)
_CERT_BONUS: float = 0.10
_RECENCY_RECENT_BONUS: float = 0.10
_RECENCY_MODERATE_BONUS: float = 0.05

# History score increments
_HISTORY_SAME_OP_INC: float = 0.50
_HISTORY_SAME_CAT_INC: float = 0.25
_HISTORY_SAME_CAT_CAP: float = 0.50


# ---------------------------------------------------------------------------
# Internal types
# ---------------------------------------------------------------------------


class _ScoredCandidate(NamedTuple):
    """Internal result before building the public response model."""

    operator_id: str
    name: str
    total_score: float
    breakdown: ScoreBreakdown
    unmet_requirements: list[str]
    explanation: str


class _FilterResult(NamedTuple):
    """Result of the hard-filter step."""

    eligible: bool
    reason: str | None  # populated when eligible is False


# ---------------------------------------------------------------------------
# Public helpers
# ---------------------------------------------------------------------------


def hard_filter(
    candidate: CandidateOperator,
    operation: OperationContext,
) -> _FilterResult:
    """Apply hard filters; return a :class:`_FilterResult`."""

    # 1. Inactive operator
    if not candidate.is_active:
        return _FilterResult(eligible=False, reason="operator is inactive")

    # 2. Conflicting assignment on the same date + shift
    for assignment in candidate.assignments:
        same_date = assignment.assignment_date == operation.assignment_date
        same_shift = assignment.shift == operation.shift
        if same_date and same_shift:
            return _FilterResult(
                eligible=False,
                reason=(
                    f"conflicting assignment on {operation.assignment_date} "
                    f"({operation.shift} shift) "
                    f"for operation '{assignment.operation_id}'"
                ),
            )

    # 3. Missing or below-threshold mandatory skill
    skills_map = {s.skill_id: s for s in candidate.skills}
    for req in operation.required_skills:
        if not req.mandatory:
            continue
        if req.skill_id not in skills_map:
            return _FilterResult(
                eligible=False,
                reason=f"missing mandatory skill '{req.skill_id}'",
            )
        op_skill = skills_map[req.skill_id]
        if op_skill.proficiency < req.min_proficiency:
            return _FilterResult(
                eligible=False,
                reason=(
                    f"proficiency {op_skill.proficiency} for mandatory skill "
                    f"'{req.skill_id}' is below minimum {req.min_proficiency}"
                ),
            )

    return _FilterResult(eligible=True, reason=None)


def compute_score(
    candidate: CandidateOperator,
    operation: OperationContext,
    evaluation_date: date | None = None,
) -> tuple[float, ScoreBreakdown, list[str]]:
    """Compute the weighted score for an *eligible* candidate.

    Parameters
    ----------
    candidate:
        Candidate operator (must have passed :func:`hard_filter`).
    operation:
        Operation context to score against.
    evaluation_date:
        Reference date for recency calculations.  Defaults to today.

    Returns
    -------
    tuple of (total_score, ScoreBreakdown, unmet_requirements)
    """
    today = evaluation_date or date.today()
    skills_map = {s.skill_id: s for s in candidate.skills}
    unmet: list[str] = []

    # ------------------------------------------------------------------
    # 1. Skills component
    # ------------------------------------------------------------------
    skill_raw_scores: list[float] = []

    for req in operation.required_skills:
        if req.skill_id not in skills_map:
            # Non-mandatory missing skill (mandatory ones are hard-filtered)
            unmet.append(f"missing non-mandatory skill '{req.skill_id}'")
            skill_raw_scores.append(0.0)
            continue

        op_skill = skills_map[req.skill_id]

        # Base proficiency ratio
        prof_ratio = op_skill.proficiency / _PROFICIENCY_MAX

        # Below minimum but non-mandatory: record as unmet, still partial credit
        if op_skill.proficiency < req.min_proficiency:
            unmet.append(
                f"proficiency {op_skill.proficiency} for '{req.skill_id}' "
                f"is below recommended minimum {req.min_proficiency}"
            )

        # Bonuses
        cert_bonus = _CERT_BONUS if op_skill.certified else 0.0
        recency_bonus = 0.0
        if op_skill.last_used_date is not None:
            days_since = (today - op_skill.last_used_date).days
            if days_since <= _RECENCY_RECENT_DAYS:
                recency_bonus = _RECENCY_RECENT_BONUS
            elif days_since <= _RECENCY_MODERATE_DAYS:
                recency_bonus = _RECENCY_MODERATE_BONUS

        skill_raw_scores.append(min(prof_ratio + cert_bonus + recency_bonus, 1.0))

    n_required = len(operation.required_skills)
    if n_required == 0:
        raw_skills = 1.0  # No requirements → full score
    else:
        coverage_ratio = len(skill_raw_scores) / n_required
        avg_skill = sum(skill_raw_scores) / len(skill_raw_scores) if skill_raw_scores else 0.0
        raw_skills = coverage_ratio * avg_skill

    # ------------------------------------------------------------------
    # 2. Availability component
    # ------------------------------------------------------------------
    # Hard filter already excluded conflicts → always 1.0 here
    raw_availability = 1.0

    # ------------------------------------------------------------------
    # 3. History component
    # ------------------------------------------------------------------
    same_op_score = 0.0
    same_cat_score = 0.0

    for assignment in candidate.assignments:
        if assignment.operation_id == operation.operation_id:
            same_op_score = min(same_op_score + _HISTORY_SAME_OP_INC, 1.0)
        elif (
            operation.category is not None
            and assignment.category is not None
            and assignment.category == operation.category
        ):
            same_cat_score = min(same_cat_score + _HISTORY_SAME_CAT_INC, _HISTORY_SAME_CAT_CAP)

    raw_history = min(same_op_score + same_cat_score, 1.0)

    # ------------------------------------------------------------------
    # 4. Experience component
    # ------------------------------------------------------------------
    total_skills = len(candidate.skills)
    if total_skills == 0:
        raw_experience = 0.0
    else:
        avg_proficiency = sum(s.proficiency for s in candidate.skills) / total_skills
        raw_experience = min((total_skills * avg_proficiency) / _EXPERIENCE_MAX_REF, 1.0)

    # ------------------------------------------------------------------
    # Weighted total
    # ------------------------------------------------------------------
    total = (
        raw_skills * WEIGHT_SKILLS
        + raw_availability * WEIGHT_AVAILABILITY
        + raw_history * WEIGHT_HISTORY
        + raw_experience * WEIGHT_EXPERIENCE
    )

    breakdown = ScoreBreakdown(
        skills_score=round(raw_skills * WEIGHT_SKILLS, 4),
        availability_score=round(raw_availability * WEIGHT_AVAILABILITY, 4),
        history_score=round(raw_history * WEIGHT_HISTORY, 4),
        experience_score=round(raw_experience * WEIGHT_EXPERIENCE, 4),
        raw_skills=round(raw_skills, 4),
        raw_availability=round(raw_availability, 4),
        raw_history=round(raw_history, 4),
        raw_experience=round(raw_experience, 4),
    )

    return round(total, 4), breakdown, unmet


def build_explanation(
    candidate: CandidateOperator,
    operation: OperationContext,
    breakdown: ScoreBreakdown,
    unmet: list[str],
) -> str:
    """Generate a stable, human-readable explanation of the score."""
    parts: list[str] = []

    # Skills part
    n_required = len(operation.required_skills)
    skills_map = {s.skill_id: s for s in candidate.skills}
    n_covered = sum(1 for r in operation.required_skills if r.skill_id in skills_map)
    if n_required > 0:
        parts.append(
            f"covers {n_covered}/{n_required} required skill(s) "
            f"(skills contribution {breakdown.skills_score:.2f}/0.40)"
        )
    else:
        parts.append("no specific skills required (full skills credit)")

    # History
    if breakdown.raw_history > 0:
        parts.append(
            f"has relevant assignment history "
            f"(history contribution {breakdown.history_score:.2f}/0.20)"
        )
    else:
        parts.append("no assignment history on this operation")

    # Unmet
    if unmet:
        parts.append(f"unmet requirements: {'; '.join(unmet)}")

    return ". ".join(parts) + "."


def rank_candidates(
    operation: OperationContext,
    candidates: list[CandidateOperator],
    top_n: int = 5,
    evaluation_date: date | None = None,
) -> tuple[list[CandidateRecommendation], list[str]]:
    """Score, rank, and return the top-N candidates.

    Parameters
    ----------
    operation:
        Operation context.
    candidates:
        Pool of candidate operators.
    top_n:
        Maximum number of recommendations to return.
    evaluation_date:
        Reference date for recency. Defaults to today.

    Returns
    -------
    (ranked_recommendations, filtered_out_ids)
    """
    filtered_out: list[str] = []
    scored: list[_ScoredCandidate] = []

    for candidate in candidates:
        result = hard_filter(candidate, operation)
        if not result.eligible:
            filtered_out.append(candidate.operator_id)
            continue

        total, breakdown, unmet = compute_score(candidate, operation, evaluation_date)
        explanation = build_explanation(candidate, operation, breakdown, unmet)
        scored.append(
            _ScoredCandidate(
                operator_id=candidate.operator_id,
                name=candidate.name,
                total_score=total,
                breakdown=breakdown,
                unmet_requirements=unmet,
                explanation=explanation,
            )
        )

    # Sort: descending score, tie-break by operator_id lexicographic ascending
    scored.sort(key=lambda c: (-c.total_score, c.operator_id))

    recommendations: list[CandidateRecommendation] = [
        CandidateRecommendation(
            operator_id=c.operator_id,
            name=c.name,
            rank=i + 1,
            total_score=c.total_score,
            breakdown=c.breakdown,
            unmet_requirements=c.unmet_requirements,
            explanation=c.explanation,
        )
        for i, c in enumerate(scored[:top_n])
    ]

    return recommendations, filtered_out
