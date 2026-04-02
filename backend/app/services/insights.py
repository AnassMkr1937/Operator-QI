"""
Insights service — strategic analytics for workforce resilience.

Provides three key analyses:
1. **Fragile operations**: workstations with too few qualified operators
2. **Learning paths**: recommended training assignments based on skill adjacency
3. **Polyvalence index**: a macro KPI measuring workforce flexibility
"""

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.logging import get_logger
from app.models.operation import Operation
from app.models.operator import Operator
from app.models.skill import OperationSimilarity, SkillSnapshot
from app.schemas.insights import InsightsResponse, LearningPath, OperationFragility
from app.services.skill_decay import compute_recency_factor, days_since

logger = get_logger(__name__)

# Risk thresholds (qualified operators per operation)
_RISK_LEVELS = [
    (0, "CRITIQUE"),
    (1, "CRITIQUE"),
    (2, "ÉLEVÉ"),
    (3, "MOYEN"),
]


def _effective_mastery(snapshot: SkillSnapshot) -> float:
    """Return effective (decay-adjusted) mastery for a snapshot."""
    if not snapshot.last_practice:
        return 0.0
    recency = compute_recency_factor(snapshot.last_practice, snapshot.decay_rate or 90.0)
    return snapshot.mastery_score * recency


def _risk_label(count: int) -> str:
    """Map qualified operator count to a risk level string."""
    for threshold, label in _RISK_LEVELS:
        if count <= threshold:
            return label
    return "OK"


def get_fragile_operations(db: Session) -> list[OperationFragility]:
    """
    Identify operations with dangerously few qualified operators.

    An operator is "qualified" if their effective (decay-adjusted) mastery score
    exceeds ``settings.MIN_COMPETENCY_THRESHOLD``.

    Returns a list of ``OperationFragility`` objects sorted by risk (most critical first),
    then by qualified_operators_count ascending.
    """
    operations: list[Operation] = list(db.scalars(select(Operation)).all())
    results: list[OperationFragility] = []

    for op in operations:
        # Fetch all skill snapshots for this operation
        snapshots: list[SkillSnapshot] = list(
            db.scalars(
                select(SkillSnapshot).where(SkillSnapshot.operation_id == op.id)
            ).all()
        )

        qualified = []
        for snap in snapshots:
            eff = _effective_mastery(snap)
            if eff >= settings.MIN_COMPETENCY_THRESHOLD:
                operator = db.get(Operator, snap.operator_id)
                if operator:
                    qualified.append(
                        {
                            "operator_id": operator.id,
                            "matricule": operator.matricule,
                            "effective_mastery": round(eff, 2),
                            "days_since_practice": days_since(snap.last_practice)
                            if snap.last_practice
                            else None,
                        }
                    )

        risk = _risk_label(len(qualified))
        # Only include non-OK operations in the response (configurable)
        results.append(
            OperationFragility(
                operation_id=op.id,
                operation_name=op.name,
                line=op.line,
                criticality=op.criticality,
                qualified_operators_count=len(qualified),
                operators_above_threshold=qualified,
                risk_level=risk,
            )
        )

    # Sort: most critical operations first, then by qualified count
    results.sort(
        key=lambda r: (
            0 if r.risk_level == "CRITIQUE" else 1 if r.risk_level == "ÉLEVÉ" else 2 if r.risk_level == "MOYEN" else 3,
            r.qualified_operators_count,
            -r.criticality,
        )
    )
    return results


