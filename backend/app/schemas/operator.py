"""Pydantic v2 schemas for the Operator domain."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class OperatorBase(BaseModel):
    """Fields shared between create and update."""

    matricule: str = Field(..., max_length=20, description="Anonymized operator ID (GDPR)")
    full_name: str = Field(..., max_length=100)
    team: str = Field(..., max_length=50, description="Production team (A/B/C/D)")
    shift: str = Field(..., max_length=20, description="matin | apres-midi | nuit")
    status: str = Field(default="present", description="present | absent | conge")


class OperatorCreate(OperatorBase):
    """Payload for POST /operators."""

    pass


class OperatorUpdate(BaseModel):
    """Payload for PUT /operators/{id} — all fields optional."""

    full_name: str | None = Field(default=None, max_length=100)
    team: str | None = Field(default=None, max_length=50)
    shift: str | None = Field(default=None, max_length=20)
    status: str | None = None


class OperatorRead(OperatorBase):
    """Full operator representation returned by GET endpoints."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime


class OperatorListResponse(BaseModel):
    """Paginated list response for operators."""

    total: int
    page: int
    page_size: int
    items: list[OperatorRead]
