"""FAA regulatory tools.

- search_far: full-text search of the federal regulations via the free eCFR API,
  scoped to Title 14 (Aeronautics and Space).
- get_notams: current NOTAMs via the FAA NOTAM API (requires FAA_NOTAM_CLIENT_ID/SECRET).
"""
from app.core.config import settings
from app.utils.logging import get_logger

logger = get_logger(__name__)

ECFR_SEARCH = "https://www.ecfr.gov/api/search/v1/results"
NOTAM_URL = "https://external-api.faa.gov/notamapi/v1/notams"


def search_far(query: str, limit: int = 5) -> str:
    import httpx

    resp = httpx.get(
        ECFR_SEARCH,
        params={"query": query, "per_page": limit, "hierarchy[title]": "14"},
        timeout=settings.http_timeout,
        headers={"Accept": "application/json"},
    )
    resp.raise_for_status()
    results = (resp.json() or {}).get("results") or []
    if not results:
        return f"No Title 14 (FAR) results for '{query}'. Confirm against the current eCFR."
    out = []
    for r in results[:limit]:
        headings = r.get("hierarchy_headings") or {}
        label = " / ".join(v for v in headings.values() if v) or r.get("label_level") or "FAR"
        excerpt = (r.get("full_text_excerpt") or "").strip()
        out.append(f"• {label}\n  {excerpt}")
    return "Source: eCFR Title 14 (verify against the current text):\n" + "\n".join(out)


def get_notams(icao: str) -> str:
    if not (settings.faa_notam_client_id and settings.faa_notam_client_secret):
        return ("NOTAMs are not configured (set FAA_NOTAM_CLIENT_ID / FAA_NOTAM_CLIENT_SECRET). "
                "Get official NOTAMs from a preflight briefing.")
    import httpx

    resp = httpx.get(
        NOTAM_URL,
        params={"icaoLocation": icao.upper(), "pageSize": 20},
        headers={
            "client_id": settings.faa_notam_client_id,
            "client_secret": settings.faa_notam_client_secret,
        },
        timeout=settings.http_timeout,
    )
    resp.raise_for_status()
    items = (resp.json() or {}).get("items") or []
    if not items:
        return f"No NOTAMs returned for {icao.upper()} (still get an official briefing)."
    return f"{len(items)} NOTAM(s) for {icao.upper()} (unofficial — verify):\n" + "\n".join(
        f"- {i.get('properties', {}).get('coreNOTAMData', {}).get('notam', {}).get('text', '')[:200]}"
        for i in items[:10]
    )


def get_faa_tools():
    from langchain_core.tools import tool

    @tool
    def search_regulations(query: str) -> str:
        """Search U.S. aviation regulations (14 CFR / FARs) by keyword via the eCFR."""
        try:
            return search_far(query)
        except Exception as e:  # noqa: BLE001
            logger.warning("search_far failed: %s", e)
            return f"Regulation search failed: {e}"

    @tool
    def airport_notams(icao: str) -> str:
        """Get current (unofficial) NOTAMs for an ICAO airport code."""
        try:
            return get_notams(icao)
        except Exception as e:  # noqa: BLE001
            return f"NOTAM lookup failed: {e}"

    return [search_regulations, airport_notams]
