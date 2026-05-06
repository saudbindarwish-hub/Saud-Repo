from datetime import date, datetime, timedelta, timezone
import zoneinfo
from telegram import Update
from telegram.ext import ContextTypes
from handlers.auth import is_authorized
from services.planning_service import generate_daily_plan
from services.claude_service import call_claude_simple
from keyboards.planning_keyboards import plan_action_keyboard
from db.repositories import task_repo, reminder_repo, whoop_repo, preference_repo
from utils.logger import get_logger

_UAE_TZ = zoneinfo.ZoneInfo("Asia/Dubai")

_AFTERNOON_SYSTEM = """You are a personal assistant giving a 3 PM check-in. Be concise and direct — 4–6 bullet points max. Cover: remaining tasks, upcoming reminders, and a brief fitness/wellness note if health data is available."""

logger = get_logger(__name__)


async def plan_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await is_authorized(update):
        return
    user_id = update.effective_user.id
    for_tomorrow = context.args and context.args[0].lower() == "tomorrow"
    target_date = (date.today() + timedelta(days=1)).isoformat() if for_tomorrow else None
    await update.message.reply_text("Generating your daily plan...")
    plan = await generate_daily_plan(user_id, for_date=target_date)
    logger.info("Plan command used", extra={"user_id": user_id, "command": "plan"})
    await update.message.reply_text(plan, reply_markup=plan_action_keyboard())


async def plan_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await is_authorized(update):
        return
    query = update.callback_query
    await query.answer()
    action = query.data.split(":")[1]
    if action == "regenerate":
        user_id = update.effective_user.id
        await query.edit_message_text("Regenerating plan...")
        plan = await generate_daily_plan(user_id)
        await query.edit_message_text(plan, reply_markup=plan_action_keyboard())
    elif action == "remind":
        await query.answer("Use /remind to set a reminder for your plan tasks.", show_alert=True)


async def send_scheduled_daily_plan(bot, user_id: int, chat_id: int) -> None:
    plan = await generate_daily_plan(user_id)
    await bot.send_message(chat_id=chat_id, text=f"Good morning! Here's your daily plan:\n\n{plan}")


async def send_afternoon_update(bot, user_id: int, chat_id: int) -> None:
    prefs = preference_repo.get_or_create_preferences(user_id)
    now_uae = datetime.now(_UAE_TZ)
    cutoff = now_uae + timedelta(hours=24)

    tasks = task_repo.get_tasks(user_id, status="pending")
    if tasks:
        tasks_text = "\n".join(
            f"- [{['High', 'Medium', 'Low'][t.priority - 1]}] {t.title}"
            + (f" (due {t.due_date})" if t.due_date else "")
            for t in tasks
        )
    else:
        tasks_text = "No pending tasks."

    reminders = reminder_repo.get_pending_reminders(user_id)
    upcoming = [
        r for r in reminders
        if datetime.fromisoformat(r.remind_at).replace(tzinfo=timezone.utc) <= cutoff.astimezone(timezone.utc)
    ]
    if upcoming:
        reminders_text = "\n".join(
            f"- {r.message} at {datetime.fromisoformat(r.remind_at).replace(tzinfo=timezone.utc).astimezone(_UAE_TZ).strftime('%H:%M')}"
            for r in upcoming
        )
    else:
        reminders_text = "No reminders in the next 24 hours."

    log = whoop_repo.get_today_log(user_id, now_uae.date().isoformat())
    if log and log.recovery_score is not None:
        health_text = f"Recovery: {log.recovery_score}/100"
        if log.hrv:
            health_text += f", HRV: {log.hrv} ms"
        if log.strain_score:
            health_text += f", Strain so far: {log.strain_score}/21"
    else:
        health_text = "No Whoop data logged today."

    prompt = f"""Afternoon check-in for {now_uae.strftime('%A, %B %d')} at {now_uae.strftime('%H:%M')} UAE time.

User: {prefs.preferred_name or 'User'}
Fitness goal: {prefs.fitness_goal}

Remaining tasks:
{tasks_text}

Upcoming reminders (next 24h):
{reminders_text}

Health data:
{health_text}

Give a brief afternoon update: what still needs attention, any reminders coming up, and a short wellness note."""

    try:
        update_text = await call_claude_simple(prompt, system=_AFTERNOON_SYSTEM)
        logger.info("Afternoon update generated", extra={"user_id": user_id})
    except Exception:
        logger.error("Afternoon update failed", extra={"user_id": user_id})
        update_text = "Here's your afternoon check-in:\n\n" + tasks_text

    await bot.send_message(chat_id=chat_id, text=f"Good afternoon! Here's your 3 PM update:\n\n{update_text}")
