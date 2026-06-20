"""Airport & Planning specialist (airport data + NOTAMs)."""
from app.agents.prompts import AIRPORT_PROMPT

NAME = "airport"
DESCRIPTION = (
    "Airport information (location, elevation, identifiers) and NOTAMs to support "
    "flight-planning practice."
)


def build_agent():
    from app.agents.common import make_react_agent
    from app.services.llm_services import get_agent_llm
    from app.tools.mcp_loader import get_aviation_tools
    from app.tools.general_tools import get_general_tools

    tools = get_aviation_tools(
        ["airport_lookup", "airport_search", "airport_notams"]
    ) + get_general_tools()
    return make_react_agent(get_agent_llm(), tools, AIRPORT_PROMPT)
