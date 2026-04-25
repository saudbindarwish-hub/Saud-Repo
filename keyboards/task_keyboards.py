from telegram import InlineKeyboardButton, InlineKeyboardMarkup


def recurrence_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🚫 No repeat", callback_data="recur:none"),
            InlineKeyboardButton("📅 Daily", callback_data="recur:daily"),
        ],
        [
            InlineKeyboardButton("📆 Weekdays", callback_data="recur:weekdays"),
            InlineKeyboardButton("🗓 Weekly", callback_data="recur:weekly"),
        ],
        [InlineKeyboardButton("🔁 Monthly", callback_data="recur:monthly")],
    ])


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
