"""RAG answer generation.

A document is uploaded + embedded once (see retriever.add_documents); questions
then retrieve the most relevant chunks for that doc_id and ground the LLM answer
in them. No more rebuilding/re-embedding the whole document per question.
"""
from functools import lru_cache

from langchain_aws import ChatBedrock

from app.core.config import settings
from app.services.rag_engine.retriever import retrieve
from app.utils.logging import get_logger

logger = get_logger(__name__)


@lru_cache
def _get_llm() -> ChatBedrock:
    return ChatBedrock(
        model_id=settings.bedrock_model_id,
        region_name=settings.aws_region,
    )


def run_rag_agent(doc_id: str, question: str) -> str:
    """Answer a question grounded in a previously uploaded document."""
    chunks = retrieve(doc_id, question)
    context = "\n\n".join(chunks)
    prompt = (
        "Use the following context to answer the question. "
        "If the answer is not in the context, say you don't know.\n\n"
        f"Context:\n{context}\n\nQuestion: {question}"
    )
    answer = _get_llm().invoke(prompt)
    # invoke() returns an AIMessage; return plain text for the API/UI.
    return getattr(answer, "content", str(answer))
