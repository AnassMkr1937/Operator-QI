from datetime import datetime

from pydantic import BaseModel, ConfigDict


class OperatorBase(BaseModel):
    employee_id: str
    name: str
    email: str | None = None
    department: str | None = None
    hire_date: str | None = None  # ISO date: YYYY-MM-DD
    is_active: bool = True


class OperatorCreate(OperatorBase):
    pass


class OperatorUpdate(BaseModel):
    name: str | None = None
    email: str | None = None
    department: str | None = None
    hire_date: str | None = None
    is_active: bool | None = None


class OperatorRead(OperatorBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    created_at: datetime
    updated_at: datetime
