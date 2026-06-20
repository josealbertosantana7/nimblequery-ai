"""General-purpose tools shared by agents: a safe calculator and web search.

The safe calculator uses an AST allow-list (NO eval()), so it cannot execute
arbitrary code.
"""
import ast
import operator

from app.core.config import settings

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


def safe_calculate(expression: str) -> str:
    try:
        return str(_safe_eval(ast.parse(expression, mode="eval")))
    except Exception as e:
        return f"Error evaluating expression: {e}"


def get_general_tools():
    """Lazily build the shared LangChain tools (imported here to keep this module light)."""
    from langchain_core.tools import tool

    @tool
    def calculator(expression: str) -> str:
        """Evaluate a basic arithmetic expression, e.g. '2 + 3 * 4'."""
        return safe_calculate(expression)

    tools = [calculator]

    if settings.serper_api_key:
        from langchain_community.utilities import GoogleSerperAPIWrapper

        search = GoogleSerperAPIWrapper()

        @tool
        def web_search(query: str) -> str:
            """Search the web for current or general information."""
            return search.run(query)

        tools.append(web_search)

    return tools
