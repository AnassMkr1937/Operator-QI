from sqlalchemy import Index, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, new_uuid


class Operator(Base):
    __tablename__ = "operators"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    employee_id: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    email: Mapped[str | None] = mapped_column(String(256), nullable=True)
    department: Mapped[str | None] = mapped_column(String(128), nullable=True)
    hire_date: Mapped[str | None] = mapped_column(String(10), nullable=True)  # ISO date string
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)

    # Relationships
    skills: Mapped[list["Skill"]] = relationship(  # noqa: F821
        "Skill", back_populates="operator", cascade="all, delete-orphan"
    )
    assignments: Mapped[list["Assignment"]] = relationship(  # noqa: F821
        "Assignment", back_populates="operator", cascade="all, delete-orphan"
    )

    __table_args__ = (
        UniqueConstraint("employee_id", name="uq_operators_employee_id"),
        Index("ix_operators_employee_id", "employee_id"),
        Index("ix_operators_name", "name"),
    )
