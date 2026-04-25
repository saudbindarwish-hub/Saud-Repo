import json
from datetime import datetime, timezone
import anthropic
from config.settings import settings
from utils.logger import get_logger

logger = get_logger(__name__)

_client = anthropic.Anthropic(api_key=settings.anthropic_api_key)

SYSTEM_PROMPT_TEMPLATE = """You are a personal productivity assistant integrated into Telegram. \
Be concise and practical.

User info:
- Preferred name: {preferred_name}
- Timezone: {timezone}
- Fitness goal: {fitness_goal}
- Current date/time: {current_datetime}

Pending tasks:
{tasks_summary}

Today's Whoop recovery:
{recovery_summary}

When the user's message implies an action (add task, set reminder, etc.), respond with a JSON block \
on its own line in this format, followed by a friendly reply:
<action>
{{"intent": "add_reminder", "data": {{"message": "...", "remind_at": "YYYY-MM-DDTHH:MM:SS"}}, "reply": "..."}}
</action>

Valid intents: add_task, add_reminder, none

If no action is needed, omit the <action> block entirely. \
Always ask at most ONE clarifying question if something is ambiguous."""


def _build_system_prompt(context_data: dict) -> str:
    return SYSTEM_PROMPT_TEMPLATE.format(**context_data)


def _extract_action(text: str) -> tuple[dict | None, str]:
    import re
    match = re.search(r"<action>\s*(\{.*?\})\s*</action>", text, re.DOTALL)
    if not match:
        return None, text
    try:
        action = json.loads(match.group(1))
    except json.JSONDecodeError:
        return None, text
    reply = re.sub(r"<action>.*?</action>", "", text, flags=re.DOTALL).strip()
    return action, reply


async def call_claude(
    messages: list[dict],
    context_data: dict,
) -> tuple[str, dict | None]:
    system = _build_system_prompt(context_data)
    response = _client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        system=system,
        messages=messages,
    )
    raw = response.content[0].text
    action, reply = _extract_action(raw)
    return reply, action


async def call_claude_simple(prompt: str, system: str = "") -> str:
    response = _client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        system=system or "You are a helpful personal assistant. Be concise.",
        messages=[{"role": "user", "content": prompt}],
    )
    return response.content[0].text
