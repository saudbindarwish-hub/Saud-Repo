from telegram import Update
from telegram.ext import (
    ContextTypes, ConversationHandler, CommandHandler,
    MessageHandler, filters,
)
from handlers.auth import is_authorized
from services import whoop_service, suggestion_service
from utils.validators import (
    validate_recovery_score, validate_hrv, validate_rhr,
    validate_sleep_hours, validate_sleep_quality, validate_strain_score, validate_notes,
)
from utils.formatters import format_whoop_stats
from utils.logger import get_logger

logger = get_logger(__name__)

(STATE_RECOVERY, STATE_HRV, STATE_RHR, STATE_NOTES,
 STATE_SLEEP_HOURS, STATE_SLEEP_QUALITY, STATE_STRAIN) = range(7)

SKIP = "/skip"


async def logrecovery_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not await is_authorized(update):
        return ConversationHandler.END
    await update.message.reply_text("Recovery score (0–100)?")
    return STATE_RECOVERY


async def recovery_received(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        score = validate_recovery_score(update.message.text)
    except ValueError as e:
        await update.message.reply_text(str(e))
        return STATE_RECOVERY
    context.user_data["recovery_score"] = score
    await update.message.reply_text("HRV in ms? (or /skip)")
    return STATE_HRV


async def hrv_received(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text.strip()
    if text != SKIP:
        try:
            context.user_data["hrv"] = validate_hrv(text)
        except ValueError as e:
            await update.message.reply_text(str(e))
            return STATE_HRV
    await update.message.reply_text("Resting heart rate (bpm)? (or /skip)")
    return STATE_RHR


async def rhr_received(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text.strip()
    if text != SKIP:
        try:
            context.user_data["rhr"] = validate_rhr(text)
        except ValueError as e:
            await update.message.reply_text(str(e))
            return STATE_RHR
    await update.message.reply_text("Any notes? (or /skip)")
    return STATE_NOTES


async def notes_received(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text.strip()
    notes = None
    if text != SKIP:
        try:
            notes = validate_notes(text)
        except ValueError as e:
            await update.message.reply_text(str(e))
            return STATE_NOTES

    user_id = update.effective_user.id
    whoop_service.log_recovery(
        user_id=user_id,
        recovery_score=context.user_data.pop("recovery_score"),
        hrv=context.user_data.pop("hrv", None),
        rhr=context.user_data.pop("rhr", None),
        notes=notes,
    )
    logger.info("Recovery log saved", extra={"user_id": user_id, "command": "logrecovery"})
    await update.message.reply_text("Recovery logged! Getting your training suggestion...")
    suggestion = await suggestion_service.get_training_suggestion(user_id)
    await update.message.reply_text(suggestion)
    return ConversationHandler.END


async def logsleep_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not await is_authorized(update):
        return ConversationHandler.END
    await update.message.reply_text("How many hours did you sleep?")
    return STATE_SLEEP_HOURS


async def sleep_hours_received(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        hours = validate_sleep_hours(update.message.text)
    except ValueError as e:
        await update.message.reply_text(str(e))
        return STATE_SLEEP_HOURS
    context.user_data["sleep_hours"] = hours
    await update.message.reply_text("Sleep quality score (0–100)? (or /skip)")
    return STATE_SLEEP_QUALITY


async def sleep_quality_received(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text.strip()
    quality = None
    if text != SKIP:
        try:
            quality = validate_sleep_quality(text)
        except ValueError as e:
            await update.message.reply_text(str(e))
            return STATE_SLEEP_QUALITY
    user_id = update.effective_user.id
    whoop_service.log_sleep(user_id, context.user_data.pop("sleep_hours"), quality)
    logger.info("Sleep logged", extra={"user_id": user_id, "command": "logsleep"})
    await update.message.reply_text("Sleep data logged!")
    return ConversationHandler.END


async def logstrain_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not await is_authorized(update):
        return ConversationHandler.END
    await update.message.reply_text("Strain score (0–21)?")
    return STATE_STRAIN


async def strain_received(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        strain = validate_strain_score(update.message.text)
    except ValueError as e:
        await update.message.reply_text(str(e))
        return STATE_STRAIN
    user_id = update.effective_user.id
    whoop_service.log_strain(user_id, strain)
    logger.info("Strain logged", extra={"user_id": user_id, "command": "logstrain"})
    await update.message.reply_text("Strain logged!")
    return ConversationHandler.END


async def whoopstats_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await is_authorized(update):
        return
    logs = whoop_service.get_recent_logs(update.effective_user.id, days=7)
    await update.message.reply_html(format_whoop_stats(logs))


def get_recovery_conversation() -> ConversationHandler:
    return ConversationHandler(
        entry_points=[CommandHandler("logrecovery", logrecovery_start)],
        states={
            STATE_RECOVERY: [MessageHandler(filters.TEXT & ~filters.COMMAND, recovery_received)],
            STATE_HRV: [MessageHandler(filters.TEXT, hrv_received)],
            STATE_RHR: [MessageHandler(filters.TEXT, rhr_received)],
            STATE_NOTES: [MessageHandler(filters.TEXT, notes_received)],
        },
        fallbacks=[CommandHandler("cancel", lambda u, c: ConversationHandler.END)],
        per_user=True, per_chat=True,
    )


def get_sleep_conversation() -> ConversationHandler:
    return ConversationHandler(
        entry_points=[CommandHandler("logsleep", logsleep_start)],
        states={
            STATE_SLEEP_HOURS: [MessageHandler(filters.TEXT & ~filters.COMMAND, sleep_hours_received)],
            STATE_SLEEP_QUALITY: [MessageHandler(filters.TEXT, sleep_quality_received)],
        },
        fallbacks=[CommandHandler("cancel", lambda u, c: ConversationHandler.END)],
        per_user=True, per_chat=True,
    )


def get_strain_conversation() -> ConversationHandler:
    return ConversationHandler(
        entry_points=[CommandHandler("logstrain", logstrain_start)],
        states={
            STATE_STRAIN: [MessageHandler(filters.TEXT & ~filters.COMMAND, strain_received)],
        },
        fallbacks=[CommandHandler("cancel", lambda u, c: ConversationHandler.END)],
        per_user=True, per_chat=True,
    )
