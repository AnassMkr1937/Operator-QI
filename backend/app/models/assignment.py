from sqlalchemy import ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, new_uuid

ASSIGNMENT_STATUSES = ("pending", "confirmed", "completed", "cancelled")


class Assignment(Base):
    __tablename__ = "assignments"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    operator_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("operators.id", ondelete="CASCADE"), nullable=False
    )
    operation_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("operations.id", ondelete="CASCADE"), nullable=False
    )
    scheduled_date: Mapped[str | None] = mapped_column(String(10), nullable=True)  # ISO date
    status: Mapped[str] = mapped_column(String(32), default="pending", nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    operator: Mapped["Operator"] = relationship(  # noqa: F821
        "Operator", back_populates="assignments"
    )
    operation: Mapped["Operation"] = relationship(  # noqa: F821
        "Operation", back_populates="assignments"
    )

    __table_args__ = (
        Index("ix_assignments_operator_id", "operator_id"),
        Index("ix_assignments_operation_id", "operation_id"),
        Index("ix_assignments_status", "status"),
    )
