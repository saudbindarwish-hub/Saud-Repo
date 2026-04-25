from db.connection import get_connection


def run_migrations() -> None:
    conn = get_connection()
    with conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS tasks (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id     INTEGER NOT NULL,
                title       TEXT    NOT NULL,
                description TEXT,
                priority    INTEGER DEFAULT 2,
                status      TEXT    DEFAULT 'pending',
                due_date    TEXT,
                created_at  TEXT    NOT NULL DEFAULT (datetime('now')),
                updated_at  TEXT    NOT NULL DEFAULT (datetime('now'))
            );
            CREATE INDEX IF NOT EXISTS idx_tasks_user_status ON tasks(user_id, status);

            CREATE TABLE IF NOT EXISTS reminders (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id     INTEGER NOT NULL,
                chat_id     INTEGER NOT NULL,
                message     TEXT    NOT NULL,
                remind_at   TEXT    NOT NULL,
                is_fired    INTEGER DEFAULT 0,
                created_at  TEXT    NOT NULL DEFAULT (datetime('now'))
            );
            CREATE INDEX IF NOT EXISTS idx_reminders_fired_time ON reminders(is_fired, remind_at);

            CREATE TABLE IF NOT EXISTS whoop_logs (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id         INTEGER NOT NULL,
                log_date        TEXT    NOT NULL,
                recovery_score  INTEGER,
                hrv             REAL,
                rhr             INTEGER,
                sleep_hours     REAL,
                sleep_quality   INTEGER,
                strain_score    REAL,
                notes           TEXT,
                created_at      TEXT    NOT NULL DEFAULT (datetime('now')),
                UNIQUE(user_id, log_date)
            );
            CREATE INDEX IF NOT EXISTS idx_whoop_user_date ON whoop_logs(user_id, log_date);

            CREATE TABLE IF NOT EXISTS user_preferences (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id         INTEGER NOT NULL UNIQUE,
                timezone        TEXT    DEFAULT 'UTC',
                daily_plan_time TEXT    DEFAULT '08:00',
                fitness_goal    TEXT    DEFAULT 'general',
                supplements     TEXT    DEFAULT '[]',
                wake_time       TEXT    DEFAULT '07:00',
                sleep_time      TEXT    DEFAULT '23:00',
                preferred_name  TEXT,
                updated_at      TEXT    NOT NULL DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS conversation_history (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id     INTEGER NOT NULL,
                role        TEXT    NOT NULL,
                content     TEXT    NOT NULL,
                created_at  TEXT    NOT NULL DEFAULT (datetime('now'))
            );
            CREATE INDEX IF NOT EXISTS idx_conv_user_time ON conversation_history(user_id, created_at);
        """)
    conn.close()
