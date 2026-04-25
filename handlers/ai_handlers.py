import time
from datetime import datetime, timezone, date
from telegram import Update
from telegram.ext import ContextTypes
from handlers.auth import is_authorized
from services import claude_service, reminder_service, task_service
from db.repositories import conversation_repo, preference_repo, task_repo, whoop_repo
from models.conversation import ConversationMessage
from utils.logger import get_logger
from config.settings import settings

logger = get_logger(__name__)

_USER_COOLDOWN_SECONDS = 3


def _build_context_data(user_id: int) -> dict:
    prefs = preference_repo.get_or_create_preferences(user_id)
    tasks = task_repo.get_tasks(user_id, status="pending")
    tasks_summary = "\n".join(f"- {t.title} (priority {t.priority})" for t in tasks) or "None"
    today_str = date.today().isoformat()
    log = whoop_repo.get_today_log(user_id, today_str)
    if log and log.recovery_score is not None:
        recovery_summary = f"Recovery: {log.recovery_score}/100"
        if log.hrv:
            recovery_summary += f", HRV: {log.hrv} ms"
    else:
        recovery_summary = "Not logged yet"
    import zoneinfo
    try:
        tz = zoneinfo.ZoneInfo(prefs.timezone)
    except Exception:
        tz = zoneinfo.ZoneInfo("UTC")
    now_local = datetime.now(tz).strftime("%A, %B %d, %Y %H:%M %Z")
    return {
        "preferred_name": prefs.preferred_name or "there",
        "timezone": prefs.timezone,
        "fitness_goal": prefs.fitness_goal,
        "current_datetime": now_local,
        "tasks_summary": tasks_summary,
        "recovery_summary": recovery_summary,
    }


async def _dispatch_action(action: dict, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    intent = action.get("intent")
    data = action.get("data", {})
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    if intent == "add_reminder":
        message = data.get("message", "Reminder")
        remind_at_str = data.get("remind_at", "")
        recurrence_rule = data.get("recurrence_rule") or None
        try:
            remind_at = datetime.fromisoformat(remind_at_str).replace(tzinfo=timezone.utc)
            reminder_service.schedule_reminder(
                context.bot, user_id, chat_id, message, remind_at, recurrence_rule=recurrence_rule
            )
        except Exception:
            logger.error("Failed to dispatch add_reminder action", extra={"user_id": user_id})
    elif intent == "add_task":
        title = data.get("title", "")
        recurrence_rule = data.get("recurrence_rule") or None
        if title:
            try:
                task_service.add_task(user_id, title, recurrence_rule=recurrence_rule)
            except Exception:
                logger.error("Failed to dispatch add_task action", extra={"user_id": user_id})


async def ai_message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await is_authorized(update):
        return

    user_id = update.effective_user.id

    last_call = context.user_data.get("ai_last_call", 0)
    if time.time() - last_call < _USER_COOLDOWN_SECONDS:
        await update.message.reply_text("Please wait a moment before sending another message.")
        return
    context.user_data["ai_last_call"] = time.time()

    user_text = update.message.text.strip()

    conversation_repo.add_message(ConversationMessage(
        user_id=user_id,
        role="user",
        content=user_text,
    ))
    conversation_repo.prune_old_messages(user_id, keep_last=50)

    history = conversation_repo.get_recent_messages(user_id, limit=settings.conversation_history_limit)
    messages = [{"role": m.role, "content": m.content} for m in history]

    context_data = _build_context_data(user_id)

    try:
        reply, action = await claude_service.call_claude(messages, context_data)
    except Exception:
        logger.error("Claude API call failed", extra={"user_id": user_id})
        await update.message.reply_text("I'm having trouble connecting right now. Please try again.")
        return

    conversation_repo.add_message(ConversationMessage(
        user_id=user_id,
        role="assistant",
        content=reply,
    ))

    if action:
        await _dispatch_action(action, update, context)

    logger.info("AI response sent", extra={"user_id": user_id, "command": "ai_chat"})
    await update.message.reply_text(reply)
