from datetime import datetime

from pydantic import BaseModel, ConfigDict


class OperationBase(BaseModel):
    code: str
    name: str
    description: str | None = None
    required_skills: list[str] | None = None
    duration_minutes: int | None = None
    is_active: bool = True


class OperationCreate(OperationBase):
    pass


class OperationUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    required_skills: list[str] | None = None
    duration_minutes: int | None = None
    is_active: bool | None = None


class OperationRead(OperationBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    created_at: datetime
    updated_at: datetime
