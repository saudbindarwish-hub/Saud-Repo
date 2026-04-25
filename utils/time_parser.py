from datetime import datetime, timezone
from typing import Optional
import dateparser


def parse_time(text: str, user_timezone: str = "UTC") -> Optional[datetime]:
    settings = {
        "TIMEZONE": user_timezone,
        "TO_TIMEZONE": "UTC",
        "RETURN_AS_TIMEZONE_AWARE": True,
        "PREFER_DATES_FROM": "future",
    }
    dt = dateparser.parse(text, settings=settings)
    if dt is None:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    if dt <= datetime.now(timezone.utc):
        return None
    return dt


def format_remind_at(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%dT%H:%M:%S")


def friendly_datetime(iso_str: str, user_timezone: str = "UTC") -> str:
    try:
        dt = datetime.fromisoformat(iso_str).replace(tzinfo=timezone.utc)
        import zoneinfo
        tz = zoneinfo.ZoneInfo(user_timezone)
        local = dt.astimezone(tz)
        return local.strftime("%b %d, %Y at %H:%M %Z")
    except Exception:
        return iso_str
