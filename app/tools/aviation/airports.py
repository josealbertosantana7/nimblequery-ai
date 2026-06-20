"""Airport lookup using the free OurAirports dataset (no API key).

The CSV is downloaded once and cached locally, then queried in-memory.
"""
import csv
import os
from functools import lru_cache

from app.core.config import settings
from app.utils.logging import get_logger

logger = get_logger(__name__)

OURAIRPORTS_CSV_URL = "https://davidmegginson.github.io/ourairports-data/airports.csv"
_CACHE_PATH = os.path.join("data", "ourairports", "airports.csv")


def _ensure_csv() -> str:
    if not os.path.exists(_CACHE_PATH):
        import httpx

        os.makedirs(os.path.dirname(_CACHE_PATH), exist_ok=True)
        logger.info("Downloading OurAirports dataset...")
        resp = httpx.get(OURAIRPORTS_CSV_URL, timeout=max(settings.http_timeout, 60.0))
        resp.raise_for_status()
        with open(_CACHE_PATH, "w", encoding="utf-8") as f:
            f.write(resp.text)
    return _CACHE_PATH


@lru_cache(maxsize=1)
def _load() -> list:
    path = _ensure_csv()
    with open(path, encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _format(row: dict) -> str:
    return (
        f"{row.get('ident')} / {row.get('iata_code') or '—'} — {row.get('name')}\n"
        f"Type: {row.get('type')}; Elevation: {row.get('elevation_ft') or '?'} ft; "
        f"Location: {row.get('municipality') or '?'}, {row.get('iso_country')} "
        f"({row.get('latitude_deg')}, {row.get('longitude_deg')})"
    )


def airport_info(code: str) -> str:
    code = code.strip().upper()
    for row in _load():
        if row.get("ident", "").upper() == code or row.get("iata_code", "").upper() == code:
            return _format(row)
    return f"No airport found for code '{code}'. Try an ICAO (e.g. KAUS) or IATA (e.g. AUS) code."


def find_airport(name: str) -> str:
    q = name.strip().lower()
    matches = [r for r in _load() if q in (r.get("name", "").lower())][:5]
    if not matches:
        return f"No airports matched '{name}'."
    return "\n\n".join(_format(r) for r in matches)


def get_airport_tools():
    from langchain_core.tools import tool

    @tool
    def airport_lookup(code: str) -> str:
        """Look up an airport by ICAO or IATA code (elevation, runways area, location)."""
        try:
            return airport_info(code)
        except Exception as e:  # noqa: BLE001
            logger.warning("airport_info failed: %s", e)
            return f"Airport lookup failed: {e}"

    @tool
    def airport_search(name: str) -> str:
        """Search for airports by name or city."""
        try:
            return find_airport(name)
        except Exception as e:  # noqa: BLE001
            return f"Airport search failed: {e}"

    return [airport_lookup, airport_search]
