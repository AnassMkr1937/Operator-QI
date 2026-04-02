"""Pydantic v2 schemas for the Skill domain."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class SkillSnapshotRead(BaseModel):
    """Skill snapshot returned by read endpoints, including decay-adjusted fields."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    operator_id: int
    operation_id: int
    mastery_score: float = Field(..., ge=0, le=100)
    last_practice: datetime | None
    decay_rate: float = Field(..., gt=0, description="Half-life in days")
    total_hours: float = Field(..., ge=0)
    created_at: datetime
    updated_at: datetime


class SkillSnapshotUpdate(BaseModel):
    """Payload for manually adjusting a skill snapshot (supervisor override)."""

    mastery_score: float | None = Field(default=None, ge=0, le=100)
    decay_rate: float | None = Field(default=None, gt=0)
    total_hours: float | None = Field(default=None, ge=0)


class OperationSimilarityRead(BaseModel):
    """Similarity entry between two operations."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    operation_id_a: int
    operation_id_b: int
    similarity: float = Field(..., ge=0, le=1)
