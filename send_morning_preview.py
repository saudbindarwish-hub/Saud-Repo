"""
Run this once on your server to send a preview of tomorrow's morning message.
Usage:  python3 send_morning_preview.py
"""
import asyncio
import os
import sys

# Load env so settings initialises cleanly
from dotenv import load_dotenv
load_dotenv()

from telegram import Bot
from config.settings import settings
from services.planning_service import generate_daily_plan
from services.metals_service import fetch_metals_prices, format_metals_section
from services.claude_service import call_claude_simple

_METALS_SYSTEM = (
    "You are a concise precious-metals market analyst. Given today's gold and silver spot prices, "
    "provide a 3–4 sentence recommendation covering: (1) whether current prices look high/low relative "
    "to recent trends, (2) a short-term outlook, (3) one actionable suggestion (buy, hold, or wait for "
    "a dip). Be direct — no disclaimers or lengthy caveats."
)


async def main() -> None:
    if not settings.allowed_user_ids:
        print("ERROR: No ALLOWED_USER_IDS configured.")
        sys.exit(1)

    user_id = next(iter(settings.allowed_user_ids))
    chat_id = user_id  # DM: chat_id == user_id
    print(f"Sending preview to user_id={user_id} ...")

    bot = Bot(token=settings.telegram_bot_token)

    # 1 — daily plan
    print("  Generating daily plan ...")
    plan = await generate_daily_plan(user_id)

    # 2 — metals prices
    print("  Fetching metals prices ...")
    prices = await fetch_metals_prices()
    if prices:
        metals_table = format_metals_section(prices)
        g, s = prices["gold"], prices["silver"]
        metals_prompt = (
            f"Gold spot: ${g['usd_oz']:,.2f}/oz (AED {g['aed_oz']:,.2f}), "
            f"${g['usd_gram']:,.2f}/gram (AED {g['aed_gram']:,.2f})\n"
            f"Silver spot: ${s['usd_oz']:,.2f}/oz (AED {s['aed_oz']:,.2f}), "
            f"${s['usd_kg']:,.2f}/kg (AED {s['aed_kg']:,.2f})\n\n"
            "Give your brief recommendation."
        )
        print("  Generating metals recommendation ...")
        try:
            metals_rec = await call_claude_simple(metals_prompt, system=_METALS_SYSTEM)
        except Exception as e:
            metals_rec = f"(Recommendation unavailable: {e})"
        metals_section = f"\n\n{metals_table}\n\n💡 <b>Recommendation</b>\n{metals_rec}"
    else:
        metals_section = "\n\n⚠️ <i>Metals prices unavailable right now.</i>"

    morning_text = (
        "🔔 <b>[PREVIEW — Tomorrow's 6 AM Message]</b>\n\n"
        f"Good morning! Here's your daily plan:\n\n{plan}{metals_section}"
    )

    print("  Sending message ...")
    await bot.send_message(chat_id=chat_id, text=morning_text, parse_mode="HTML")
    print("Done! Check your Telegram.")


if __name__ == "__main__":
    asyncio.run(main())
