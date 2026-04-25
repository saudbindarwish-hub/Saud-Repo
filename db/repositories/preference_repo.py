from typing import Optional
from db.connection import get_connection
from models.preference import UserPreference


def get_or_create_preferences(user_id: int) -> UserPreference:
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM user_preferences WHERE user_id = ?",
        (user_id,),
    ).fetchone()
    if row:
        conn.close()
        return UserPreference(**dict(row))
    with conn:
        conn.execute(
            "INSERT INTO user_preferences (user_id) VALUES (?)",
            (user_id,),
        )
    row = conn.execute(
        "SELECT * FROM user_preferences WHERE user_id = ?",
        (user_id,),
    ).fetchone()
    conn.close()
    return UserPreference(**dict(row))


_FIELD_TO_SQL: dict[str, str] = {
    "timezone":        "UPDATE user_preferences SET timezone = ?, updated_at = datetime('now') WHERE user_id = ?",
    "daily_plan_time": "UPDATE user_preferences SET daily_plan_time = ?, updated_at = datetime('now') WHERE user_id = ?",
    "fitness_goal":    "UPDATE user_preferences SET fitness_goal = ?, updated_at = datetime('now') WHERE user_id = ?",
    "supplements":     "UPDATE user_preferences SET supplements = ?, updated_at = datetime('now') WHERE user_id = ?",
    "wake_time":       "UPDATE user_preferences SET wake_time = ?, updated_at = datetime('now') WHERE user_id = ?",
    "sleep_time":      "UPDATE user_preferences SET sleep_time = ?, updated_at = datetime('now') WHERE user_id = ?",
    "preferred_name":  "UPDATE user_preferences SET preferred_name = ?, updated_at = datetime('now') WHERE user_id = ?",
}


def update_preference(user_id: int, field: str, value: str) -> None:
    sql = _FIELD_TO_SQL.get(field)
    if sql is None:
        raise ValueError(f"Unknown preference field: {field}")
    conn = get_connection()
    with conn:
        conn.execute(sql, (value, user_id))
    conn.close()
