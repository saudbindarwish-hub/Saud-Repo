from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler, CommandHandler, MessageHandler, CallbackQueryHandler, filters
from handlers.auth import is_authorized
from services import task_service
from utils.formatters import format_task_list
from keyboards.task_keyboards import priority_keyboard, task_action_keyboard
from utils.logger import get_logger

logger = get_logger(__name__)

STATE_TITLE, STATE_PRIORITY, STATE_DUE = range(3)


async def addtask_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int | None:
    if not await is_authorized(update):
        return ConversationHandler.END
    args = context.args
    if args:
        title = " ".join(args)
        try:
            task_id = task_service.add_task(update.effective_user.id, title)
            logger.info("Task added", extra={"user_id": update.effective_user.id, "command": "addtask"})
            await update.message.reply_html(
                f"Task added! <b>{title}</b>\n\nSet priority:",
                reply_markup=priority_keyboard(),
            )
            context.user_data["pending_task_id"] = task_id
        except ValueError as e:
            await update.message.reply_text(str(e))
        return None
    context.user_data.pop("task_title", None)
    await update.message.reply_text("What's the task title?")
    return STATE_TITLE


async def task_title_received(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    title = update.message.text.strip()
    try:
        from utils.validators import validate_task_title
        validate_task_title(title)
    except ValueError as e:
        await update.message.reply_text(str(e))
        return STATE_TITLE
    context.user_data["task_title"] = title
    await update.message.reply_text("Set priority:", reply_markup=priority_keyboard())
    return STATE_PRIORITY


async def task_priority_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    priority = int(query.data.split(":")[1])
    context.user_data["task_priority"] = priority
    if "task_title" in context.user_data:
        await query.edit_message_text("Due date? (e.g. tomorrow, 2026-05-01) or /skip")
        return STATE_DUE
    task_id = context.user_data.pop("pending_task_id", None)
    if task_id:
        from db.repositories import task_repo
        from utils.validators import validate_priority
        task_repo.update_task_priority(task_id, update.effective_user.id, priority)
    await query.edit_message_text("Priority set!")
    return ConversationHandler.END


async def task_due_received(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text.strip()
    due_date = None
    if text != "/skip":
        due_date = text
    title = context.user_data.pop("task_title", "")
    priority = context.user_data.pop("task_priority", 2)
    user_id = update.effective_user.id
    try:
        task_service.add_task(user_id, title, priority=priority, due_date=due_date)
        logger.info("Task added", extra={"user_id": user_id, "command": "addtask"})
        await update.message.reply_html(f"Task <b>{title}</b> added!")
    except ValueError as e:
        await update.message.reply_text(str(e))
    return ConversationHandler.END


async def listtasks_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await is_authorized(update):
        return
    user_id = update.effective_user.id
    priority_filter = None
    if context.args and context.args[0].lower() == "high":
        priority_filter = 1
    tasks = task_service.list_tasks(user_id, priority_filter=priority_filter)
    if not tasks:
        await update.message.reply_text("No pending tasks.")
        return
    for task in tasks:
        await update.message.reply_html(
            f"{'🔴' if task.priority==1 else '🟡' if task.priority==2 else '🟢'} "
            f"<b>{task.title}</b> [ID:{task.id}]"
            + (f"\n   Due: {task.due_date}" if task.due_date else ""),
            reply_markup=task_action_keyboard(task.id),
        )


async def task_action_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await is_authorized(update):
        return
    query = update.callback_query
    await query.answer()
    action, task_id_str = query.data.split(":")
    user_id = update.effective_user.id
    if action == "task_done":
        ok = task_service.mark_done(user_id, task_id_str)
        await query.edit_message_text("✅ Task marked as done!" if ok else "Task not found.")
    elif action == "task_delete":
        ok = task_service.delete_task(user_id, task_id_str)
        await query.edit_message_text("🗑 Task deleted!" if ok else "Task not found.")


async def donetask_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await is_authorized(update):
        return
    if not context.args:
        await update.message.reply_text("Usage: /donetask <id>")
        return
    try:
        ok = task_service.mark_done(update.effective_user.id, context.args[0])
        await update.message.reply_text("✅ Task marked as done!" if ok else "Task not found.")
    except ValueError as e:
        await update.message.reply_text(str(e))


async def deletetask_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await is_authorized(update):
        return
    if not context.args:
        await update.message.reply_text("Usage: /deletetask <id>")
        return
    try:
        ok = task_service.delete_task(update.effective_user.id, context.args[0])
        await update.message.reply_text("🗑 Task deleted!" if ok else "Task not found.")
    except ValueError as e:
        await update.message.reply_text(str(e))


async def prioritize_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await is_authorized(update):
        return
    if len(context.args) < 2:
        await update.message.reply_text("Usage: /prioritize <id> <1|2|3>")
        return
    try:
        ok = task_service.change_priority(update.effective_user.id, context.args[0], context.args[1])
        await update.message.reply_text("Priority updated!" if ok else "Task not found.")
    except ValueError as e:
        await update.message.reply_text(str(e))


def get_task_conversation_handler() -> ConversationHandler:
    return ConversationHandler(
        entry_points=[CommandHandler("addtask", addtask_handler)],
        states={
            STATE_TITLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, task_title_received)],
            STATE_PRIORITY: [CallbackQueryHandler(task_priority_callback, pattern=r"^priority:")],
            STATE_DUE: [MessageHandler(filters.TEXT, task_due_received)],
        },
        fallbacks=[CommandHandler("cancel", lambda u, c: ConversationHandler.END)],
        per_user=True,
        per_chat=True,
        per_message=False,
    )
