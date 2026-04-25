from datetime import date, datetime, timezone
import zoneinfo
from db.repositories import task_repo, whoop_repo, preference_repo
from services.claude_service import call_claude_simple
from utils.logger import get_logger

logger = get_logger(__name__)

_PLANNING_SYSTEM = """You are a personal productivity coach. Generate a clear, practical daily plan.
Format the plan with time blocks, ordered by priority. Be concise — use bullet points.
If Whoop recovery data is available, factor intensity recommendations into the schedule."""


async def generate_daily_plan(user_id: int, for_date: str | None = None) -> str:
    prefs = preference_repo.get_or_create_preferences(user_id)
    try:
        tz = zoneinfo.ZoneInfo(prefs.timezone)
    except Exception:
        tz = zoneinfo.ZoneInfo("UTC")

    target_date = for_date or date.today().isoformat()
    tasks = task_repo.get_tasks(user_id, status="pending")

    if not tasks:
        tasks_text = "No pending tasks."
    else:
        tasks_text = "\n".join(
            f"- [{['High', 'Medium', 'Low'][t.priority - 1]}] {t.title}"
            + (f" (due {t.due_date})" if t.due_date else "")
            for t in tasks
        )

    log = whoop_repo.get_today_log(user_id, target_date)
    if log:
        recovery_text = f"Recovery: {log.recovery_score}/100" if log.recovery_score is not None else "Recovery: not logged"
        if log.hrv:
            recovery_text += f", HRV: {log.hrv} ms"
        if log.strain_score:
            recovery_text += f", Yesterday strain: {log.strain_score}/21"
    else:
        recovery_text = "No Whoop data logged for today."

    now_local = datetime.now(tz).strftime("%A, %B %d, %Y")
    prompt = f"""Create a daily plan for {now_local}.

User: {prefs.preferred_name or 'User'}
Timezone: {prefs.timezone}
Wake time: {prefs.wake_time}, Sleep time: {prefs.sleep_time}
Fitness goal: {prefs.fitness_goal}

Pending tasks:
{tasks_text}

Health data:
{recovery_text}

Generate a structured daily schedule with time blocks. Include task priorities and a brief fitness/wellness suggestion."""

    try:
        plan = await call_claude_simple(prompt, system=_PLANNING_SYSTEM)
        logger.info("Daily plan generated", extra={"user_id": user_id})
        return plan
    except Exception:
        logger.error("Planning failed", extra={"user_id": user_id})
        return "Could not generate plan right now. Please try again."
