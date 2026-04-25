from telegram import InlineKeyboardButton, InlineKeyboardMarkup


def plan_action_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🔄 Regenerate", callback_data="plan:regenerate"),
            InlineKeyboardButton("⏰ Set reminder", callback_data="plan:remind"),
        ]
    ])