def get_learning_paths(db: Session) -> list[LearningPath]:
    """
    Recommend training assignments based on skill adjacency.

    Logic:
    - For every (operator, operation) pair where the operator does NOT yet have
      effective mastery ≥ ``settings.MIN_COMPETENCY_THRESHOLD`` on the target operation,
    - but DOES have effective mastery ≥ 70% on at least one operation that is
      similar (similarity ≥ 0.5) to the target,
    - generate a learning path recommendation.

    ``estimated_weeks_to_qualify`` is estimated assuming ~8 hours/week of practice
    and the ``mastery_from_hours`` learning curve.
    """
    ADJACENT_THRESHOLD = 70.0
    SIMILARITY_THRESHOLD = 0.5
    HOURS_PER_WEEK = 8.0
    SATURATION_HOURS = 200.0

    # Fetch similarity pairs above threshold
    sim_rows = db.execute(
        select(
            OperationSimilarity.operation_id_a,
            OperationSimilarity.operation_id_b,
            OperationSimilarity.similarity,
        ).where(OperationSimilarity.similarity >= SIMILARITY_THRESHOLD)
    ).all()

    if not sim_rows:
        return []

    # Build adjacency map: {op_id: [(similar_op_id, similarity), ...]}
    adjacency: dict[int, list[tuple[int, float]]] = {}
    for row in sim_rows:
        adjacency.setdefault(row.operation_id_a, []).append(
            (row.operation_id_b, row.similarity)
        )
        adjacency.setdefault(row.operation_id_b, []).append(
            (row.operation_id_a, row.similarity)
        )

    # Fetch all skill snapshots indexed by (operator_id, operation_id)
    all_skills: list[SkillSnapshot] = list(db.scalars(select(SkillSnapshot)).all())
    skill_index: dict[tuple[int, int], float] = {}
    for snap in all_skills:
        eff = _effective_mastery(snap)
        skill_index[(snap.operator_id, snap.operation_id)] = eff

    operators: list[Operator] = list(db.scalars(select(Operator)).all())
    operations: list[Operation] = list(db.scalars(select(Operation)).all())
    op_map = {op.id: op for op in operations}

    paths: list[LearningPath] = []

    for operator in operators:
        for target_op in operations:
            target_mastery = skill_index.get((operator.id, target_op.id), 0.0)
            # Skip if already qualified
            if target_mastery >= settings.MIN_COMPETENCY_THRESHOLD:
                continue

            # Check if operator is skilled on a similar operation
            neighbors = adjacency.get(target_op.id, [])
            best_adjacent_score = 0.0
            for similar_op_id, similarity in neighbors:
                adjacent_mastery = skill_index.get((operator.id, similar_op_id), 0.0)
                if adjacent_mastery >= ADJACENT_THRESHOLD:
                    weighted = adjacent_mastery * similarity
                    if weighted > best_adjacent_score:
                        best_adjacent_score = weighted

            if best_adjacent_score < ADJACENT_THRESHOLD * SIMILARITY_THRESHOLD:
                continue  # Not enough adjacent skill to justify recommendation

            # Estimate weeks to qualify using a simplified learning model
            # Assume transfer bonus: start at 20% of saturation hours due to adjacent skills
            transfer_hours = (best_adjacent_score / 100.0) * 0.3 * SATURATION_HOURS
            hours_needed = max(0.0, SATURATION_HOURS * 0.6 - transfer_hours)
            estimated_weeks = round(hours_needed / HOURS_PER_WEEK, 1)

            # Priority based on operation criticality and hours needed
            if target_op.criticality >= 4 and estimated_weeks <= 10:
                priority = "HIGH"
            elif target_op.criticality >= 3 or estimated_weeks <= 16:
                priority = "MEDIUM"
            else:
                priority = "LOW"

            paths.append(
                LearningPath(
                    operator_id=operator.id,
                    operator_name=operator.full_name,
                    target_operation_id=target_op.id,
                    target_operation_name=target_op.name,
                    estimated_weeks_to_qualify=estimated_weeks,
                    current_adjacent_score=round(best_adjacent_score, 2),
                    recommended_priority=priority,
                )
            )

    # Sort by priority then by estimated weeks
    priority_order = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}
    paths.sort(key=lambda p: (priority_order.get(p.recommended_priority, 9), p.estimated_weeks_to_qualify))
    return paths


def compute_polyvalence_index(db: Session) -> float:
    """
    Compute the workforce polyvalence index.

    Definition: the average number of operations per operator for which the
    operator's effective mastery exceeds ``settings.MIN_COMPETENCY_THRESHOLD``.

    A higher index means a more flexible, resilient workforce.
    Returns 0.0 if no operators exist.
    """
    operators: list[Operator] = list(db.scalars(select(Operator)).all())
    if not operators:
        return 0.0

    total_qualified_ops = 0
    for operator in operators:
        snapshots: list[SkillSnapshot] = list(
            db.scalars(
                select(SkillSnapshot).where(SkillSnapshot.operator_id == operator.id)
            ).all()
        )
        qualified_count = sum(
            1
            for snap in snapshots
            if _effective_mastery(snap) >= settings.MIN_COMPETENCY_THRESHOLD
        )
        total_qualified_ops += qualified_count

    return round(total_qualified_ops / len(operators), 2)


def get_full_insights(db: Session) -> InsightsResponse:
    """
    Compute and return the complete insights payload.

    This is the aggregation function called by the ``/insights`` endpoint.
    All three analyses run sequentially and their results are bundled together.
    """
    logger.info("insights.computing")

    fragile = get_fragile_operations(db)
    paths = get_learning_paths(db)
    poly = compute_polyvalence_index(db)
    total_operators = db.scalar(select(func.count(Operator.id))) or 0

    logger.info(
        "insights.computed",
        fragile_count=len(fragile),
        learning_paths=len(paths),
        polyvalence=poly,
    )

    return InsightsResponse(
        fragile_operations=fragile,
        learning_paths=paths,
        total_operators=total_operators,
        polyvalence_index=poly,
    )
