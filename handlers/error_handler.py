import traceback
from telegram import Update
from telegram.ext import ContextTypes
from telegram.error import NetworkError, TimedOut
from utils.logger import get_logger

logger = get_logger(__name__)


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    if isinstance(context.error, (NetworkError, TimedOut)):
        return

    logger.error(
        "Unhandled exception in handler",
        extra={
            "error_type": type(context.error).__name__,
            "handler": context.match,
        },
        exc_info=context.error,
    )

    if isinstance(update, Update) and update.effective_message:
        await update.effective_message.reply_text(
            "Something went wrong. Please try again later."
        )
