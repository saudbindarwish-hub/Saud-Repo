from telegram import Update
from telegram.ext import ContextTypes
from handlers.auth import is_authorized
from services.daily_report_service import generate_morning_report
from utils.logger import get_logger

logger = get_logger(__name__)


async def dailyreport_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await is_authorized(update):
        return
    user_id = update.effective_user.id
    await update.message.reply_text("Generating your morning report...")
    report = await generate_morning_report(user_id)
    logger.info("Daily report requested", extra={"user_id": user_id, "command": "dailyreport"})
    await update.message.reply_html(report)
