"""Ingest aviation PDFs into the persistent knowledge base.

Drop public-domain FAA PDFs into ``data/aviation_docs/`` and run:

    python -m scripts.ingest_aviation_docs            # default dir
    python -m scripts.ingest_aviation_docs /path/dir  # custom dir

Each PDF is chunked and embedded once into the ``aviation_kb`` Chroma collection,
which the Regulations and Aerospace agents query via ``retriever.retrieve_kb``.

Suggested public-domain sources (FAA):
- Pilot's Handbook of Aeronautical Knowledge (PHAK)
- Airplane Flying Handbook
- Aeronautical Information Manual (AIM)
"""
import os
import sys
from typing import Optional

from app.core.config import settings
from app.services.rag_engine.loader import load_and_split
from app.services.rag_engine.retriever import add_documents
from app.utils.logging import get_logger

logger = get_logger(__name__)


def ingest_dir(directory: Optional[str] = None) -> int:
    """Chunk + embed every PDF in `directory` into the aviation_kb collection."""
    directory = directory or settings.aviation_docs_dir
    os.makedirs(directory, exist_ok=True)

    pdfs = [f for f in sorted(os.listdir(directory)) if f.lower().endswith(".pdf")]
    if not pdfs:
        logger.warning("No PDFs found in %s — drop FAA handbook PDFs there and re-run.", directory)
        return 0

    total = 0
    for fname in pdfs:
        path = os.path.join(directory, fname)
        logger.info("Ingesting %s ...", fname)
        chunks = load_and_split(path)
        n = add_documents(
            doc_id=fname,
            chunks=chunks,
            collection=settings.aviation_kb_collection,
        )
        total += n
        logger.info("  -> indexed %d chunks", n)

    logger.info(
        "Done. Indexed %d chunks from %d PDF(s) into '%s'.",
        total, len(pdfs), settings.aviation_kb_collection,
    )
    return total


if __name__ == "__main__":
    ingest_dir(sys.argv[1] if len(sys.argv) > 1 else None)
