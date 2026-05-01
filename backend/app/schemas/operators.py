from __future__ import annotations

from datetime import date
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class OperatorSkillPayload(BaseModel):
    skill_id: str = Field(..., description="Skill identifier")
    proficiency: int = Field(..., ge=1, le=5)
    certified: bool = Field(default=False)
    last_used_date: date | None = None


class AssignmentPayload(BaseModel):
    operation_id: str
    assignment_date: date
    shift: Literal["morning", "afternoon", "night"]
    category: str | None = None


class OperatorCreate(BaseModel):
    operator_id: str
    name: str
    is_active: bool = True
    skills: list[OperatorSkillPayload] = Field(default_factory=list)
    assignments: list[AssignmentPayload] = Field(default_factory=list)


class OperatorUpdate(BaseModel):
    name: str | None = None
    is_active: bool | None = None
    skills: list[OperatorSkillPayload] | None = None
    assignments: list[AssignmentPayload] | None = None


class OperatorSkillResponse(OperatorSkillPayload):
    model_config = ConfigDict(from_attributes=True)


class AssignmentResponse(AssignmentPayload):
    model_config = ConfigDict(from_attributes=True)


class OperatorResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    operator_id: str
    name: str
    is_active: bool
    skills: list[OperatorSkillResponse] = Field(default_factory=list)
    assignments: list[AssignmentResponse] = Field(default_factory=list)


class OperatorListResponse(BaseModel):
    items: list[OperatorResponse]
    total: int
