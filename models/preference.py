from typing import Optional
from pydantic import BaseModel


class UserPreference(BaseModel):
    id: Optional[int] = None
    user_id: int
    timezone: str = "UTC"
    daily_plan_time: str = "08:00"
    fitness_goal: str = "general"
    supplements: str = "[]"  # JSON array stored as string
    wake_time: str = "07:00"
    sleep_time: str = "23:00"
    preferred_name: Optional[str] = None
    updated_at: Optional[str] = None
