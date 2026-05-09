# Route handler for POST /retrieve.

import logging

from fastapi import APIRouter, Depends, HTTPException

from src.api.rate_limit import rate_limiter
from src.api.schemas import RetrieveRequest, RetrieveResponse, RetrievedChunk
from src.rag.retriever import retrieve
from src.utils.config import get_settings

logger = logging.getLogger(__name__)
router = APIRouter()
settings = get_settings()


@router.post(
    "/retrieve",
    response_model=RetrieveResponse,
    dependencies=[
        Depends(
            rate_limiter.limit(
                requests=settings.retrieve_rate_limit_per_minute,
                seconds=60,
            )
        )
    ],
)
def retrieve_chunks(request: RetrieveRequest) -> RetrieveResponse:
    try:
        # Pass settings so retrieve routes to Pinecone when the key is configured
        matches = retrieve(query=request.query, top_k=request.top_k, settings=settings)
        return RetrieveResponse(
            query=request.query,
            matches=[
                RetrievedChunk(
                    chunk_id=match.chunk_id,
                    document_id=match.document_id,
                    title=match.title,
                    score=match.score,
                    text=match.text,
                )
                for match in matches
            ],
        )
    except ValueError as exc:
        logger.exception("Invalid retrieval request")
        raise HTTPException(status_code=422, detail=str(exc)) from exc
