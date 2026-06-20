"""Aerospace Engineering specialist (aerodynamics + performance calculators)."""
from app.agents.prompts import AERO_PROMPT

NAME = "aero"
DESCRIPTION = (
    "Aerospace engineering and aircraft performance: principles of flight, aerodynamics, "
    "density altitude, wind components, and weight & balance calculations."
)


def build_agent():
    from app.agents.common import kb_search_tool, make_react_agent
    from app.services.llm_services import get_agent_llm
    from app.tools.aviation.calculators import get_calculator_tools
    from app.tools.general_tools import get_general_tools

    tools = get_calculator_tools() + [kb_search_tool()] + get_general_tools()
    return make_react_agent(get_agent_llm(), tools, AERO_PROMPT)
