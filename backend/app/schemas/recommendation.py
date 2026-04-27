"""Pydantic schemas for the operator recommendation / matching API (v1)."""

from __future__ import annotations

from datetime import date
from typing import Literal

from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# Sub-models shared between request and response
# ---------------------------------------------------------------------------


class RequiredSkill(BaseModel):
    """A skill requirement declared by the operation."""

    skill_id: str = Field(..., description="Unique identifier of the required skill")
    min_proficiency: int = Field(
        default=1,
        ge=1,
        le=5,
        description="Minimum acceptable proficiency level (1–5)",
    )
    mandatory: bool = Field(
        default=True,
        description="If True, operators missing this skill are hard-filtered out",
    )


class OperationContext(BaseModel):
    """Description of the operation / assignment need to fill."""

    operation_id: str = Field(..., description="Unique identifier of the operation")
    name: str = Field(..., description="Human-readable operation name")
    required_skills: list[RequiredSkill] = Field(
        default_factory=list,
        description="Skills required to perform this operation",
    )
    assignment_date: date = Field(..., description="Date of the assignment (ISO 8601)")
    shift: Literal["morning", "afternoon", "night"] = Field(
        ..., description="Shift slot: morning | afternoon | night"
    )
    category: str | None = Field(
        default=None,
        description="Optional operation category used for history similarity",
    )


class OperatorSkill(BaseModel):
    """A skill possessed by a candidate operator."""

    skill_id: str = Field(..., description="Skill identifier")
    proficiency: int = Field(
        ..., ge=1, le=5, description="Current proficiency level (1–5)"
    )
    certified: bool = Field(
        default=False, description="Whether the operator holds a formal certification"
    )
    last_used_date: date | None = Field(
        default=None,
        description="Most recent date the skill was actively used",
    )


class PastAssignment(BaseModel):
    """A historical or current assignment of the operator."""

    operation_id: str = Field(..., description="Operation that was/is assigned")
    assignment_date: date = Field(..., description="Date of the assignment")
    shift: Literal["morning", "afternoon", "night"] = Field(
        ..., description="Shift of the assignment"
    )
    category: str | None = Field(
        default=None,
        description="Optional operation category (used for similarity signals)",
    )


class CandidateOperator(BaseModel):
    """A candidate operator to be scored against an operation."""

    operator_id: str = Field(..., description="Unique operator identifier")
    name: str = Field(..., description="Operator full name")
    is_active: bool = Field(default=True, description="Whether the operator is active")
    skills: list[OperatorSkill] = Field(
        default_factory=list, description="Skills held by this operator"
    )
    assignments: list[PastAssignment] = Field(
        default_factory=list,
        description="Past and current assignments (used for history + conflict detection)",
    )


# ---------------------------------------------------------------------------
# Request schemas
# ---------------------------------------------------------------------------


class RecommendationRequest(BaseModel):
    """Body for POST /api/v1/recommendations/operators."""

    operation: OperationContext = Field(
        ..., description="Operation context describing what needs to be filled"
    )
    candidates: list[CandidateOperator] = Field(
        ..., min_length=1, description="Pool of candidate operators to rank"
    )
    top_n: int = Field(
        default=5,
        ge=1,
        le=100,
        description="Maximum number of recommendations to return",
    )


class ScorePreviewRequest(BaseModel):
    """Body for POST /api/v1/recommendations/preview — single-operator score preview."""

    operation: OperationContext = Field(..., description="Operation context")
    candidate: CandidateOperator = Field(..., description="Single operator to evaluate")


# ---------------------------------------------------------------------------
# Response schemas
# ---------------------------------------------------------------------------


class ScoreBreakdown(BaseModel):
    """Machine-readable score breakdown for a single candidate."""

    # Weighted contributions (sum = total_score)
    skills_score: float = Field(
        ..., description="Weighted skills contribution (weight 0.40)"
    )
    availability_score: float = Field(
        ..., description="Weighted availability contribution (weight 0.30)"
    )
    history_score: float = Field(
        ..., description="Weighted history contribution (weight 0.20)"
    )
    experience_score: float = Field(
        ..., description="Weighted experience contribution (weight 0.10)"
    )
    # Raw (un-weighted) component values [0..1]
    raw_skills: float = Field(
        ..., description="Raw skills component before weighting [0..1]"
    )
    raw_availability: float = Field(
        ..., description="Raw availability component before weighting [0..1]"
    )
    raw_history: float = Field(
        ..., description="Raw history component before weighting [0..1]"
    )
    raw_experience: float = Field(
        ..., description="Raw experience component before weighting [0..1]"
    )


class CandidateRecommendation(BaseModel):
    """Ranked recommendation entry for a single candidate."""

    operator_id: str
    name: str
    rank: int = Field(..., description="1-based rank among eligible candidates")
    total_score: float = Field(..., description="Composite score [0..1]")
    breakdown: ScoreBreakdown
    unmet_requirements: list[str] = Field(
        default_factory=list,
        description="List of requirements the operator does not fully satisfy",
    )
    explanation: str = Field(
        ..., description="Human-readable explanation of the score"
    )


class RecommendationResponse(BaseModel):
    """Response for POST /api/v1/recommendations/operators."""

    recommendations: list[CandidateRecommendation] = Field(
        ..., description="Top-N ranked eligible candidates"
    )
    total_eligible: int = Field(
        ..., description="Total operators that passed hard filters"
    )
    total_candidates: int = Field(
        ..., description="Total operators provided as input"
    )
    operation_id: str = Field(
        ..., description="Echo of the requested operation_id"
    )
    filtered_out: list[str] = Field(
        default_factory=list,
        description="operator_ids excluded by hard filters",
    )


class ScorePreviewResponse(BaseModel):
    """Response for POST /api/v1/recommendations/preview."""

    operator_id: str
    eligible: bool = Field(..., description="Whether the operator passed hard filters")
    filter_reason: str | None = Field(
        default=None, description="Reason for hard-filter exclusion, if any"
    )
    total_score: float | None = Field(
        default=None, description="Composite score (None if filtered out)"
    )
    breakdown: ScoreBreakdown | None = Field(
        default=None, description="Score breakdown (None if filtered out)"
    )
    unmet_requirements: list[str] = Field(
        default_factory=list,
        description="Non-blocking requirements the operator does not fully satisfy",
    )
    explanation: str | None = Field(
        default=None,
        description="Human-readable explanation (None if filtered out)",
    )
