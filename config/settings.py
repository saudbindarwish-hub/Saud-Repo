import os
from dataclasses import dataclass, field
from dotenv import load_dotenv

load_dotenv()


@dataclass
class Settings:
    telegram_bot_token: str
    anthropic_api_key: str
    allowed_user_ids: set[int]
    db_path: str = "data/app.db"
    scheduler_db_path: str = "data/scheduler.db"
    log_dir: str = "logs"
    conversation_history_limit: int = 20

    @classmethod
    def from_env(cls) -> "Settings":
        token = os.getenv("TELEGRAM_BOT_TOKEN", "")
        api_key = os.getenv("ANTHROPIC_API_KEY", "")
        raw_ids = os.getenv("ALLOWED_USER_IDS", "")

        if not token:
            raise ValueError("TELEGRAM_BOT_TOKEN is not set in environment")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY is not set in environment")
        if not raw_ids:
            raise ValueError("ALLOWED_USER_IDS is not set in environment")

        try:
            allowed_ids = {int(uid.strip()) for uid in raw_ids.split(",") if uid.strip()}
        except ValueError:
            raise ValueError("ALLOWED_USER_IDS must be comma-separated integers")

        if not allowed_ids:
            raise ValueError("ALLOWED_USER_IDS must contain at least one user ID")

        return cls(
            telegram_bot_token=token,
            anthropic_api_key=api_key,
            allowed_user_ids=allowed_ids,
        )


settings = Settings.from_env()
