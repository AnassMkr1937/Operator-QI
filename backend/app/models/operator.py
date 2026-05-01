from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Operator(Base):
    __tablename__ = "operators"

    operator_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
    )

    skills: Mapped[list["OperatorSkill"]] = relationship(
        back_populates="operator",
        cascade="all, delete-orphan",
    )
    assignments: Mapped[list["Assignment"]] = relationship(
        back_populates="operator",
        cascade="all, delete-orphan",
    )


class OperatorSkill(Base):
    __tablename__ = "operator_skills"

    operator_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("operators.operator_id", ondelete="CASCADE"),
        primary_key=True,
    )
    skill_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("skills.skill_id", ondelete="CASCADE"),
        primary_key=True,
    )
    proficiency: Mapped[int] = mapped_column(Integer)
    certified: Mapped[bool] = mapped_column(Boolean, default=False)
    last_used_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    operator: Mapped["Operator"] = relationship(back_populates="skills")
    skill: Mapped["Skill"] = relationship(back_populates="operators")


class Assignment(Base):
    __tablename__ = "assignments"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    operator_id: Mapped[str] = mapped_column(
        String(64), ForeignKey("operators.operator_id", ondelete="CASCADE")
    )
    operation_id: Mapped[str] = mapped_column(String(64))
    assignment_date: Mapped[date] = mapped_column(Date)
    shift: Mapped[str] = mapped_column(String(32))
    category: Mapped[str | None] = mapped_column(String(64), nullable=True)

    operator: Mapped["Operator"] = relationship(back_populates="assignments")
