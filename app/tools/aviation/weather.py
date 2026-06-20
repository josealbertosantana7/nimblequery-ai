"""Aviation weather tools.

- METAR / TAF from aviationweather.gov (NOAA Aviation Weather Center) — free, no key.
- Point forecast from Windy — requires WINDY_API_KEY.
"""
from app.core.config import settings
from app.utils.logging import get_logger

logger = get_logger(__name__)

AWC_BASE = "https://aviationweather.gov/api/data"
WINDY_URL = "https://api.windy.com/api/point-forecast/v2"


def _awc(path: str, ids: str) -> str:
    import httpx

    resp = httpx.get(
        f"{AWC_BASE}/{path}",
        params={"ids": ids.upper(), "format": "raw"},
        timeout=settings.http_timeout,
    )
    resp.raise_for_status()
    return resp.text.strip()


def fetch_metar(icao: str) -> str:
    text = _awc("metar", icao)
    return text or f"No current METAR found for {icao.upper()}."


def fetch_taf(icao: str) -> str:
    text = _awc("taf", icao)
    return text or f"No current TAF found for {icao.upper()}."


def fetch_windy_point(lat: float, lon: float) -> str:
    if not settings.windy_api_key:
        return "Windy forecast is not configured (set WINDY_API_KEY)."
    import httpx

    payload = {
        "lat": lat,
        "lon": lon,
        "model": "gfs",
        "parameters": ["wind", "windGust", "temp"],
        "levels": ["surface"],
        "key": settings.windy_api_key,
    }
    resp = httpx.post(WINDY_URL, json=payload, timeout=settings.http_timeout)
    resp.raise_for_status()
    return resp.text  # raw JSON; the agent summarizes for the user


def get_weather_tools():
    from langchain_core.tools import tool

    @tool
    def get_metar(icao: str) -> str:
        """Get the current METAR (weather observation) for an ICAO airport code, e.g. KAUS."""
        try:
            return fetch_metar(icao)
        except Exception as e:  # noqa: BLE001
            logger.warning("METAR lookup failed for %s: %s", icao, e)
            return f"Weather lookup failed: {e}"

    @tool
    def get_taf(icao: str) -> str:
        """Get the current TAF (terminal aerodrome forecast) for an ICAO airport code."""
        try:
            return fetch_taf(icao)
        except Exception as e:  # noqa: BLE001
            logger.warning("TAF lookup failed for %s: %s", icao, e)
            return f"Forecast lookup failed: {e}"

    tools = [get_metar, get_taf]

    if settings.windy_api_key:

        @tool
        def point_forecast(lat: float, lon: float) -> str:
            """Get a Windy point forecast (wind/temp) for a latitude/longitude."""
            try:
                return fetch_windy_point(lat, lon)
            except Exception as e:  # noqa: BLE001
                return f"Windy forecast failed: {e}"

        tools.append(point_forecast)

    return tools
