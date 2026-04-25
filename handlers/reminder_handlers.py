from datetime import datetime, timezone
from telegram import Update
from telegram.ext import (
    ContextTypes, ConversationHandler, CommandHandler,
    MessageHandler, CallbackQueryHandler, filters,
)
from handlers.auth import is_authorized
from services import reminder_service
from db.repositories import reminder_repo, preference_repo
from utils.validators import validate_reminder_message
from utils.formatters import format_reminder_list
from utils.time_parser import parse_time, format_remind_at, friendly_datetime
from keyboards.reminder_keyboards import quick_time_keyboard, reminder_cancel_keyboard, recurrence_keyboard
from utils.logger import get_logger

logger = get_logger(__name__)

STATE_TEXT, STATE_TIME, STATE_CUSTOM, STATE_RECURRENCE = range(4)

_RECURRENCE_LABELS = {
    "daily": "Daily",
    "weekdays": "Weekdays (Mon–Fri)",
    "weekly": "Weekly",
    "monthly": "Monthly",
}


async def remind_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not await is_authorized(update):
        return ConversationHandler.END
    await update.message.reply_text("What should I remind you about?")
    return STATE_TEXT


async def remind_text_received(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text.strip()
    try:
        text = validate_reminder_message(text)
    except ValueError as e:
        await update.message.reply_text(str(e))
        return STATE_TEXT
    context.user_data["remind_message"] = text
    await update.message.reply_text("When?", reply_markup=quick_time_keyboard())
    return STATE_TIME


async def remind_quick_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    choice = query.data.split(":")[1]

    if choice == "custom":
        await query.edit_message_text("Enter a time (e.g. 'tomorrow at 9am', 'in 3 hours'):")
        return STATE_CUSTOM

    now = datetime.now(timezone.utc)
    from datetime import timedelta
    offsets = {
        "1h": timedelta(hours=1),
        "2h": timedelta(hours=2),
        "4h": timedelta(hours=4),
    }
    if choice in offsets:
        remind_at = now + offsets[choice]
    elif choice == "tomorrow9am":
        from datetime import date
        tomorrow = date.today().replace(day=date.today().day + 1)
        remind_at = datetime(tomorrow.year, tomorrow.month, tomorrow.day, 9, 0, tzinfo=timezone.utc)
    else:
        await query.edit_message_text("Unknown time option.")
        return ConversationHandler.END

    return await _ask_recurrence(update, context, remind_at)


async def remind_custom_received(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.effective_user.id
    prefs = preference_repo.get_or_create_preferences(user_id)
    remind_at = parse_time(update.message.text.strip(), user_timezone=prefs.timezone)
    if remind_at is None:
        await update.message.reply_text("Couldn't understand that time. Try 'tomorrow at 9am' or 'in 2 hours'.")
        return STATE_CUSTOM
    return await _ask_recurrence(update, context, remind_at)


async def _ask_recurrence(update: Update, context: ContextTypes.DEFAULT_TYPE, remind_at: datetime) -> int:
    context.user_data["remind_at"] = remind_at
    text = "How often should this repeat?"
    if update.callback_query:
        await update.callback_query.edit_message_text(text, reply_markup=recurrence_keyboard())
    else:
        await update.message.reply_text(text, reply_markup=recurrence_keyboard())
    return STATE_RECURRENCE


async def remind_recurrence_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    rule = query.data.split(":")[1]
    recurrence_rule = None if rule == "none" else rule

    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    message = context.user_data.pop("remind_message", "Reminder")
    remind_at: datetime = context.user_data.pop("remind_at")
    bot = context.bot

    reminder_service.schedule_reminder(bot, user_id, chat_id, message, remind_at, recurrence_rule=recurrence_rule)

    prefs = preference_repo.get_or_create_preferences(user_id)
    friendly = friendly_datetime(format_remind_at(remind_at), prefs.timezone)
    logger.info("Reminder set", extra={"user_id": user_id, "command": "remind", "recurrence": recurrence_rule})

    label = _RECURRENCE_LABELS.get(recurrence_rule, "") if recurrence_rule else ""
    recur_text = f"\n🔁 Repeats: {label}" if recurrence_rule else ""
    reply_text = f"⏰ Reminder set for <b>{friendly}</b>:\n{message}{recur_text}"
    await query.edit_message_text(reply_text, parse_mode="HTML")
    return ConversationHandler.END


async def listreminders_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await is_authorized(update):
        return
    reminders = reminder_repo.get_pending_reminders(update.effective_user.id)
    if not reminders:
        await update.message.reply_text("No pending reminders.")
        return
    for r in reminders:
        recur_text = f"\n🔁 {_RECURRENCE_LABELS.get(r.recurrence_rule, r.recurrence_rule)}" if r.recurrence_rule else ""
        await update.message.reply_html(
            f"⏰ <b>{r.message}</b>\nWhen: {r.remind_at} UTC{recur_text} [ID:{r.id}]",
            reply_markup=reminder_cancel_keyboard(r.id),
        )


async def cancelreminder_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await is_authorized(update):
        return
    if not context.args:
        await update.message.reply_text("Usage: /cancelreminder <id>")
        return
    try:
        rid = int(context.args[0])
    except ValueError:
        await update.message.reply_text("Reminder ID must be a number.")
        return
    ok = reminder_service.cancel_reminder_job(rid, update.effective_user.id)
    await update.message.reply_text("Reminder cancelled." if ok else "Reminder not found.")


async def reminder_cancel_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await is_authorized(update):
        return
    query = update.callback_query
    await query.answer()
    rid = int(query.data.split(":")[1])
    ok = reminder_service.cancel_reminder_job(rid, update.effective_user.id)
    await query.edit_message_text("Reminder cancelled." if ok else "Reminder not found.")


def get_reminder_conversation_handler() -> ConversationHandler:
    return ConversationHandler(
        entry_points=[CommandHandler("remind", remind_start)],
        states={
            STATE_TEXT: [MessageHandler(filters.TEXT & ~filters.COMMAND, remind_text_received)],
            STATE_TIME: [CallbackQueryHandler(remind_quick_callback, pattern=r"^remind_quick:")],
            STATE_CUSTOM: [MessageHandler(filters.TEXT & ~filters.COMMAND, remind_custom_received)],
            STATE_RECURRENCE: [CallbackQueryHandler(remind_recurrence_callback, pattern=r"^recur:")],
        },
        fallbacks=[CommandHandler("cancel", lambda u, c: ConversationHandler.END)],
        per_user=True,
        per_chat=True,
        per_message=False,
    )
