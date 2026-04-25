from telegram import InlineKeyboardButton, InlineKeyboardMarkup


def quick_time_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("In 1 hour", callback_data="remind_quick:1h"),
            InlineKeyboardButton("In 2 hours", callback_data="remind_quick:2h"),
        ],
        [
            InlineKeyboardButton("In 4 hours", callback_data="remind_quick:4h"),
            InlineKeyboardButton("Tomorrow 9am", callback_data="remind_quick:tomorrow9am"),
        ],
        [InlineKeyboardButton("Custom time...", callback_data="remind_quick:custom")],
    ])


def reminder_cancel_keyboard(reminder_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("❌ Cancel", callback_data=f"reminder_cancel:{reminder_id}")]
    ])
