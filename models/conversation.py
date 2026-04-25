from typing import Optional
from pydantic import BaseModel, field_validator


class ConversationMessage(BaseModel):
    id: Optional[int] = None
    user_id: int
    role: str  # 'user' | 'assistant'
    content: str
    created_at: Optional[str] = None

    @field_validator("role")
    @classmethod
    def role_valid(cls, v: str) -> str:
        if v not in ("user", "assistant"):
            raise ValueError("Role must be 'user' or 'assistant'")
        return v
