"""Load aviation tools from the MCP server, with a memoized fallback to the local
in-process tools so the app never hard-breaks if the MCP server is down.

`get_aviation_tools(names)` returns the named tools, resolved once (the registry —
MCP or local — is chosen on first use and cached for the process).
"""
from typing import List, Optional

from app.core.config import settings
from app.utils.logging import get_logger

logger = get_logger(__name__)

_registry: Optional[dict] = None  # name -> LangChain tool
_resolved = False


def _load_from_mcp() -> dict:
    import asyncio

    from langchain_mcp_adapters.client import MultiServerMCPClient

    client = MultiServerMCPClient(
        {"aviation": {"transport": settings.mcp_transport, "url": settings.mcp_aviation_url}}
    )
    tools = asyncio.run(client.get_tools())
    logger.info("Loaded %d aviation tools from MCP server at %s", len(tools), settings.mcp_aviation_url)
    return {t.name: t for t in tools}


def _load_local() -> dict:
    from app.tools.aviation.airports import get_airport_tools
    from app.tools.aviation.faa import get_faa_tools
    from app.tools.aviation.tracking import get_tracking_tools
    from app.tools.aviation.weather import get_weather_tools

    tools = get_weather_tools() + get_tracking_tools() + get_airport_tools() + get_faa_tools()
    return {t.name: t for t in tools}


def _get_registry() -> dict:
    global _registry, _resolved
    if not _resolved:
        _resolved = True
        if settings.use_mcp_tools:
            try:
                _registry = _load_from_mcp()
            except Exception as e:  # noqa: BLE001
                logger.warning("MCP tools unavailable (%s); falling back to local tools", e)
                _registry = None
        if _registry is None:
            _registry = _load_local()
    return _registry


def get_aviation_tools(names: List[str]):
    """Return the named aviation tools (MCP-served if available, else local)."""
    registry = _get_registry()
    return [registry[n] for n in names if n in registry]
