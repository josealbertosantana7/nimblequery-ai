"""Aviation Weather specialist (METAR / TAF / winds)."""
from app.agents.prompts import WEATHER_PROMPT

NAME = "weather"
DESCRIPTION = (
    "Aviation weather: current METARs, TAF forecasts, winds and conditions for airports, "
    "decoded into plain language and flight categories (VFR/MVFR/IFR)."
)


def build_agent():
    from app.agents.common import make_react_agent
    from app.services.llm_services import get_agent_llm
    from app.tools.mcp_loader import get_aviation_tools
    from app.tools.general_tools import get_general_tools

    tools = get_aviation_tools(["get_metar", "get_taf", "point_forecast"]) + get_general_tools()
    return make_react_agent(get_agent_llm(), tools, WEATHER_PROMPT)
