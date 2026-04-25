from datetime import datetime, timezone
from telegram import Bot
from models.reminder import Reminder
from db.repositories import reminder_repo
from services.scheduler_service import scheduler
from utils.logger import get_logger

logger = get_logger(__name__)

_DOW_NAMES = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]


def _build_cron_trigger(remind_at: datetime, rule: str):
    from apscheduler.triggers.cron import CronTrigger
    hour = remind_at.hour
    minute = remind_at.minute
    if rule == "daily":
        return CronTrigger(hour=hour, minute=minute, timezone="UTC", start_date=remind_at)
    if rule == "weekdays":
        return CronTrigger(day_of_week="mon-fri", hour=hour, minute=minute, timezone="UTC", start_date=remind_at)
    if rule == "weekly":
        dow = _DOW_NAMES[remind_at.weekday()]
        return CronTrigger(day_of_week=dow, hour=hour, minute=minute, timezone="UTC", start_date=remind_at)
    if rule == "monthly":
        return CronTrigger(day=remind_at.day, hour=hour, minute=minute, timezone="UTC", start_date=remind_at)
    return None


async def fire_reminder(bot: Bot, reminder_id: int) -> None:
    reminder = reminder_repo.get_reminder_by_id(reminder_id)
    if not reminder or reminder.is_fired:
        return
    try:
        await bot.send_message(chat_id=reminder.chat_id, text=f"⏰ Reminder: {reminder.message}")
        reminder_repo.mark_reminder_fired(reminder_id)
        logger.info("Reminder fired", extra={"reminder_id": reminder_id})
    except Exception:
        logger.error("Failed to send reminder", extra={"reminder_id": reminder_id})


async def fire_recurring_reminder(bot: Bot, reminder_id: int) -> None:
    """Fire a recurring reminder without marking it as done."""
    reminder = reminder_repo.get_reminder_by_id(reminder_id)
    if not reminder or reminder.is_fired:
        return
    try:
        await bot.send_message(chat_id=reminder.chat_id, text=f"🔁 Reminder: {reminder.message}")
        logger.info("Recurring reminder fired", extra={"reminder_id": reminder_id})
    except Exception:
        logger.error("Failed to send recurring reminder", extra={"reminder_id": reminder_id})


def schedule_reminder(
    bot: Bot,
    user_id: int,
    chat_id: int,
    message: str,
    remind_at: datetime,
    recurrence_rule: str | None = None,
) -> int:
    reminder = Reminder(
        user_id=user_id,
        chat_id=chat_id,
        message=message,
        remind_at=remind_at.strftime("%Y-%m-%dT%H:%M:%S"),
        recurrence_rule=recurrence_rule,
    )
    reminder_id = reminder_repo.create_reminder(reminder)
    job_id = f"reminder_{reminder_id}"

    if recurrence_rule:
        trigger = _build_cron_trigger(remind_at, recurrence_rule)
        scheduler.add_job(
            fire_recurring_reminder,
            trigger,
            args=[bot, reminder_id],
            id=job_id,
            replace_existing=True,
            misfire_grace_time=300,
        )
    else:
        scheduler.add_job(
            fire_reminder,
            "date",
            run_date=remind_at,
            args=[bot, reminder_id],
            id=job_id,
            replace_existing=True,
            misfire_grace_time=300,
        )

    logger.info("Reminder scheduled", extra={"reminder_id": reminder_id, "recurrence": recurrence_rule})
    return reminder_id


def cancel_reminder_job(reminder_id: int, user_id: int) -> bool:
    ok = reminder_repo.cancel_reminder(reminder_id, user_id)
    if ok:
        job_id = f"reminder_{reminder_id}"
        try:
            scheduler.remove_job(job_id)
        except Exception:
            pass
    return ok
