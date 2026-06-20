"""Aviation supervisor: routes each query to the best specialist, then returns its
answer with a safety disclaimer appended.

A lightweight router node (LLM structured output) picks one specialist; that
specialist (a ReAct agent) answers. Single-hop routing keeps the graph simple and
robust; multi-agent collaboration can be added later.
"""
from functools import lru_cache
from typing import List, Optional

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from langgraph.graph import END, START, StateGraph
from pydantic import BaseModel, Field

from app.agents import specialists
from app.agents.common import make_react_agent
from app.agents.prompts import DISCLAIMER, GENERAL_PROMPT, ROUTER_SYSTEM
from app.agents.state import AviationState
from app.services.llm_services import get_agent_llm
from app.tools.general_tools import get_general_tools
from app.utils.logging import get_logger

logger = get_logger(__name__)


def _last_ai_text(messages) -> str:
    for m in reversed(messages):
        if isinstance(m, AIMessage):
            return m.content if isinstance(m.content, str) else str(m.content)
    return ""


@lru_cache(maxsize=1)
def _build_graph():
    mods = specialists.enabled_specialists()
    agents = {m.NAME: m.build_agent() for m in mods}
    descriptions = {m.NAME: m.DESCRIPTION for m in mods}
    routes = list(agents.keys()) + ["general"]

    llm = get_agent_llm()
    general_agent = make_react_agent(llm, get_general_tools(), GENERAL_PROMPT)

    class Route(BaseModel):
        route: str = Field(description="One of: " + ", ".join(routes))

    router_llm = llm.with_structured_output(Route)
    desc_block = "\n".join(f"- {n}: {d}" for n, d in descriptions.items())

    def router_node(state: AviationState):
        system = (
            f"{ROUTER_SYSTEM}\n\nSpecialists:\n{desc_block}\n- general: anything else.\n"
            f"Valid routes: {', '.join(routes)}."
        )
        try:
            choice = router_llm.invoke([SystemMessage(content=system)] + list(state["messages"]))
            route = (choice.route or "").strip().lower()
        except Exception as e:  # noqa: BLE001
            logger.warning("Router failed, defaulting to general: %s", e)
            route = "general"
        if route not in routes:
            route = "general"
        logger.info("Routed query to: %s", route)
        return {"route": route}

    def make_node(agent):
        def node(state: AviationState):
            result = agent.invoke({"messages": list(state["messages"])})
            return {"messages": [AIMessage(content=_last_ai_text(result["messages"]))]}
        return node

    graph = StateGraph(AviationState)
    graph.add_node("router", router_node)
    graph.add_node("general", make_node(general_agent))
    for name, agent in agents.items():
        graph.add_node(name, make_node(agent))

    graph.add_edge(START, "router")
    graph.add_conditional_edges("router", lambda s: s["route"], {r: r for r in routes})
    for r in routes:
        graph.add_edge(r, END)
    return graph.compile()


def run_supervisor(prompt: str, history: Optional[List[BaseMessage]] = None) -> str:
    """Route a prompt to the right specialist; return its answer + safety disclaimer."""
    graph = _build_graph()
    messages: List[BaseMessage] = list(history or []) + [HumanMessage(content=prompt)]
    result = graph.invoke({"messages": messages, "route": None})
    answer = _last_ai_text(result["messages"]) or "Sorry, I couldn't produce an answer."
    return f"{answer}\n\n{DISCLAIMER}"
