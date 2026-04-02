"""
SQLAlchemy declarative base with automatic audit columns.

Every table in the system inherits from ``Base`` and therefore automatically
receives ``id``, ``created_at``, and ``updated_at`` columns without having to
declare them individually.
"""

from datetime import datetime, timezone

from sqlalchemy import DateTime, Integer, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """
    Shared declarative base for all ORM models.

    Columns added to every table:
        id         — auto-incrementing integer primary key
        created_at — UTC timestamp set on INSERT
        updated_at — UTC timestamp updated on every UPDATE via SQLAlchemy event
    """

    # SQLAlchemy 2.x uses __abstract__ on the base itself so that it is not
    # treated as a concrete mapper target.
    __abstract__ = True

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="Row creation timestamp (UTC)",
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
        comment="Last update timestamp (UTC)",
    )
