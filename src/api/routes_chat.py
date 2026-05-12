# Route handler for POST /chat.

import logging

from fastapi import APIRouter, Depends, HTTPException

from src.api.rate_limit import rate_limiter
from src.api.schemas import ChatRequest, ChatResponse
from src.rag.generator import generate_answer
from src.rag.retriever import retrieve
from src.trust.trust_score import calculate_trust_score, should_route_for_review, get_review_reason
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
        matches = retrieve(query=request.question, top_k=request.top_k, settings=settings)
        answer, confidence, answer_status = generate_answer(
            question=request.question,
            matches=matches,
            settings=settings,
        )

        trust_score = calculate_trust_score(
            retrieved_matches=matches,
            answer_confidence=confidence,
            answer_status=answer_status,
        )
        needs_review = should_route_for_review(trust_score)
        review_reason = get_review_reason(trust_score)

        logger.info(
            "Chat request completed",
            extra={
                "question": request.question,
                "matched_chunks": [m.chunk_id for m in matches],
                "status": answer_status,
                "confidence": confidence,
            },
        )
        return ChatResponse(
            answer=answer,
            confidence=confidence,
            answer_status=answer_status,
            trust_score=trust_score,
            sources_used=len(matches) if answer_status == "answered" else 0,
            needs_review=needs_review,
            review_reason=review_reason,
        )
    except ValueError as exc:
        logger.exception("Invalid chat request")
        raise HTTPException(status_code=422, detail=str(exc)) from exc
