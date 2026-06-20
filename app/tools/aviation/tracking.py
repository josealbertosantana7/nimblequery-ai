"""Live flight tracking via the OpenSky Network REST API (ADS-B).

Works anonymously (rate-limited); OPENSKY_USER/PASS raise the limits. We use OpenSky
rather than FlightRadar24, which has no free/open developer API.
"""
import math

from app.core.config import settings
from app.utils.logging import get_logger

logger = get_logger(__name__)

OPENSKY_STATES = "https://opensky-network.org/api/states/all"


def _auth():
    if settings.opensky_user and settings.opensky_pass:
        return (settings.opensky_user, settings.opensky_pass)
    return None


def _get_states(params: dict) -> list:
    import httpx

    resp = httpx.get(OPENSKY_STATES, params=params, auth=_auth(), timeout=settings.http_timeout)
    resp.raise_for_status()
    return resp.json().get("states") or []


def traffic_near(lat: float, lon: float, radius_nm: float = 30.0) -> str:
    """Aircraft currently within a bounding box around a point."""
    dlat = radius_nm / 60.0
    dlon = radius_nm / (60.0 * max(math.cos(math.radians(lat)), 0.1))
    states = _get_states({
        "lamin": lat - dlat, "lamax": lat + dlat,
        "lomin": lon - dlon, "lomax": lon + dlon,
    })
    if not states:
        return f"No ADS-B traffic seen within ~{radius_nm:.0f} NM right now (coverage varies)."
    lines = []
    for s in states[:10]:
        callsign = (s[1] or "").strip() or "(no callsign)"
        baro_alt_m, on_ground, velocity = s[7], s[8], s[9]
        alt_ft = f"{baro_alt_m * 3.281:.0f} ft" if baro_alt_m is not None else "alt n/a"
        spd = f"{velocity * 1.944:.0f} kt" if velocity is not None else "spd n/a"
        state = "on ground" if on_ground else f"{alt_ft}, {spd}"
        lines.append(f"- {callsign}: {state}")
    return f"{len(states)} aircraft nearby. Sample:\n" + "\n".join(lines)


def track_callsign(callsign: str) -> str:
    states = _get_states({})
    cs = callsign.strip().upper()
    for s in states:
        if (s[1] or "").strip().upper() == cs:
            lat, lon, baro = s[6], s[5], s[7]
            alt = f"{baro * 3.281:.0f} ft" if baro is not None else "alt n/a"
            return f"{cs} is near {lat:.3f}, {lon:.3f} at {alt} (ADS-B; may be delayed)."
    return f"No live ADS-B position found for {cs} (it may be out of coverage or not flying)."


def get_tracking_tools():
    from langchain_core.tools import tool

    @tool
    def traffic_near_point(lat: float, lon: float, radius_nm: float = 30.0) -> str:
        """List live aircraft within radius_nm of a latitude/longitude (ADS-B, situational awareness only)."""
        try:
            return traffic_near(lat, lon, radius_nm)
        except Exception as e:  # noqa: BLE001
            logger.warning("traffic_near failed: %s", e)
            return f"Flight tracking failed: {e}"

    @tool
    def track_flight(callsign: str) -> str:
        """Find the current position of a flight by callsign (e.g. UAL123)."""
        try:
            return track_callsign(callsign)
        except Exception as e:  # noqa: BLE001
            return f"Flight tracking failed: {e}"

    return [traffic_near_point, track_flight]
