import httpx
from utils.logger import get_logger

logger = get_logger(__name__)

_TROY_OZ_TO_GRAMS = 31.1035
# AED has been pegged to USD at this fixed rate since 1997
_AED_PER_USD = 3.6725
_METALS_API_URL = "https://api.metals.live/v1/spot"


async def get_gold_price_aed_per_gram() -> float | None:
    """Return live gold spot price in AED per gram, or None on failure."""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(_METALS_API_URL)
            resp.raise_for_status()
            data = resp.json()

        if isinstance(data, list):
            price_usd_per_oz = data[0].get("gold") if data else None
        elif isinstance(data, dict):
            price_usd_per_oz = data.get("gold")
        else:
            price_usd_per_oz = None

        if price_usd_per_oz is None:
            return None

        price_aed_per_gram = (float(price_usd_per_oz) / _TROY_OZ_TO_GRAMS) * _AED_PER_USD
        return round(price_aed_per_gram, 2)
    except Exception as exc:
        logger.error("Failed to fetch gold price", extra={"error": str(exc)})
        return None
