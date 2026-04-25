from typing import Optional
from pydantic import BaseModel


class Reminder(BaseModel):
    id: Optional[int] = None
    user_id: int
    chat_id: int
    message: str
    remind_at: str  # ISO8601 UTC datetime string
    is_fired: int = 0
    created_at: Optional[str] = None
