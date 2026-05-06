# Route handler for POST /ingest.
# Receives a list of documents, passes them through the ingestion pipeline,
# and returns a summary of how many chunks were created.

import logging

from fastapi import APIRouter, Depends, HTTPException

from src.api.rate_limit import rate_limiter
from src.api.schemas import IngestRequest, IngestResponse
from src.rag.ingest import ingest_documents
from src.utils.config import get_settings

logger = logging.getLogger(__name__)
router = APIRouter()
settings = get_settings()


@router.post(
    "/ingest",
    response_model=IngestResponse,
    dependencies=[
        Depends(
            rate_limiter.limit(
                requests=settings.ingest_rate_limit_per_minute,
                seconds=60,
            )
        )
    ],
)
def ingest(request: IngestRequest) -> IngestResponse:
    try:
        # The underscore discards the chunk list — the caller only needs the summary.
        # Chunks will be stored in Pinecone in Week 2.
        _, summary = ingest_documents(request.documents, settings)
        return IngestResponse(**summary)
    except (ValueError, RuntimeError) as exc:
        # ValueError: invalid document content (e.g. empty text after stripping)
        # RuntimeError: misconfigured environment (e.g. bad CHUNK_SIZE in .env)
        logger.exception("Invalid ingestion request")
        raise HTTPException(status_code=422, detail=str(exc)) from exc
