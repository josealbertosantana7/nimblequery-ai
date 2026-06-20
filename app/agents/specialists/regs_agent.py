"""Regulations & Knowledge specialist (FARs / AIM / FAA handbooks)."""
from app.agents.prompts import REGS_PROMPT

NAME = "regs"
DESCRIPTION = (
    "FAA regulations (14 CFR / FARs), the AIM, and airman knowledge from FAA handbooks — "
    "e.g. student-pilot privileges, currency, airspace and right-of-way rules."
)


def build_agent():
    from app.agents.common import kb_search_tool, make_react_agent
    from app.services.llm_services import get_agent_llm
    from app.tools.mcp_loader import get_aviation_tools
    from app.tools.general_tools import get_general_tools

    tools = [kb_search_tool()] + get_aviation_tools(
        ["search_regulations", "airport_notams"]
    ) + get_general_tools()
    return make_react_agent(get_agent_llm(), tools, REGS_PROMPT)
