"""Flight Tracking specialist (live ADS-B via OpenSky)."""
from app.agents.prompts import TRACKING_PROMPT

NAME = "tracking"
DESCRIPTION = (
    "Live aircraft positions and nearby traffic from ADS-B (OpenSky) — "
    "e.g. 'what's flying near KSFO' or 'where is UAL123'."
)


def build_agent():
    from app.agents.common import make_react_agent
    from app.services.llm_services import get_agent_llm
    from app.tools.mcp_loader import get_aviation_tools
    from app.tools.general_tools import get_general_tools

    tools = get_aviation_tools(["traffic_near_point", "track_flight"]) + get_general_tools()
    return make_react_agent(get_agent_llm(), tools, TRACKING_PROMPT)
