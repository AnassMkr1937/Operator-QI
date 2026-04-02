"""Operation (workstation) domain model."""

from sqlalchemy import Column, Float, Integer, String
from sqlalchemy.orm import relationship

from app.db.base_class import Base


class Operation(Base):
    """
    A workstation / manufacturing operation on the production line.

    ``criticality`` encodes business priority for replacement decisions:
    - 1 = low impact (buffers exist, easily substituted)
    - 3 = standard (default)
    - 5 = critical bottleneck (line stops if unmanned)

    ``nominal_cycle_time_s`` is the designed takt time in seconds; it is used
    to detect performance anomalies when an operator's measured cycle time
    diverges from the nominal.
    """

    __tablename__ = "operations"

    code = Column(String(20), unique=True, index=True, nullable=False)
    name = Column(String(100), nullable=False)
    line = Column(
        String(50),
        index=True,
        nullable=False,
        comment="Production line identifier",
    )
    criticality = Column(
        Integer,
        default=3,
        nullable=False,
        comment="Criticality 1 (low) → 5 (critical bottleneck)",
    )
    nominal_cycle_time_s = Column(Float, comment="Nominal cycle time in seconds")

    # ── Relationships ─────────────────────────────────────────────────────
    assignments = relationship("Assignment", back_populates="operation", lazy="select")
    skills = relationship("SkillSnapshot", back_populates="operation", lazy="select")
    quality_metrics = relationship("QualityMetric", back_populates="operation", lazy="select")

    def __repr__(self) -> str:
        return f"<Operation id={self.id} code={self.code!r} line={self.line!r}>"
