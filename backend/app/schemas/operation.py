"""Pydantic v2 schemas for the Operation domain."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class OperationBase(BaseModel):
    """Fields shared between create and update."""

    code: str = Field(..., max_length=20, description="Unique operation code (e.g. OP-A-001)")
    name: str = Field(..., max_length=100)
    line: str = Field(..., max_length=50, description="Production line identifier")
    criticality: int = Field(default=3, ge=1, le=5, description="Criticality 1 (low) → 5 (critical)")
    nominal_cycle_time_s: float | None = Field(
        default=None, gt=0, description="Nominal takt time in seconds"
    )


class OperationCreate(OperationBase):
    """Payload for POST /operations."""

    pass


class OperationUpdate(BaseModel):
    """Payload for PUT /operations/{id} — all fields optional."""

    name: str | None = Field(default=None, max_length=100)
    line: str | None = Field(default=None, max_length=50)
    criticality: int | None = Field(default=None, ge=1, le=5)
    nominal_cycle_time_s: float | None = Field(default=None, gt=0)


class OperationRead(OperationBase):
    """Full operation representation returned by GET endpoints."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime


class OperationListResponse(BaseModel):
    """Paginated list response for operations."""

    total: int
    page: int
    page_size: int
    items: list[OperationRead]
