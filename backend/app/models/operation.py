from sqlalchemy import Index, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, new_uuid


class Operation(Base):
    __tablename__ = "operations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    code: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    required_skills: Mapped[str | None] = mapped_column(
        Text, nullable=True
    )  # JSON array stored as text
    duration_minutes: Mapped[int | None] = mapped_column(nullable=True)
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)

    # Relationships
    assignments: Mapped[list["Assignment"]] = relationship(  # noqa: F821
        "Assignment", back_populates="operation", cascade="all, delete-orphan"
    )

    __table_args__ = (
        UniqueConstraint("code", name="uq_operations_code"),
        Index("ix_operations_code", "code"),
        Index("ix_operations_name", "name"),
    )
