"""
Replacement matching engine.

Computes a ranked list of replacement candidates for a given operation.

Scoring formula (all components 0-100 unless noted):
    skill_component  = mastery_score × recency_factor          [0-100]
    quality_penalty  = min(dph100 / target_dph100 × 20, 20)   [0-20]
    adjacency_bonus  = max over neighbors(mastery_n × sim × 0.20)  [0-20]
    final_score      = clamp(skill_component + adjacency_bonus - quality_penalty, 0, 100)

Design goals:
- Target < 200 ms per call (single DB round-trip with joined eager loads)
- Deterministic: same inputs always produce the same ranking
- Explainable: every candidate carries a human-readable `reason` string
"""

import time
from typing import Any

from sqlalchemy import and_, or_, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.logging import get_logger
from app.models.operation import Operation
from app.models.operator import Operator
from app.models.quality import QualityMetric
from app.models.skill import OperationSimilarity, SkillSnapshot
from app.schemas.replacement import ReplacementCandidate, ReplacementResponse
from app.services.skill_decay import compute_recency_factor, days_since

logger = get_logger(__name__)


def _clamp(value: float, lo: float = 0.0, hi: float = 100.0) -> float:
    """Clamp *value* to the inclusive interval [lo, hi]."""
    return max(lo, min(hi, value))


def _get_quality_index(db: Session, operation_id: int) -> dict[int, float]:
    """
    Return a mapping of {operator_id: defects_per_100} for a given operation.

    Uses the most recent quality metric record per operator.
    Returns an empty dict if no quality data exists.
    """
    rows = (
        db.execute(
            select(QualityMetric.operator_id, QualityMetric.defects_per_100)
            .where(QualityMetric.operation_id == operation_id)
            .order_by(QualityMetric.operator_id, QualityMetric.period_end.desc())
        )
        .all()
    )
    # Keep only the most recent record per operator (results are sorted by period_end desc)
    seen: dict[int, float] = {}
    for row in rows:
        if row.operator_id not in seen:
            seen[row.operator_id] = row.defects_per_100
    return seen


def _get_adjacency_index(
    db: Session,
    operation_id: int,
) -> dict[int, list[tuple[int, float]]]:
    """
    For each operator who has skills on operations similar to *operation_id*,
    return a list of (similar_operation_id, similarity_score) tuples.

    Returns {operator_id: [(op_id, similarity), ...]}
    """
    # Find all operations similar to the target
    sim_rows = db.execute(
        select(
            OperationSimilarity.operation_id_a,
            OperationSimilarity.operation_id_b,
            OperationSimilarity.similarity,
        ).where(
            or_(
                OperationSimilarity.operation_id_a == operation_id,
                OperationSimilarity.operation_id_b == operation_id,
            )
        )
    ).all()

    if not sim_rows:
        return {}

    # Build {similar_op_id: similarity}
    similar_ops: dict[int, float] = {}
    for row in sim_rows:
        other_id = row.operation_id_b if row.operation_id_a == operation_id else row.operation_id_a
        similar_ops[other_id] = row.similarity

    if not similar_ops:
        return {}

    # Fetch skill snapshots on those similar operations
    skill_rows = db.execute(
        select(
            SkillSnapshot.operator_id,
            SkillSnapshot.operation_id,
            SkillSnapshot.mastery_score,
            SkillSnapshot.last_practice,
            SkillSnapshot.decay_rate,
        ).where(SkillSnapshot.operation_id.in_(list(similar_ops.keys())))
    ).all()

    adjacency: dict[int, list[tuple[int, float, float]]] = {}
    for row in skill_rows:
        sim = similar_ops.get(row.operation_id, 0.0)
        if row.last_practice:
            recency = compute_recency_factor(row.last_practice, row.decay_rate or 90.0)
            effective = row.mastery_score * recency
        else:
            effective = 0.0
        adjacency.setdefault(row.operator_id, []).append((row.operation_id, sim, effective))

    return adjacency  # type: ignore[return-value]


