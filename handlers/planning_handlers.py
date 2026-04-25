from telegram import Update
from telegram.ext import ContextTypes
from handlers.auth import is_authorized
from services.planning_service import generate_daily_plan
from keyboards.planning_keyboards import plan_action_keyboard
from utils.logger import get_logger
from datetime import date, timedelta

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
