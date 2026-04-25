from datetime import date
import json
from db.repositories import whoop_repo, preference_repo
from services.claude_service import call_claude_simple
from services.whoop_service import rule_based_suggestion
from utils.logger import get_logger

logger = get_logger(__name__)

_SUGGESTION_SYSTEM = """You are a fitness coach. Be concise — respond in 3–5 sentences max.
Provide: (1) Training intensity today, (2) Specific workout type, (3) One supplement timing tip."""


async def get_training_suggestion(user_id: int) -> str:
    prefs = preference_repo.get_or_create_preferences(user_id)
    today = date.today().isoformat()
    log = whoop_repo.get_today_log(user_id, today)
    recent = whoop_repo.get_recent_logs(user_id, days=7)

    if not log or log.recovery_score is None:
        return "Log your recovery score first with /logrecovery to get a personalized suggestion."

    avg_recovery = sum(l.recovery_score for l in recent if l.recovery_score is not None)
    count = sum(1 for l in recent if l.recovery_score is not None)
    avg_recovery = avg_recovery / count if count else log.recovery_score

    try:
        supplements = json.loads(prefs.supplements)
    except Exception:
        supplements = []

    prompt = f"""Recovery data:
- Today's recovery: {log.recovery_score}/100
- HRV: {log.hrv or 'not logged'} ms
- Resting HR: {log.rhr or 'not logged'} bpm
- 7-day average recovery: {avg_recovery:.0f}/100
- Fitness goal: {prefs.fitness_goal}
- Current supplements: {', '.join(supplements) or 'none listed'}

Give a specific training and supplement recommendation for today."""

    try:
        suggestion = await call_claude_simple(prompt, system=_SUGGESTION_SYSTEM)
        logger.info("Suggestion generated", extra={"user_id": user_id})
        return suggestion
    except Exception:
        logger.error("Suggestion API call failed", extra={"user_id": user_id})
        return rule_based_suggestion(log.recovery_score)
