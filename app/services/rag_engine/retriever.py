"""Index and retrieve document chunks against the persistent vector store.

Embeddings are computed ONCE in `add_documents`; queries reuse the persisted
index. Chunks are tagged with `doc_id` metadata so retrieval is scoped to a
single uploaded document.
"""
from typing import Optional

from langchain_core.documents import Document

from app.core.config import settings
from app.services.rag_engine.vector_store import get_vector_store
from app.utils.logging import get_logger

logger = get_logger(__name__)


def add_documents(doc_id: str, chunks) -> int:
    """Embed + persist chunks (LangChain Documents or raw strings) under doc_id."""
    store = get_vector_store()
    documents = []
    for chunk in chunks:
        text = getattr(chunk, "page_content", chunk)
        meta = dict(getattr(chunk, "metadata", {}) or {})
        meta["doc_id"] = doc_id
        documents.append(Document(page_content=text, metadata=meta))
    store.add_documents(documents)
    logger.info("Indexed %d chunks for doc_id=%s", len(documents), doc_id)
    return len(documents)


def retrieve(doc_id: str, query: str, k: Optional[int] = None):
    """Return the top-k most relevant chunk texts for a query within one doc."""
    store = get_vector_store()
    k = k or settings.rag_top_k
    results = store.similarity_search(query, k=k, filter={"doc_id": doc_id})
    return [doc.page_content for doc in results]
