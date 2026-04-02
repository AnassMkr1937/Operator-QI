"""Operator domain model — represents a production operator."""

from sqlalchemy import Column, Enum as SAEnum, String
from sqlalchemy.orm import relationship

from app.db.base_class import Base


class Operator(Base):
    """
    An industrial production operator.

    The ``matricule`` is anonymized (e.g. ``OP-0042``) for GDPR compliance —
    it must never contain the operator's real name or national ID.

    ``team`` and ``shift`` are used for availability filtering during replacement
    so the system only suggests operators who are on duty.
    """

    __tablename__ = "operators"

    matricule = Column(
        String(20),
        unique=True,
        index=True,
        nullable=False,
        comment="Anonymized operator identifier (GDPR)",
    )
    full_name = Column(String(100), nullable=False)
    team = Column(
        String(50),
        index=True,
        nullable=False,
        comment="Production team (A/B/C/D)",
    )
    shift = Column(
        String(20),
        nullable=False,
        comment="Work shift (matin/apres-midi/nuit)",
    )
    status = Column(
        SAEnum("present", "absent", "conge", name="operator_status"),
        default="present",
        nullable=False,
        comment="Current attendance status",
    )

    # ── Relationships ─────────────────────────────────────────────────────
    assignments = relationship("Assignment", back_populates="operator", lazy="select")
    skills = relationship("SkillSnapshot", back_populates="operator", lazy="select")
    quality_metrics = relationship("QualityMetric", back_populates="operator", lazy="select")

    def __repr__(self) -> str:
        return f"<Operator id={self.id} matricule={self.matricule!r} team={self.team!r}>"
