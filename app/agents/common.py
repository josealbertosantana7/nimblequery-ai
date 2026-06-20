"""Shared helpers for the agent layer."""


def make_react_agent(llm, tools, prompt):
    """Build a ReAct agent, tolerant of the create_react_agent signature change
    across langgraph versions (`prompt=` in newer, `state_modifier=` in older)."""
    from langgraph.prebuilt import create_react_agent

    try:
        return create_react_agent(llm, tools, prompt=prompt)
    except TypeError:
        return create_react_agent(llm, tools, state_modifier=prompt)


def kb_search_tool():
    """A LangChain tool that searches the aviation knowledge base (shared by the
    regulations and aerospace-engineering agents)."""
    from langchain_core.tools import tool

    @tool
    def search_aviation_kb(query: str) -> str:
        """Search the aviation knowledge base (FAA handbooks / AIM) for relevant passages."""
        from app.services.rag_engine.retriever import retrieve_kb

        try:
            chunks = retrieve_kb(query)
        except Exception as e:  # noqa: BLE001
            return f"Knowledge base unavailable: {e}"
        return "\n\n".join(chunks) if chunks else "No knowledge-base match (the KB may be empty)."

    return search_aviation_kb
