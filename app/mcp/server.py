"""Aviation tools exposed as an MCP server (FastMCP).

This wraps the pure functions in app/tools/aviation/* as MCP tools so specialist
agents (or any MCP client) can consume them over a standard protocol. Run it as a
streamable-HTTP service:

    python -m app.mcp.server            # serves http://localhost:9000/mcp

Tool names here MUST match the local tool names in app/tools/aviation/* so the
loader's local fallback is a drop-in replacement.
"""
from mcp.server.fastmcp import FastMCP

from app.core.config import settings
from app.tools.aviation import airports, faa, tracking, weather

mcp = FastMCP("aviation-tools", host="0.0.0.0", port=9000)


@mcp.tool()
def get_metar(icao: str) -> str:
    """Current METAR (observation) for an ICAO airport code, e.g. KAUS."""
    return weather.fetch_metar(icao)


@mcp.tool()
def get_taf(icao: str) -> str:
    """Current TAF (forecast) for an ICAO airport code."""
    return weather.fetch_taf(icao)


@mcp.tool()
def point_forecast(lat: float, lon: float) -> str:
    """Windy point forecast (wind/temp) for a latitude/longitude (needs WINDY_API_KEY)."""
    return weather.fetch_windy_point(lat, lon)


@mcp.tool()
def traffic_near_point(lat: float, lon: float, radius_nm: float = 30.0) -> str:
    """Live aircraft within radius_nm of a latitude/longitude (ADS-B / OpenSky)."""
    return tracking.traffic_near(lat, lon, radius_nm)


@mcp.tool()
def track_flight(callsign: str) -> str:
    """Current position of a flight by callsign (e.g. UAL123)."""
    return tracking.track_callsign(callsign)


@mcp.tool()
def airport_lookup(code: str) -> str:
    """Airport information by ICAO or IATA code."""
    return airports.airport_info(code)


@mcp.tool()
def airport_search(name: str) -> str:
    """Search for airports by name or city."""
    return airports.find_airport(name)


@mcp.tool()
def search_regulations(query: str) -> str:
    """Search U.S. aviation regulations (14 CFR / FARs) via the eCFR."""
    return faa.search_far(query)


@mcp.tool()
def airport_notams(icao: str) -> str:
    """Current (unofficial) NOTAMs for an ICAO airport code."""
    return faa.get_notams(icao)


if __name__ == "__main__":
    # settings imported so .env (API keys) is loaded before the server starts.
    _ = settings
    mcp.run(transport="streamable-http")
