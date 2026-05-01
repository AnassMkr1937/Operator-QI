"""API router for operator recommendation endpoints (v1)."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from app.schemas.recommendation import (
    RecommendationRequest,
    RecommendationResponse,
    ScorePreviewRequest,
    ScorePreviewResponse,
)
from app.core.rate_limit import limiter
from app.services.matching import (
    build_explanation,
    compute_score,
    hard_filter,
    rank_candidates,
)
from app.services.auth import require_roles

router = APIRouter(prefix="/api/v1/recommendations", tags=["recommendations"])


@router.post(
    "/operators",
    response_model=RecommendationResponse,
    summary="Rank operator candidates for an operation",
    description=(
        "Accepts an operation context and a pool of candidate operators. "
        "Applies hard filters (inactive, conflicting assignment, missing mandatory skill) "
        "then returns the top-N ranked candidates with a full score breakdown."
    ),
    dependencies=[Depends(require_roles("admin", "manager"))],
)
@limiter.limit("30/minute")
def recommend_operators(body: RecommendationRequest) -> RecommendationResponse:
    recommendations, filtered_out = rank_candidates(
        operation=body.operation,
        candidates=body.candidates,
        top_n=body.top_n,
    )
    n_eligible = len(body.candidates) - len(filtered_out)
    return RecommendationResponse(
        recommendations=recommendations,
        total_eligible=n_eligible,
        total_candidates=len(body.candidates),
        operation_id=body.operation.operation_id,
        filtered_out=filtered_out,
    )


@router.post(
    "/preview",
    response_model=ScorePreviewResponse,
    summary="Preview score for a single operator",
    description=(
        "Evaluates a single operator against an operation context and returns "
        "the full score breakdown without persisting anything. "
        "Useful for debugging or UI previews."
    ),
    dependencies=[Depends(require_roles("admin", "manager"))],
)
@limiter.limit("30/minute")
def preview_score(body: ScorePreviewRequest) -> ScorePreviewResponse:
    filter_result = hard_filter(body.candidate, body.operation)

    if not filter_result.eligible:
        return ScorePreviewResponse(
            operator_id=body.candidate.operator_id,
            eligible=False,
            filter_reason=filter_result.reason,
        )

    total, breakdown, unmet = compute_score(body.candidate, body.operation)
    explanation = build_explanation(body.candidate, body.operation, breakdown, unmet)

    return ScorePreviewResponse(
        operator_id=body.candidate.operator_id,
        eligible=True,
        filter_reason=None,
        total_score=total,
        breakdown=breakdown,
        unmet_requirements=unmet,
        explanation=explanation,
    )
