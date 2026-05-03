import logging
from typing import Any

from src.api.schemas import DocumentIngestItem
from src.rag.chunking import DocumentChunk, chunk_document
from src.utils.config import Settings

logger = logging.getLogger(__name__)


def ingest_documents(
    documents: list[DocumentIngestItem],
    settings: Settings,
) -> tuple[list[DocumentChunk], dict[str, Any]]:
    chunks: list[DocumentChunk] = []

    for document in documents:
        metadata = {
            "title": document.title,
            "source_type": document.source_type,
            "department": document.department,
        }
        try:
            doc_chunks = chunk_document(
                document_id=document.id,
                text=document.text,
                metadata=metadata,
                chunk_size=settings.chunk_size,
                chunk_overlap=settings.chunk_overlap,
            )
            chunks.extend(doc_chunks)
            logger.debug(
                "Ingested document '%s' into %d chunks", document.id, len(doc_chunks)
            )
        except ValueError as exc:
            logger.exception("Failed to ingest document '%s'", document.id)
            raise ValueError(f"Document '{document.id}' ingestion failed") from exc

    summary = {
        "documents_received": len(documents),
        "chunks_created": len(chunks),
        "status": "success",
    }
    logger.info("Documents ingested: %s", summary)
    return chunks, summary
