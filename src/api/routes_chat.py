# Route handler for POST /chat.

import logging

from fastapi import APIRouter, Depends, HTTPException

from src.api.rate_limit import rate_limiter
from src.api.schemas import ChatRequest, ChatResponse, SourceCitation
from src.rag.generator import generate_answer
from src.rag.retriever import retrieve
from src.utils.config import get_settings

logger = logging.getLogger(__name__)
router = APIRouter()
settings = get_settings()


@router.post(
    "/chat",
    response_model=ChatResponse,
    dependencies=[
        Depends(
            rate_limiter.limit(
                requests=settings.chat_rate_limit_per_minute,
                seconds=60,
            )
        )
    ],
)
def chat(request: ChatRequest) -> ChatResponse:
    try:
        # Pass settings so both retrieve and generate_answer use real APIs
        matches = retrieve(query=request.question, top_k=request.top_k, settings=settings)
        answer, confidence, status = generate_answer(
            question=request.question,
            matches=matches,
            settings=settings,
        )
        sources = [
            SourceCitation(
                document_id=match.document_id,
                title=match.title,
                chunk_id=match.chunk_id,
            )
            for match in matches
        ]
        if status == "unsupported":
            sources = []

        logger.info(
            "Chat request completed",
            extra={
                "question": request.question,
                "matched_chunks": [match.chunk_id for match in matches],
                "status": status,
                "confidence": confidence,
            },
        )
        return ChatResponse(
            answer=answer,
            sources=sources,
            confidence=confidence,
            status=status,
        )
    except ValueError as exc:
        logger.exception("Invalid chat request")
        raise HTTPException(status_code=422, detail=str(exc)) from exc
