"""Vector-store factory.

The rest of the app talks to a LangChain `VectorStore` and never to a concrete
backend, so the store is a config swap:
  - chroma   : local persistent store for development
  - pgvector : production (Aurora Serverless) -- Phase 2

This is how we honour "Chroma now" while keeping a path to massive scale.
"""
from app.core.config import settings
from app.services.rag_engine.embedder import get_embedder


def get_vector_store(collection: str = "documents"):
    embedder = get_embedder()

    if settings.vector_store == "chroma":
        from langchain_chroma import Chroma

        return Chroma(
            collection_name=collection,
            embedding_function=embedder,
            persist_directory=settings.chroma_dir,
        )

    if settings.vector_store == "pgvector":
        # Phase 2: langchain_postgres.PGVector(connection=settings.pg_connection, ...)
        raise NotImplementedError(
            "pgvector backend is planned for Phase 2; use VECTOR_STORE=chroma for local dev."
        )

    raise ValueError(f"Unknown VECTOR_STORE: {settings.vector_store!r}")
