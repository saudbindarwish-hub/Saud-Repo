from telegram import Update
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    CallbackQueryHandler, filters, Defaults,
)
from telegram.constants import ParseMode
from telegram.ext import AIORateLimiter

from config.settings import settings
from db.migrations import run_migrations
from services.scheduler_service import start_scheduler, scheduler
from utils.logger import get_logger

from handlers.start import start_handler, help_handler
from handlers.error_handler import error_handler
from handlers.task_handlers import (
    get_task_conversation_handler, listtasks_handler,
    donetask_handler, deletetask_handler, prioritize_handler,
    task_action_callback,
)
from handlers.reminder_handlers import (
    get_reminder_conversation_handler, listreminders_handler,
    cancelreminder_handler, reminder_cancel_callback,
)
from handlers.planning_handlers import plan_handler, plan_callback
from handlers.whoop_handlers import (
    get_recovery_conversation, get_sleep_conversation,
    get_strain_conversation, whoopstats_handler,
)
from handlers.preference_handlers import setpreference_handler, mypreferences_handler
from handlers.report_handlers import dailyreport_handler
from handlers.ai_handlers import ai_message_handler

logger = get_logger(__name__)


def _schedule_daily_reports(bot) -> None:
    from apscheduler.triggers.cron import CronTrigger
    from db.repositories import preference_repo
    from services.daily_report_service import send_daily_report

    for user_id in settings.allowed_user_ids:
        prefs = preference_repo.get_or_create_preferences(user_id)
        tz = prefs.timezone or "UTC"
        trigger = CronTrigger(hour=5, minute=30, timezone=tz)
        scheduler.add_job(
            send_daily_report,
            trigger,
            # For private Telegram chats, chat_id == user_id
            args=[bot, user_id, user_id],
            id=f"daily_report_{user_id}",
            replace_existing=True,
            misfire_grace_time=600,
        )
        logger.info("Daily report scheduled", extra={"user_id": user_id, "timezone": tz})


def main() -> None:
    run_migrations()
    logger.info("Database migrations complete")

    start_scheduler()

    app = (
        ApplicationBuilder()
        .token(settings.telegram_bot_token)
        .rate_limiter(AIORateLimiter(max_retries=3))
        .defaults(Defaults(parse_mode=ParseMode.HTML))
        .build()
    )

    # Core
    app.add_handler(CommandHandler("start", start_handler))
    app.add_handler(CommandHandler("help", help_handler))

    # Tasks — ConversationHandler first, then direct commands
    app.add_handler(get_task_conversation_handler())
    app.add_handler(CommandHandler("listtasks", listtasks_handler))
    app.add_handler(CommandHandler("donetask", donetask_handler))
    app.add_handler(CommandHandler("deletetask", deletetask_handler))
    app.add_handler(CommandHandler("prioritize", prioritize_handler))
    app.add_handler(CallbackQueryHandler(task_action_callback, pattern=r"^task_(done|delete):"))

    # Reminders
    app.add_handler(get_reminder_conversation_handler())
    app.add_handler(CommandHandler("listreminders", listreminders_handler))
    app.add_handler(CommandHandler("cancelreminder", cancelreminder_handler))
    app.add_handler(CallbackQueryHandler(reminder_cancel_callback, pattern=r"^reminder_cancel:"))

    # Planning
    app.add_handler(CommandHandler("plan", plan_handler))
    app.add_handler(CallbackQueryHandler(plan_callback, pattern=r"^plan:"))

    # Whoop
    app.add_handler(get_recovery_conversation())
    app.add_handler(get_sleep_conversation())
    app.add_handler(get_strain_conversation())
    app.add_handler(CommandHandler("whoopstats", whoopstats_handler))

    # Preferences
    app.add_handler(CommandHandler("setpreference", setpreference_handler))
    app.add_handler(CommandHandler("mypreferences", mypreferences_handler))

    # Daily report (on-demand)
    app.add_handler(CommandHandler("dailyreport", dailyreport_handler))

    # AI catch-all — MUST be last
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, ai_message_handler))

    # Global error handler
    app.add_error_handler(error_handler)

    # Schedule 5:30 AM daily reports for all authorised users
    _schedule_daily_reports(app.bot)
    logger.info("Daily reports scheduled")

    logger.info("Bot starting — polling mode")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
