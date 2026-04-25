from telegram import Update
from telegram.ext import ContextTypes
from handlers.auth import is_authorized


HELP_TEXT = """
<b>Personal Assistant Commands</b>

<b>Tasks</b>
/addtask &lt;title&gt; — Add a new task
/listtasks — List all pending tasks
/listtasks high — List high-priority tasks only
/donetask &lt;id&gt; — Mark task as done
/deletetask &lt;id&gt; — Delete a task
/prioritize &lt;id&gt; &lt;1|2|3&gt; — Set priority (1=High, 2=Med, 3=Low)

<b>Reminders</b>
/remind — Create a reminder (guided)
/listreminders — List pending reminders
/cancelreminder &lt;id&gt; — Cancel a reminder

<b>Planning</b>
/plan — Generate today's AI-powered daily plan
/plan tomorrow — Plan for tomorrow

<b>Fitness (Whoop)</b>
/logrecovery — Log today's recovery score
/logsleep — Log sleep data
/logstrain — Log strain score
/whoopstats — View last 7 days of Whoop data

<b>Preferences</b>
/setpreference timezone &lt;tz&gt; — e.g. America/New_York
/setpreference goal &lt;strength|endurance|weight_loss|general&gt;
/setpreference plantime &lt;HH:MM&gt; — Daily plan time
/setpreference name &lt;name&gt; — Your preferred name
/setpreference supplement add &lt;name&gt;
/setpreference supplement remove &lt;name&gt;
/mypreferences — View all preferences

<b>AI Chat</b>
Just type naturally — I understand plain language too!
"""


async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await is_authorized(update):
        return
    name = update.effective_user.first_name or "there"
    await update.message.reply_html(
        f"Hi <b>{name}</b>! I'm your personal assistant.\n\n"
        "I can help with tasks, reminders, daily planning, and fitness tracking.\n\n"
        + HELP_TEXT
    )


async def help_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await is_authorized(update):
        return
    await update.message.reply_html(HELP_TEXT)
