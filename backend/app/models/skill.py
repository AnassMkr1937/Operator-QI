"""
Skill-related domain models.

Two models:
- ``SkillSnapshot`` — the pre-computed current skill state for an (operator, operation) pair.
- ``OperationSimilarity`` — an adjacency matrix between operations used for the
  "transfer learning" bonus in the replacement engine.
"""

from sqlalchemy import Column, DateTime, Float, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship

from app.db.base_class import Base


class SkillSnapshot(Base):
    """
    Pre-computed skill state for a single (operator, operation) pair.

    Columns:
        mastery_score   Raw competency score 0-100 built from training hours
                        and historical performance.  Does NOT include decay —
                        decay is applied at query time by the matching engine.
        last_practice   UTC datetime of the most recent assignment to this
                        operation.  Drives exponential skill decay.
        decay_rate      Half-life in days for this operator/operation pair.
                        Defaults to the application-wide setting (90 days).
        total_hours     Cumulative hours ever worked at this operation.
    """

    __tablename__ = "skill_snapshots"
    __table_args__ = (
        UniqueConstraint("operator_id", "operation_id", name="uq_skill_operator_operation"),
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
    mastery_score = Column(
        Float,
        nullable=False,
        default=0.0,
        comment="Raw mastery score 0-100 (before decay)",
    )
    last_practice = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="Datetime of the most recent assignment",
    )
    decay_rate = Column(
        Float,
        nullable=False,
        default=90.0,
        comment="Skill half-life in days",
    )
    total_hours = Column(
        Float,
        nullable=False,
        default=0.0,
        comment="Cumulative hours worked at this operation",
    )

    # ── Relationships ─────────────────────────────────────────────────────
    operator = relationship("Operator", back_populates="skills")
    operation = relationship("Operation", back_populates="skills")

    def __repr__(self) -> str:
        return (
            f"<SkillSnapshot op={self.operator_id} op_id={self.operation_id} "
            f"mastery={self.mastery_score:.1f}>"
        )


class OperationSimilarity(Base):
    """
    Pairwise similarity score between two operations.

    Used by the replacement engine to grant an *adjacency bonus*: if an operator
    is highly skilled at an operation that is structurally similar to the target,
    they receive partial credit even without direct experience.

    ``similarity`` ranges from 0.0 (completely unrelated) to 1.0 (identical).

    The table stores only one direction (a < b) to avoid duplication; the
    service layer handles symmetry lookups.
    """

    __tablename__ = "operation_similarities"
    __table_args__ = (
        UniqueConstraint(
            "operation_id_a",
            "operation_id_b",
            name="uq_similarity_pair",
        ),
    )

    operation_id_a = Column(
        ForeignKey("operations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    operation_id_b = Column(
        ForeignKey("operations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    similarity = Column(
        Float,
        nullable=False,
        comment="Similarity coefficient 0-1 between the two operations",
    )

    # ── Relationships ─────────────────────────────────────────────────────
    operation_a = relationship("Operation", foreign_keys=[operation_id_a])
    operation_b = relationship("Operation", foreign_keys=[operation_id_b])

    def __repr__(self) -> str:
        return (
            f"<OperationSimilarity {self.operation_id_a}<->{self.operation_id_b} "
            f"sim={self.similarity:.2f}>"
        )
