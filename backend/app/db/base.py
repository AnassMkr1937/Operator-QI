"""
Model registry for Alembic auto-discovery.

Import every ORM model here so that ``Base.metadata`` knows about all tables
before Alembic generates migration scripts.  Adding a new model? Add its
import below.
"""

# Re-export Base so Alembic env.py only needs to import from here
from app.db.base_class import Base  # noqa: F401

# ── Domain models ─────────────────────────────────────────────────────────
from app.models.operator import Operator  # noqa: F401
from app.models.operation import Operation  # noqa: F401
from app.models.assignment import Assignment  # noqa: F401
from app.models.skill import OperationSimilarity, SkillSnapshot  # noqa: F401
from app.models.quality import QualityMetric  # noqa: F401
