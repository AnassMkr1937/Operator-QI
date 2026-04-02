"""Assignment domain model — historical record of operator-to-operation placements."""

from datetime import date, datetime

from sqlalchemy import Column, Date, DateTime, Float, ForeignKey, String
from sqlalchemy.orm import relationship

from app.db.base_class import Base


class Assignment(Base):
    """
    Records a single occurrence of an operator working at a specific operation.

    The assignment history is the primary data source for skill computation:
    - ``total_hours`` accumulated per (operator, operation) drives ``mastery_score``
    - ``end_time`` (or last assignment date) determines skill recency

    ``shift_date`` is stored separately so reports can be grouped by calendar day
    independently of the precise start/end timestamps.
    """

    __tablename__ = "assignments"

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
    shift_date = Column(Date, nullable=False, index=True, comment="Calendar date of the shift")
    start_time = Column(DateTime(timezone=True), nullable=True)
    end_time = Column(DateTime(timezone=True), nullable=True)
    duration_hours = Column(
        Float,
        nullable=False,
        default=0.0,
        comment="Hours actually worked at this operation during the assignment",
    )
    shift_label = Column(
        String(20),
        nullable=True,
        comment="Shift label at time of assignment (matin/apres-midi/nuit)",
    )
    notes = Column(String(255), nullable=True)

    # ── Relationships ─────────────────────────────────────────────────────
    operator = relationship("Operator", back_populates="assignments")
    operation = relationship("Operation", back_populates="assignments")

    def __repr__(self) -> str:
        return (
            f"<Assignment id={self.id} operator_id={self.operator_id} "
            f"operation_id={self.operation_id} date={self.shift_date}>"
        )
