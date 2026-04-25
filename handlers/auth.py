from telegram import Update
from telegram.ext import ContextTypes
from config.settings import settings


async def is_authorized(update: Update) -> bool:
    """Check authorization using immutable numeric user_id — never @username."""
    if update.effective_user is None:
        return False
    return update.effective_user.id in settings.allowed_user_ids
