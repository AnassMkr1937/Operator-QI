"""Quality metric domain model — defect tracking per operator/operation."""

from datetime import date

from sqlalchemy import Column, Date, Float, ForeignKey, Integer, UniqueConstraint
from sqlalchemy.orm import relationship

from app.db.base_class import Base


class QualityMetric(Base):
    """
    Aggregated quality performance for an operator at a specific operation
    over a given time period.

    ``defects_per_100`` is the primary quality KPI: the number of non-conforming
    pieces per 100 produced.  It is used as a quality penalty in the replacement
    scoring engine — operators with elevated defect rates receive a lower score.

    Data is typically imported from the factory MES (Manufacturing Execution System)
    on a weekly or monthly basis.
    """

    __tablename__ = "quality_metrics"
    __table_args__ = (
        UniqueConstraint(
            "operator_id",
            "operation_id",
            "period_start",
            name="uq_quality_operator_operation_period",
        ),
    )

    operator_id = Column(
        ForeignKey("operators.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    operation_id = Column(
        ForeignKey("operations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    defects_per_100 = Column(
        Float,
        nullable=False,
        default=0.0,
        comment="Non-conforming pieces per 100 produced",
    )
    pieces_produced = Column(
        Integer,
        nullable=False,
        default=0,
        comment="Total pieces produced in the period",
    )
    period_start = Column(Date, nullable=False, comment="Start of the measurement period")
    period_end = Column(Date, nullable=False, comment="End of the measurement period")

    # ── Relationships ─────────────────────────────────────────────────────
    operator = relationship("Operator", back_populates="quality_metrics")
    operation = relationship("Operation", back_populates="quality_metrics")

    def __repr__(self) -> str:
        return (
            f"<QualityMetric op={self.operator_id} op_id={self.operation_id} "
            f"dph100={self.defects_per_100:.2f}>"
        )
