import json
from telegram import Update
from telegram.ext import ContextTypes
from handlers.auth import is_authorized
from db.repositories import preference_repo
from services.scheduler_service import scheduler
from handlers.planning_handlers import send_scheduled_daily_plan
from utils.validators import (
    validate_timezone, validate_plan_time, validate_fitness_goal,
    validate_supplement_name, validate_preferred_name,
)
from utils.logger import get_logger

logger = get_logger(__name__)


async def setpreference_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await is_authorized(update):
        return
    args = context.args
    if not args:
        await update.message.reply_text(
            "Usage: /setpreference <field> <value>\n"
            "Fields: timezone, goal, plantime, name, supplement add/remove <name>"
        )
        return

    user_id = update.effective_user.id
    field = args[0].lower()

    try:
        if field == "timezone" and len(args) >= 2:
            tz = validate_timezone(args[1])
            preference_repo.update_preference(user_id, "timezone", tz)
            await update.message.reply_text(f"Timezone set to {tz}.")

        elif field == "goal" and len(args) >= 2:
            goal = validate_fitness_goal(args[1])
            preference_repo.update_preference(user_id, "fitness_goal", goal)
            await update.message.reply_text(f"Fitness goal set to {goal}.")

        elif field == "plantime" and len(args) >= 2:
            plan_time = validate_plan_time(args[1])
            preference_repo.update_preference(user_id, "daily_plan_time", plan_time)
            prefs = preference_repo.get_or_create_preferences(user_id)
            _reschedule_daily_plan(user_id, update.effective_chat.id, plan_time, prefs.timezone)
            await update.message.reply_text(f"Daily plan time set to {plan_time}.")

        elif field == "name" and len(args) >= 2:
            name = validate_preferred_name(" ".join(args[1:]))
            preference_repo.update_preference(user_id, "preferred_name", name)
            await update.message.reply_text(f"I'll call you {name}.")

        elif field == "supplement" and len(args) >= 3:
            action = args[1].lower()
            supplement = validate_supplement_name(" ".join(args[2:]))
            prefs = preference_repo.get_or_create_preferences(user_id)
            try:
                supplements = json.loads(prefs.supplements)
            except Exception:
                supplements = []
            if action == "add":
                if supplement not in supplements:
                    supplements.append(supplement)
                preference_repo.update_preference(user_id, "supplements", json.dumps(supplements))
                await update.message.reply_text(f"Added supplement: {supplement}.")
            elif action == "remove":
                supplements = [s for s in supplements if s != supplement]
                preference_repo.update_preference(user_id, "supplements", json.dumps(supplements))
                await update.message.reply_text(f"Removed supplement: {supplement}.")
            else:
                await update.message.reply_text("Use: /setpreference supplement add/remove <name>")

        else:
            await update.message.reply_text(
                "Unknown preference or missing value.\n"
                "Fields: timezone, goal, plantime, name, supplement add/remove <name>"
            )
    except ValueError as e:
        await update.message.reply_text(str(e))

    logger.info("Preference updated", extra={"user_id": user_id, "command": "setpreference"})


def _reschedule_daily_plan(user_id: int, chat_id: int, plan_time: str, timezone: str) -> None:
    try:
        h, m = int(plan_time[:2]), int(plan_time[3:])
        import zoneinfo
        try:
            tz = zoneinfo.ZoneInfo(timezone)
        except Exception:
            import pytz
            tz = pytz.timezone(timezone)
        job_id = f"daily_plan_{user_id}"
        scheduler.add_job(
            send_scheduled_daily_plan,
            "cron",
            hour=h,
            minute=m,
            timezone=tz,
            id=job_id,
            replace_existing=True,
            args=[None, user_id, chat_id],
            misfire_grace_time=300,
        )
    except Exception:
        logger.error("Failed to reschedule daily plan", extra={"user_id": user_id})


async def mypreferences_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await is_authorized(update):
        return
    user_id = update.effective_user.id
    prefs = preference_repo.get_or_create_preferences(user_id)
    try:
        supplements = json.loads(prefs.supplements)
        supplements_text = ", ".join(supplements) if supplements else "none"
    except Exception:
        supplements_text = "none"

    text = (
        f"<b>Your Preferences:</b>\n"
        f"Name: {prefs.preferred_name or 'not set'}\n"
        f"Timezone: {prefs.timezone}\n"
        f"Daily plan time: {prefs.daily_plan_time}\n"
        f"Fitness goal: {prefs.fitness_goal}\n"
        f"Wake time: {prefs.wake_time}\n"
        f"Sleep time: {prefs.sleep_time}\n"
        f"Supplements: {supplements_text}"
    )
    await update.message.reply_html(text)
