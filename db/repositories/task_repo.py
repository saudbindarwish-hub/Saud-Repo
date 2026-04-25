from typing import Optional
from db.connection import get_connection
from models.task import Task


def create_task(task: Task) -> int:
    conn = get_connection()
    with conn:
        cur = conn.execute(
            "INSERT INTO tasks (user_id, title, description, priority, due_date) VALUES (?, ?, ?, ?, ?)",
            (task.user_id, task.title, task.description, task.priority, task.due_date),
        )
    task_id = cur.lastrowid
    conn.close()
    return task_id


def get_tasks(user_id: int, status: str = "pending") -> list[Task]:
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM tasks WHERE user_id = ? AND status = ? ORDER BY priority ASC, due_date ASC",
        (user_id, status),
    ).fetchall()
    conn.close()
    return [Task(**dict(row)) for row in rows]


def get_task_by_id(task_id: int, user_id: int) -> Optional[Task]:
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM tasks WHERE id = ? AND user_id = ?",
        (task_id, user_id),
    ).fetchone()
    conn.close()
    return Task(**dict(row)) if row else None


def update_task_status(task_id: int, user_id: int, status: str) -> bool:
    conn = get_connection()
    with conn:
        cur = conn.execute(
            "UPDATE tasks SET status = ?, updated_at = datetime('now') WHERE id = ? AND user_id = ?",
            (status, task_id, user_id),
        )
    conn.close()
    return cur.rowcount > 0


def update_task_priority(task_id: int, user_id: int, priority: int) -> bool:
    conn = get_connection()
    with conn:
        cur = conn.execute(
            "UPDATE tasks SET priority = ?, updated_at = datetime('now') WHERE id = ? AND user_id = ?",
            (priority, task_id, user_id),
        )
    conn.close()
    return cur.rowcount > 0
