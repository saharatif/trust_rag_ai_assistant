# Human review endpoints for TrustRAG.
# Allows human reviewers to inspect, approve, reject, or modify AI responses.

import logging
from typing import Literal

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from src.db import queries
from src.db.database import get_db
from src.utils.config import get_settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/review", tags=["review"])


# ============================================================================
# Request/Response Models
# ============================================================================


class ReviewItemDetail(BaseModel):
    """A pending review with full context."""

    review_id: str
    response_id: str
    question: str
    answer: str
    confidence: str
    trust_score: float
    review_reason: str
    created_at: str


class ListReviewsResponse(BaseModel):
    """List of pending reviews."""

    total: int
    items: list[ReviewItemDetail]


class ApproveReviewRequest(BaseModel):
    """Approve a review with optional comments."""

    reviewer_id: str = Field(min_length=1)
    notes: str | None = None


class RejectReviewRequest(BaseModel):
    """Reject a review (response will not be delivered)."""

    reviewer_id: str = Field(min_length=1)
    reason: str = Field(min_length=1)


class ModifyReviewRequest(BaseModel):
    """Modify an AI response before approval."""

    reviewer_id: str = Field(min_length=1)
    corrected_answer: str = Field(min_length=1)
    notes: str | None = None


class ReviewActionResponse(BaseModel):
    """Response after taking action on a review."""

    review_id: str
    response_id: str
    status: str
    message: str


# ============================================================================
# Endpoints
# ============================================================================


@router.get(
    "/pending",
    response_model=ListReviewsResponse,
    summary="List pending reviews",
    description="Get all responses awaiting human review, newest first.",
)
def list_pending_reviews(limit: int = Field(default=50, ge=1, le=500)):
    """List all pending reviews."""
    try:
        reviews = queries.list_pending_reviews(limit=limit)

        items = []
        for review in reviews:
            response = queries.get_ai_response(review["response_id"])
            if not response:
                logger.warning(f"Response {review['response_id']} not found")
                continue

            items.append(
                ReviewItemDetail(
                    review_id=review["id"],
                    response_id=review["response_id"],
                    question=response.get("question", ""),
                    answer=response.get("answer", ""),
                    confidence=response.get("confidence", "unknown"),
                    trust_score=response.get("trust_score", 0.0),
                    review_reason=review.get("review_reason", ""),
                    created_at=review.get("created_at", ""),
                )
            )

        logger.info(f"Retrieved {len(items)} pending reviews")
        return ListReviewsResponse(total=len(items), items=items)

    except Exception as e:
        logger.error(f"Error listing reviews: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list pending reviews",
        )


@router.post(
    "/{review_id}/approve",
    response_model=ReviewActionResponse,
    summary="Approve a review",
    description="Approve an AI response for delivery to the user.",
)
def approve_review(review_id: str, request: ApproveReviewRequest):
    """Approve a review and mark response as ready for delivery."""
    try:
        review = queries.get_review(review_id)
        if not review:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Review not found"
            )

        if review["status"] != "pending":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Review is already {review['status']}",
            )

        # Update review status
        queries.update_review(
            review_id=review_id,
            status="approved",
            reviewer_id=request.reviewer_id,
            reviewer_notes=request.notes,
        )

        # Log audit trail
        queries.log_audit(
            action="review_approved",
            resource_type="response",
            resource_id=review["response_id"],
            actor_type="reviewer",
            actor_id=request.reviewer_id,
            details={"review_id": review_id, "notes": request.notes},
        )

        logger.info(
            f"Review {review_id} approved by {request.reviewer_id}"
        )

        return ReviewActionResponse(
            review_id=review_id,
            response_id=review["response_id"],
            status="approved",
            message="Response approved and will be delivered to user.",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error approving review: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to approve review",
        )


@router.post(
    "/{review_id}/reject",
    response_model=ReviewActionResponse,
    summary="Reject a review",
    description="Reject an AI response; it will not be delivered to the user.",
)
def reject_review(review_id: str, request: RejectReviewRequest):
    """Reject a review and do not deliver the response."""
    try:
        review = queries.get_review(review_id)
        if not review:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Review not found"
            )

        if review["status"] != "pending":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Review is already {review['status']}",
            )

        # Update review status
        queries.update_review(
            review_id=review_id,
            status="rejected",
            reviewer_id=request.reviewer_id,
            reviewer_notes=request.reason,
        )

        # Log audit trail
        queries.log_audit(
            action="review_rejected",
            resource_type="response",
            resource_id=review["response_id"],
            actor_type="reviewer",
            actor_id=request.reviewer_id,
            details={"review_id": review_id, "reason": request.reason},
        )

        logger.info(f"Review {review_id} rejected by {request.reviewer_id}")

        return ReviewActionResponse(
            review_id=review_id,
            response_id=review["response_id"],
            status="rejected",
            message="Response rejected and will not be delivered.",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error rejecting review: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to reject review",
        )


@router.post(
    "/{review_id}/modify",
    response_model=ReviewActionResponse,
    summary="Modify and approve a review",
    description="Edit the AI response and approve it for delivery.",
)
def modify_review(review_id: str, request: ModifyReviewRequest):
    """Modify an AI response and mark it as approved."""
    try:
        review = queries.get_review(review_id)
        if not review:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Review not found"
            )

        if review["status"] != "pending":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Review is already {review['status']}",
            )

        response = queries.get_ai_response(review["response_id"])
        if not response:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Associated response not found",
            )

        # Update the AI response with the corrected answer
        db = get_db()
        db.execute(
            """
            UPDATE ai_responses SET answer = ? WHERE id = ?
            """,
            (request.corrected_answer, response["id"]),
        )
        db.commit()

        # Mark review as modified and approved
        queries.update_review(
            review_id=review_id,
            status="modified",
            reviewer_id=request.reviewer_id,
            reviewer_notes=request.notes,
        )

        # Log audit trail
        queries.log_audit(
            action="review_modified",
            resource_type="response",
            resource_id=review["response_id"],
            actor_type="reviewer",
            actor_id=request.reviewer_id,
            details={
                "review_id": review_id,
                "original_answer": response.get("answer"),
                "corrected_answer": request.corrected_answer,
                "notes": request.notes,
            },
        )

        logger.info(
            f"Review {review_id} modified and approved by {request.reviewer_id}"
        )

        return ReviewActionResponse(
            review_id=review_id,
            response_id=review["response_id"],
            status="modified",
            message="Response modified and approved. It will be delivered to user.",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error modifying review: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to modify review",
        )
