from telegram import InlineKeyboardButton, InlineKeyboardMarkup


def priority_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🔴 High", callback_data="priority:1"),
            InlineKeyboardButton("🟡 Medium", callback_data="priority:2"),
            InlineKeyboardButton("🟢 Low", callback_data="priority:3"),
        ]
    ])


def task_action_keyboard(task_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ Done", callback_data=f"task_done:{task_id}"),
            InlineKeyboardButton("🗑 Delete", callback_data=f"task_delete:{task_id}"),
        ]
    ])
