"""The aviation tool loader must fall back to local tools when MCP is unavailable."""
import app.tools.mcp_loader as ml
from app.core.config import settings


def test_local_fallback_when_mcp_disabled(monkeypatch):
    # Force the local path and reset the module's memoized registry.
    monkeypatch.setattr(settings, "use_mcp_tools", False)
    monkeypatch.setattr(ml, "_registry", None)
    monkeypatch.setattr(ml, "_resolved", False)

    tools = ml.get_aviation_tools(["get_metar", "get_taf"])
    assert sorted(t.name for t in tools) == ["get_metar", "get_taf"]


def test_unknown_tool_names_are_skipped(monkeypatch):
    monkeypatch.setattr(settings, "use_mcp_tools", False)
    monkeypatch.setattr(ml, "_registry", None)
    monkeypatch.setattr(ml, "_resolved", False)

    tools = ml.get_aviation_tools(["get_metar", "does_not_exist"])
    assert [t.name for t in tools] == ["get_metar"]
