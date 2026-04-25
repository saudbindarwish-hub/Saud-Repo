from datetime import date
from models.whoop_log import WhoopLog
from db.repositories import whoop_repo
from utils.logger import get_logger

logger = get_logger(__name__)


def rule_based_suggestion(recovery_score: int) -> str:
    if recovery_score >= 67:
        return "Your recovery is great! Go for a full-intensity workout today."
    elif recovery_score >= 34:
        return "Moderate recovery — a light to moderate session works well today."
    else:
        return "Low recovery — prioritize rest or gentle mobility work today."


def log_recovery(user_id: int, recovery_score: int, hrv: float | None = None,
                 rhr: int | None = None, notes: str | None = None) -> WhoopLog:
    today = date.today().isoformat()
    log = WhoopLog(
        user_id=user_id,
        log_date=today,
        recovery_score=recovery_score,
        hrv=hrv,
        rhr=rhr,
        notes=notes,
    )
    whoop_repo.upsert_whoop_log(log)
    logger.info("Recovery logged", extra={"user_id": user_id})
    return log


def log_sleep(user_id: int, sleep_hours: float, sleep_quality: int | None = None) -> WhoopLog:
    today = date.today().isoformat()
    log = WhoopLog(
        user_id=user_id,
        log_date=today,
        sleep_hours=sleep_hours,
        sleep_quality=sleep_quality,
    )
    whoop_repo.upsert_whoop_log(log)
    logger.info("Sleep logged", extra={"user_id": user_id})
    return log


def log_strain(user_id: int, strain_score: float) -> WhoopLog:
    today = date.today().isoformat()
    log = WhoopLog(user_id=user_id, log_date=today, strain_score=strain_score)
    whoop_repo.upsert_whoop_log(log)
    logger.info("Strain logged", extra={"user_id": user_id})
    return log


def get_recent_logs(user_id: int, days: int = 7) -> list[WhoopLog]:
    return whoop_repo.get_recent_logs(user_id, days)
