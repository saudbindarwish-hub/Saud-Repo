import httpx
from utils.logger import get_logger

logger = get_logger(__name__)

_USD_TO_AED = 3.6725  # Fixed UAE peg
_TROY_OZ_TO_GRAM = 31.1035

# metals.live — free, no API key, returns spot prices in USD per troy oz
_METALS_URL = "https://metals.live/api/v1/spot"


def _parse_spot(data) -> dict[str, float]:
    """Normalise the metals.live response into {symbol: price_usd_oz}."""
    if isinstance(data, dict):
        return {k.upper(): float(v) for k, v in data.items()}
    if isinstance(data, list):
        merged: dict[str, float] = {}
        for item in data:
            if isinstance(item, dict):
                merged.update({k.upper(): float(v) for k, v in item.items()})
        return merged
    return {}


async def fetch_metals_prices() -> dict | None:
    """
    Returns dict with gold/silver spot prices in USD and AED, per oz and per gram.
    Returns None if the fetch fails.
    """
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(_METALS_URL, follow_redirects=True)
            resp.raise_for_status()
            raw = _parse_spot(resp.json())

        gold_usd_oz = raw.get("XAU") or raw.get("GOLD")
        silver_usd_oz = raw.get("XAG") or raw.get("SILVER")

        if not gold_usd_oz or not silver_usd_oz:
            logger.warning("Metals API returned unexpected format", extra={"raw_keys": list(raw.keys())})
            return None

        def _convert(usd_oz: float) -> dict:
            return {
                "usd_oz":   round(usd_oz, 2),
                "usd_gram": round(usd_oz / _TROY_OZ_TO_GRAM, 2),
                "aed_oz":   round(usd_oz * _USD_TO_AED, 2),
                "aed_gram": round((usd_oz / _TROY_OZ_TO_GRAM) * _USD_TO_AED, 2),
            }

        logger.info("Metals prices fetched")
        return {"gold": _convert(gold_usd_oz), "silver": _convert(silver_usd_oz)}

    except Exception as exc:
        logger.error("Failed to fetch metals prices", extra={"error": str(exc)})
        return None


def format_metals_section(prices: dict) -> str:
    g = prices["gold"]
    s = prices["silver"]
    return (
        "📊 <b>Spot Prices (today)</b>\n"
        "\n"
        "🥇 <b>Gold</b>\n"
        f"  Per oz:   ${g['usd_oz']:,.2f}  |  AED {g['aed_oz']:,.2f}\n"
        f"  Per gram: ${g['usd_gram']:,.2f}  |  AED {g['aed_gram']:,.2f}\n"
        "\n"
        "🥈 <b>Silver</b>\n"
        f"  Per oz:   ${s['usd_oz']:,.2f}  |  AED {s['aed_oz']:,.2f}\n"
        f"  Per gram: ${s['usd_gram']:,.2f}  |  AED {s['aed_gram']:,.2f}\n"
        "\n"
        f"<i>USD/AED rate: {_USD_TO_AED} (fixed peg)</i>"
    )
