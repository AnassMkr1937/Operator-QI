"""Schemas for the smart replacement engine."""

from pydantic import BaseModel, Field


class ReplacementCandidate(BaseModel):
    """
    A single ranked candidate for replacing an operator at a given operation.

    ``score`` is the composite compatibility score (0-100) computed by the
    matching engine, accounting for mastery, recency, quality history and
    adjacency to similar operations.
    """

    operator_id: int
    matricule: str
    full_name: str
    score: float = Field(..., ge=0, le=100, description="Composite compatibility score 0-100")
    mastery_score: float = Field(..., ge=0, le=100, description="Raw mastery before decay")
    recency_factor: float = Field(..., ge=0, le=1, description="Skill freshness factor 0-1")
    quality_penalty: float = Field(..., ge=0, description="Points deducted for defect history")
    adjacency_bonus: float = Field(..., ge=0, description="Points added from similar operations")
    days_since_practice: int = Field(..., ge=0)
    reason: str = Field(..., description="Human-readable explanation of the score")


class ReplacementResponse(BaseModel):
    """
    The full response of the matching endpoint.

    ``computation_time_ms`` is included so the client can detect
    regressions in engine performance.
    """

    operation_id: int
    operation_name: str
    shift: str
    candidates: list[ReplacementCandidate]
    computation_time_ms: float
