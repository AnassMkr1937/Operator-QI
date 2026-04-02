"""
Models package — re-exports all ORM models.

Importing from ``app.models`` is the canonical way to access any model class.
Alembic and ``app.db.base`` also import from here for metadata discovery.
"""

from app.models.assignment import Assignment
from app.models.operation import Operation
from app.models.operator import Operator
from app.models.quality import QualityMetric
from app.models.skill import OperationSimilarity, SkillSnapshot

__all__ = [
    "Operator",
    "Operation",
    "Assignment",
    "SkillSnapshot",
    "OperationSimilarity",
    "QualityMetric",
]
