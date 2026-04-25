from sqlalchemy import ForeignKey, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, new_uuid


class Skill(Base):
    __tablename__ = "skills"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    operator_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("operators.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    level: Mapped[int] = mapped_column(Integer, default=1, nullable=False)  # 1-5
    certified_at: Mapped[str | None] = mapped_column(String(10), nullable=True)  # ISO date

    # Relationships
    operator: Mapped["Operator"] = relationship(  # noqa: F821
        "Operator", back_populates="skills"
    )

    __table_args__ = (
        Index("ix_skills_operator_id", "operator_id"),
        Index("ix_skills_name", "name"),
    )