def compute_replacements(
    db: Session,
    operation_id: int,
    shift: str = "all",
) -> ReplacementResponse:
    """
    Compute ranked replacement candidates for *operation_id*.

    Args:
        db:           SQLAlchemy session.
        operation_id: Primary key of the target ``Operation``.
        shift:        Filter operators by shift label, or ``"all"`` for no filter.

    Returns:
        A ``ReplacementResponse`` with up to ``settings.MAX_REPLACEMENT_CANDIDATES``
        candidates sorted by descending composite score.

    Raises:
        ValueError: if *operation_id* does not exist.
    """
    t_start = time.monotonic()

    # ── 1. Fetch target operation ────────────────────────────────────────
    operation = db.get(Operation, operation_id)
    if operation is None:
        raise ValueError(f"Opération {operation_id} introuvable")

    # ── 2. Fetch present operators (optionally filtered by shift) ────────
    query = select(Operator).where(Operator.status == "present")
    if shift and shift.lower() != "all":
        query = query.where(Operator.shift == shift)
    operators: list[Operator] = list(db.scalars(query).all())

    if not operators:
        logger.warning("matching.no_candidates", operation_id=operation_id, shift=shift)
        return ReplacementResponse(
            operation_id=operation_id,
            operation_name=operation.name,
            shift=shift,
            candidates=[],
            computation_time_ms=0.0,
        )

    operator_ids = [op.id for op in operators]
    operator_map = {op.id: op for op in operators}

    # ── 3. Fetch skill snapshots for these operators on the target op ────
    skill_rows = db.execute(
        select(SkillSnapshot).where(
            and_(
                SkillSnapshot.operation_id == operation_id,
                SkillSnapshot.operator_id.in_(operator_ids),
            )
        )
    ).scalars().all()
    skill_map: dict[int, SkillSnapshot] = {s.operator_id: s for s in skill_rows}

    # ── 4. Fetch quality penalties ────────────────────────────────────────
    quality_index = _get_quality_index(db, operation_id)

    # ── 5. Fetch adjacency bonuses ────────────────────────────────────────
    adjacency_index = _get_adjacency_index(db, operation_id)

    # ── 6. Score each operator ────────────────────────────────────────────
    candidates: list[ReplacementCandidate] = []

    for operator in operators:
        op_id = operator.id
        skill = skill_map.get(op_id)

        # -- Skill component --
        if skill and skill.last_practice:
            recency = compute_recency_factor(skill.last_practice, skill.decay_rate or 90.0)
            mastery = skill.mastery_score
            effective_skill = mastery * recency
            days_inactive = days_since(skill.last_practice)
        else:
            recency = 0.0
            mastery = 0.0
            effective_skill = 0.0
            days_inactive = 9999

        # -- Quality penalty (capped at 20 pts) --
        dph100 = quality_index.get(op_id, 0.0)
        target_dph = settings.TARGET_DEFECTS_PER_100
        quality_penalty = _clamp(
            (dph100 / target_dph) * 20 if target_dph > 0 else 0.0,
            0.0,
            20.0,
        )

        # -- Adjacency bonus (max contribution from most similar neighbor) --
        neighbor_data = adjacency_index.get(op_id, [])
        adjacency_bonus = 0.0
        if neighbor_data:
            # bonus = max(effective_mastery_neighbor × similarity × 0.20)
            adjacency_bonus = max(
                eff_mastery * sim * 0.20 for _, sim, eff_mastery in neighbor_data
            )
            adjacency_bonus = _clamp(adjacency_bonus, 0.0, 20.0)

        # -- Final score --
        final_score = _clamp(effective_skill + adjacency_bonus - quality_penalty)

        # -- Human-readable explanation --
        reason_parts: list[str] = []
        if mastery >= settings.MIN_COMPETENCY_THRESHOLD:
            reason_parts.append(f"Maîtrise de base {mastery:.0f}/100")
        elif mastery > 0:
            reason_parts.append(f"Maîtrise partielle {mastery:.0f}/100")
        else:
            reason_parts.append("Aucune expérience directe")

        if recency > 0:
            reason_parts.append(f"fraîcheur {recency:.0%}")
        if days_inactive < 9999:
            reason_parts.append(f"dernière pratique il y a {days_inactive}j")
        if adjacency_bonus > 0:
            reason_parts.append(f"bonus adjacence +{adjacency_bonus:.1f}pts")
        if quality_penalty > 0:
            reason_parts.append(f"pénalité qualité -{quality_penalty:.1f}pts")

        reason = " | ".join(reason_parts) if reason_parts else "Candidat sans données"

        candidates.append(
            ReplacementCandidate(
                operator_id=op_id,
                matricule=operator.matricule,
                full_name=operator.full_name,
                score=round(final_score, 2),
                mastery_score=round(mastery, 2),
                recency_factor=round(recency, 4),
                quality_penalty=round(quality_penalty, 2),
                adjacency_bonus=round(adjacency_bonus, 2),
                days_since_practice=days_inactive if days_inactive < 9999 else 0,
                reason=reason,
            )
        )

    # ── 7. Sort and limit ─────────────────────────────────────────────────
    candidates.sort(key=lambda c: c.score, reverse=True)
    candidates = candidates[: settings.MAX_REPLACEMENT_CANDIDATES]

    elapsed_ms = (time.monotonic() - t_start) * 1000
    logger.info(
        "matching.completed",
        operation_id=operation_id,
        shift=shift,
        candidates_found=len(candidates),
        elapsed_ms=round(elapsed_ms, 2),
    )

    return ReplacementResponse(
        operation_id=operation_id,
        operation_name=operation.name,
        shift=shift,
        candidates=candidates,
        computation_time_ms=round(elapsed_ms, 2),
    )
