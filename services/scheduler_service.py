import os
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from config.settings import settings
from utils.logger import get_logger

logger = get_logger(__name__)

os.makedirs(os.path.dirname(settings.scheduler_db_path), exist_ok=True)

_jobstores = {
    "default": SQLAlchemyJobStore(url=f"sqlite:///{settings.scheduler_db_path}")
}

scheduler = AsyncIOScheduler(jobstores=_jobstores, timezone="UTC")


def start_scheduler() -> None:
    if not scheduler.running:
        scheduler.start()
        logger.info("APScheduler started")
