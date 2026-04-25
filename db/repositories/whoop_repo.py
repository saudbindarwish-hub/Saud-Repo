from typing import Optional
from db.connection import get_connection
from models.whoop_log import WhoopLog


def upsert_whoop_log(log: WhoopLog) -> None:
    conn = get_connection()
    with conn:
        conn.execute(
            """INSERT INTO whoop_logs
               (user_id, log_date, recovery_score, hrv, rhr, sleep_hours, sleep_quality, strain_score, notes)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
               ON CONFLICT(user_id, log_date) DO UPDATE SET
                 recovery_score = COALESCE(excluded.recovery_score, recovery_score),
                 hrv            = COALESCE(excluded.hrv, hrv),
                 rhr            = COALESCE(excluded.rhr, rhr),
                 sleep_hours    = COALESCE(excluded.sleep_hours, sleep_hours),
                 sleep_quality  = COALESCE(excluded.sleep_quality, sleep_quality),
                 strain_score   = COALESCE(excluded.strain_score, strain_score),
                 notes          = COALESCE(excluded.notes, notes)
            """,
            (
                log.user_id, log.log_date, log.recovery_score, log.hrv,
                log.rhr, log.sleep_hours, log.sleep_quality, log.strain_score, log.notes,
            ),
        )
    conn.close()


def get_today_log(user_id: int, log_date: str) -> Optional[WhoopLog]:
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM whoop_logs WHERE user_id = ? AND log_date = ?",
        (user_id, log_date),
    ).fetchone()
    conn.close()
    return WhoopLog(**dict(row)) if row else None


def get_recent_logs(user_id: int, days: int = 7) -> list[WhoopLog]:
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM whoop_logs WHERE user_id = ? ORDER BY log_date DESC LIMIT ?",
        (user_id, days),
    ).fetchall()
    conn.close()
    return [WhoopLog(**dict(row)) for row in rows]
