from datetime import datetime
from typing import Optional
from pydantic import BaseModel, field_validator


class Task(BaseModel):
    id: Optional[int] = None
    user_id: int
    title: str
    description: Optional[str] = None
    priority: int = 2  # 1=High, 2=Medium, 3=Low
    status: str = "pending"
    due_date: Optional[str] = None
    recurrence_rule: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    @field_validator("priority")
    @classmethod
    def priority_range(cls, v: int) -> int:
        if v not in (1, 2, 3):
            raise ValueError("Priority must be 1, 2, or 3")
        return v

    @field_validator("status")
    @classmethod
    def status_valid(cls, v: str) -> str:
        if v not in ("pending", "done", "deleted"):
            raise ValueError("Status must be pending, done, or deleted")
        return v

    @property
    def priority_label(self) -> str:
        return {1: "High", 2: "Medium", 3: "Low"}.get(self.priority, "Medium")
