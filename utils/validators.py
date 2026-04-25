import re
from zoneinfo import available_timezones


def validate_task_title(text: str) -> str:
    text = text.strip()
    if not text:
        raise ValueError("Task title cannot be empty.")
    if len(text) > 500:
        raise ValueError("Task title must be 500 characters or fewer.")
    return text


def validate_task_description(text: str) -> str:
    text = text.strip()
    if len(text) > 2000:
        raise ValueError("Description must be 2000 characters or fewer.")
    return text


def validate_priority(text: str) -> int:
    try:
        p = int(text.strip())
    except ValueError:
        raise ValueError("Priority must be 1, 2, or 3.")
    if p not in (1, 2, 3):
        raise ValueError("Priority must be 1 (High), 2 (Medium), or 3 (Low).")
    return p


def validate_task_id(text: str) -> int:
    try:
        tid = int(text.strip())
    except ValueError:
        raise ValueError("Task ID must be a number.")
    if tid <= 0:
        raise ValueError("Task ID must be a positive number.")
    return tid


def validate_recovery_score(text: str) -> int:
    try:
        score = int(text.strip())
    except ValueError:
        raise ValueError("Recovery score must be a whole number (0–100).")
    if not 0 <= score <= 100:
        raise ValueError("Recovery score must be between 0 and 100.")
    return score


def validate_hrv(text: str) -> float:
    try:
        hrv = float(text.strip())
    except ValueError:
        raise ValueError("HRV must be a number (e.g. 45.2).")
    if hrv <= 0 or hrv > 300:
        raise ValueError("HRV must be between 1 and 300 ms.")
    return hrv


def validate_rhr(text: str) -> int:
    try:
        rhr = int(text.strip())
    except ValueError:
        raise ValueError("Resting heart rate must be a whole number.")
    if not 30 <= rhr <= 200:
        raise ValueError("Resting heart rate must be between 30 and 200 bpm.")
    return rhr


def validate_sleep_hours(text: str) -> float:
    try:
        hours = float(text.strip())
    except ValueError:
        raise ValueError("Sleep hours must be a number (e.g. 7.5).")
    if not 0 <= hours <= 24:
        raise ValueError("Sleep hours must be between 0 and 24.")
    return hours


def validate_sleep_quality(text: str) -> int:
    try:
        q = int(text.strip())
    except ValueError:
        raise ValueError("Sleep quality must be a whole number (0–100).")
    if not 0 <= q <= 100:
        raise ValueError("Sleep quality must be between 0 and 100.")
    return q


def validate_strain_score(text: str) -> float:
    try:
        s = float(text.strip())
    except ValueError:
        raise ValueError("Strain score must be a number (e.g. 12.5).")
    if not 0 <= s <= 21:
        raise ValueError("Strain score must be between 0 and 21.")
    return s


def validate_notes(text: str) -> str:
    text = text.strip()
    if len(text) > 500:
        raise ValueError("Notes must be 500 characters or fewer.")
    return text


def validate_reminder_message(text: str) -> str:
    text = text.strip()
    if not text:
        raise ValueError("Reminder message cannot be empty.")
    if len(text) > 1000:
        raise ValueError("Reminder message must be 1000 characters or fewer.")
    return text


def validate_timezone(text: str) -> str:
    tz = text.strip()
    if tz not in available_timezones():
        raise ValueError(f"Unknown timezone: {tz}. Use a valid IANA timezone like 'America/New_York'.")
    return tz


def validate_plan_time(text: str) -> str:
    text = text.strip()
    if not re.match(r"^\d{2}:\d{2}$", text):
        raise ValueError("Plan time must be in HH:MM format (e.g. 08:00).")
    h, m = int(text[:2]), int(text[3:])
    if not (0 <= h <= 23 and 0 <= m <= 59):
        raise ValueError("Plan time must be a valid 24-hour time.")
    return text


def validate_fitness_goal(text: str) -> str:
    valid = ("strength", "endurance", "weight_loss", "general")
    goal = text.strip().lower()
    if goal not in valid:
        raise ValueError(f"Fitness goal must be one of: {', '.join(valid)}.")
    return goal


def validate_supplement_name(text: str) -> str:
    text = text.strip()
    if not text or len(text) > 100:
        raise ValueError("Supplement name must be 1–100 characters.")
    return text


def validate_preferred_name(text: str) -> str:
    text = text.strip()
    if not text or len(text) > 50:
        raise ValueError("Name must be 1–50 characters.")
    return text
