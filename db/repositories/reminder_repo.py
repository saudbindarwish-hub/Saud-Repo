from typing import Optional
from db.connection import get_connection
from models.reminder import Reminder


def create_reminder(reminder: Reminder) -> int:
    conn = get_connection()
    with conn:
        cur = conn.execute(
            "INSERT INTO reminders (user_id, chat_id, message, remind_at, recurrence_rule) VALUES (?, ?, ?, ?, ?)",
            (reminder.user_id, reminder.chat_id, reminder.message, reminder.remind_at, reminder.recurrence_rule),
        )
    reminder_id = cur.lastrowid
    conn.close()
    return reminder_id


def get_reminder_by_id(reminder_id: int) -> Optional[Reminder]:
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM reminders WHERE id = ?",
        (reminder_id,),
    ).fetchone()
    conn.close()
    return Reminder(**dict(row)) if row else None


def get_pending_reminders(user_id: int) -> list[Reminder]:
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM reminders WHERE user_id = ? AND is_fired = 0 ORDER BY remind_at ASC",
        (user_id,),
    ).fetchall()
    conn.close()
    return [Reminder(**dict(row)) for row in rows]


def get_all_pending_reminders() -> list[Reminder]:
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM reminders WHERE is_fired = 0 ORDER BY remind_at ASC",
    ).fetchall()
    conn.close()
    return [Reminder(**dict(row)) for row in rows]


def mark_reminder_fired(reminder_id: int) -> None:
    conn = get_connection()
    with conn:
        conn.execute(
            "UPDATE reminders SET is_fired = 1 WHERE id = ?",
            (reminder_id,),
        )
    conn.close()


def cancel_reminder(reminder_id: int, user_id: int) -> bool:
    conn = get_connection()
    with conn:
        cur = conn.execute(
            "UPDATE reminders SET is_fired = 1 WHERE id = ? AND user_id = ?",
            (reminder_id, user_id),
        )
    conn.close()
    return cur.rowcount > 0
