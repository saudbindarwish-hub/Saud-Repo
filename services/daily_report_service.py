from datetime import date
from telegram import Bot
from services.gold_service import get_gold_price_aed_per_gram
from services.planning_service import generate_daily_plan
from db.repositories import task_repo, whoop_repo, preference_repo
from utils.logger import get_logger

logger = get_logger(__name__)

_RECURRENCE_ICON = {
    "daily": "🔁",
    "weekdays": "🔁",
    "weekly": "🔁",
    "monthly": "🔁",
}


async def generate_morning_report(user_id: int) -> str:
    prefs = preference_repo.get_or_create_preferences(user_id)
    today = date.today().isoformat()

    # Gold price
    gold_price = await get_gold_price_aed_per_gram()
    gold_text = f"💰 <b>Gold:</b> AED {gold_price:,.2f}/gram" if gold_price else "💰 <b>Gold:</b> unavailable"

    # Pending tasks
    tasks = task_repo.get_tasks(user_id, status="pending")
    if tasks:
        lines = []
        for t in tasks:
            emoji = "🔴" if t.priority == 1 else "🟡" if t.priority == 2 else "🟢"
            recur = " 🔁" if t.recurrence_rule else ""
            due = f" · due {t.due_date}" if t.due_date else ""
            lines.append(f"  {emoji} {t.title}{recur}{due}")
        tasks_text = "\n".join(lines)
    else:
        tasks_text = "  ✓ No pending tasks"

    # Health / Whoop
    log = whoop_repo.get_today_log(user_id, today)
    if log and log.recovery_score is not None:
        rec_emoji = "🟢" if log.recovery_score >= 67 else ("🟡" if log.recovery_score >= 34 else "🔴")
        parts = [f"{rec_emoji} Recovery: {log.recovery_score}/100"]
        if log.hrv:
            parts.append(f"HRV: {log.hrv}ms")
        if log.sleep_hours:
            parts.append(f"Sleep: {log.sleep_hours}h")
        health_text = " | ".join(parts)
    else:
        health_text = "⚪ No Whoop data logged yet"

    # AI-generated daily plan
    plan = await generate_daily_plan(user_id)

    name = prefs.preferred_name or "there"
    return (
        f"☀️ <b>Good morning, {name}!</b>\n"
        f"\n{gold_text}\n"
        f"\n📋 <b>Tasks:</b>\n{tasks_text}\n"
        f"\n💪 <b>Health:</b>\n  {health_text}\n"
        f"\n📅 <b>Today's Plan:</b>\n{plan}"
    )


async def send_daily_report(bot: Bot, user_id: int, chat_id: int) -> None:
    try:
        report = await generate_morning_report(user_id)
        await bot.send_message(chat_id=chat_id, text=report, parse_mode="HTML")
        logger.info("Daily report sent", extra={"user_id": user_id})
    except Exception:
        logger.error("Failed to send daily report", extra={"user_id": user_id})
