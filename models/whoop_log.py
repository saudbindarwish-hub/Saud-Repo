from typing import Optional
from pydantic import BaseModel, field_validator


class WhoopLog(BaseModel):
    id: Optional[int] = None
    user_id: int
    log_date: str  # YYYY-MM-DD
    recovery_score: Optional[int] = None
    hrv: Optional[float] = None
    rhr: Optional[int] = None
    sleep_hours: Optional[float] = None
    sleep_quality: Optional[int] = None
    strain_score: Optional[float] = None
    notes: Optional[str] = None
    created_at: Optional[str] = None

    @field_validator("recovery_score")
    @classmethod
    def recovery_range(cls, v: Optional[int]) -> Optional[int]:
        if v is not None and not 0 <= v <= 100:
            raise ValueError("Recovery score must be 0–100")
        return v

    @field_validator("sleep_quality")
    @classmethod
    def sleep_quality_range(cls, v: Optional[int]) -> Optional[int]:
        if v is not None and not 0 <= v <= 100:
            raise ValueError("Sleep quality must be 0–100")
        return v

    @field_validator("strain_score")
    @classmethod
    def strain_range(cls, v: Optional[float]) -> Optional[float]:
        if v is not None and not 0 <= v <= 21:
            raise ValueError("Strain score must be 0–21")
        return v
