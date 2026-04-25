from db.connection import get_connection
from models.conversation import ConversationMessage


def add_message(msg: ConversationMessage) -> None:
    conn = get_connection()
    with conn:
        conn.execute(
            "INSERT INTO conversation_history (user_id, role, content) VALUES (?, ?, ?)",
            (msg.user_id, msg.role, msg.content),
        )
    conn.close()


def get_recent_messages(user_id: int, limit: int = 20) -> list[ConversationMessage]:
    conn = get_connection()
    rows = conn.execute(
        """SELECT * FROM conversation_history
           WHERE user_id = ?
           ORDER BY created_at DESC
           LIMIT ?""",
        (user_id, limit),
    ).fetchall()
    conn.close()
    return list(reversed([ConversationMessage(**dict(row)) for row in rows]))


def prune_old_messages(user_id: int, keep_last: int = 50) -> None:
    conn = get_connection()
    with conn:
        conn.execute(
            """DELETE FROM conversation_history
               WHERE user_id = ? AND id NOT IN (
                   SELECT id FROM conversation_history
                   WHERE user_id = ?
                   ORDER BY created_at DESC
                   LIMIT ?
               )""",
            (user_id, user_id, keep_last),
        )
    conn.close()
