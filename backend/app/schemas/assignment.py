"""Pydantic v2 schemas for the Assignment domain."""

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field


class AssignmentCreate(BaseModel):
    """Payload for POST /assignments."""

    operator_id: int = Field(..., gt=0)
    operation_id: int = Field(..., gt=0)
    shift_date: date
    start_time: datetime | None = None
    end_time: datetime | None = None
    duration_hours: float = Field(default=0.0, ge=0)
    shift_label: str | None = Field(default=None, max_length=20)
    notes: str | None = Field(default=None, max_length=255)


class AssignmentRead(BaseModel):
    """Full assignment representation returned by GET endpoints."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    operator_id: int
    operation_id: int
    shift_date: date
    start_time: datetime | None
    end_time: datetime | None
    duration_hours: float
    shift_label: str | None
    notes: str | None
    created_at: datetime
    updated_at: datetime


class AssignmentListResponse(BaseModel):
    """Paginated list response for assignments."""

    total: int
    page: int
    page_size: int
    items: list[AssignmentRead]
