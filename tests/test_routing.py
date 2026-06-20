"""Structural tests for the supervisor graph + specialist registry.

These build the graph offline (no Bedrock calls happen until invocation), so they
validate the wiring without needing AWS or a network.
"""
import app.tools.mcp_loader as ml
from app.agents import specialists
from app.core.config import settings


def test_enabled_specialists_default():
    names = {m.NAME for m in specialists.enabled_specialists()}
    assert names == {"regs", "weather", "tracking", "airport", "aero"}


def test_supervisor_graph_builds(monkeypatch):
    # Use local tools so building does not attempt an MCP connection.
    monkeypatch.setattr(settings, "use_mcp_tools", False)
    monkeypatch.setattr(ml, "_registry", None)
    monkeypatch.setattr(ml, "_resolved", False)

    from app.agents.supervisor import _build_graph

    _build_graph.cache_clear()
    graph = _build_graph()
    nodes = set(graph.get_graph().nodes)
    for expected in ("router", "regs", "weather", "tracking", "airport", "aero", "general"):
        assert expected in nodes
