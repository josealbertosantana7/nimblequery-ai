"""Shared graph state for the aviation supervisor."""
from typing import Optional

from typing_extensions import Annotated, TypedDict

from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages


class AviationState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    route: Optional[str]
