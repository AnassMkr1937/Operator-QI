from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class SkillBase(BaseModel):
    operator_id: str
    name: str
    level: int = Field(default=1, ge=1, le=5)
    certified_at: str | None = None  # ISO date: YYYY-MM-DD


class SkillCreate(SkillBase):
    pass


class SkillUpdate(BaseModel):
    name: str | None = None
    level: int | None = Field(default=None, ge=1, le=5)
    certified_at: str | None = None


class SkillRead(SkillBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    created_at: datetime
    updated_at: datetime
