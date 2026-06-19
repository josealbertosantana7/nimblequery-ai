
import ast
import operator
import os
from dotenv import load_dotenv

# Load environment variables early
load_dotenv()

from langchain_aws import ChatBedrock
from langchain_core.tools import Tool
from langchain_community.utilities import GoogleSerperAPIWrapper
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage
from typing import List, Optional
from pydantic import BaseModel
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import create_react_agent


# --- Define the agent state schema (best practice: use Pydantic)
class AgentState(BaseModel):
    messages: List[BaseMessage]
    output: Optional[str] = None

# --- Define your tools
def logic_reasoning_tool(query: str) -> str:
    return f"I am reasoning about: {query}"

# --- Safe arithmetic evaluator (no eval(); avoids arbitrary code execution)
_ALLOWED_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}

def _safe_eval(node):
    if isinstance(node, ast.Expression):
        return _safe_eval(node.body)
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return node.value
    if isinstance(node, ast.BinOp) and type(node.op) in _ALLOWED_OPERATORS:
        return _ALLOWED_OPERATORS[type(node.op)](_safe_eval(node.left), _safe_eval(node.right))
    if isinstance(node, ast.UnaryOp) and type(node.op) in _ALLOWED_OPERATORS:
        return _ALLOWED_OPERATORS[type(node.op)](_safe_eval(node.operand))
    raise ValueError("Unsupported or unsafe expression")

def calculator_tool(expression: str) -> str:
    try:
        return str(_safe_eval(ast.parse(expression, mode="eval")))
    except Exception as e:
        return f"Error evaluating expression: {e}"

search = GoogleSerperAPIWrapper()

tools = [
    Tool(
        name="google_search",
        func=search.run,
        description="Useful for answering questions about current events or factual information."
    ),
    Tool(
        name="calculator",
        func=calculator_tool,
        description="Useful for evaluating mathematical expressions like addition, multiplication, etc."
    ),
    Tool(
        name="reasoning_tool",
        func=logic_reasoning_tool,
        description="Useful for complex reasoning or logic questions."
    ),
]

# --- Instantiate Claude via Bedrock as a ChatModel
llm = ChatBedrock(
    model_id=os.getenv("BEDROCK_MODEL_ID", "anthropic.claude-3-haiku-20240307-v1:0"),
    region_name=os.getenv("AWS_REGION", "us-west-2")
)

# --- Create the agent executor
agent_executor = create_react_agent(llm, tools)

# --- Build the LangGraph workflow
graph = StateGraph(AgentState)
graph.add_node("agent", agent_executor)
graph.set_entry_point("agent")
graph.add_edge("agent", END)

workflow = graph.compile()

# --- Agent runner function: returns both reply and updated history
# --- Agent runner function: returns both reply and updated history
def run_agent(prompt: str, chat_history: Optional[List[BaseMessage]] = None) -> str:
    if chat_history is None:
        chat_history = []
    # Do NOT append HumanMessage here!
    model_history = chat_history + [HumanMessage(content=prompt)]
    result = workflow.invoke({"messages": model_history})
    ai_reply = result.get("output")
    if ai_reply is None:
        ai_msgs = [m for m in result["messages"] if isinstance(m, AIMessage)]
        ai_reply = ai_msgs[-1].content if ai_msgs else ""
    return ai_reply

# NOTE: PDF retrieval-augmented generation lives in
# app/services/rag_engine/rag_llm.py (run_rag_agent). Import it from there.
