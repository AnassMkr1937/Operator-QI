from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict

AssignmentStatus = Literal["pending", "confirmed", "completed", "cancelled"]


class AssignmentBase(BaseModel):
    operator_id: str
    operation_id: str
    scheduled_date: str | None = None  # ISO date: YYYY-MM-DD
    status: AssignmentStatus = "pending"
    notes: str | None = None


class AssignmentCreate(AssignmentBase):
    pass


class AssignmentUpdate(BaseModel):
    scheduled_date: str | None = None
    status: AssignmentStatus | None = None
    notes: str | None = None


class AssignmentRead(AssignmentBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    created_at: datetime
    updated_at: datetime
