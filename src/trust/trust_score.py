# Trust score calculation for RAG responses.
# Combines retrieval relevance, source credibility, and answer grounding to produce
# a normalized trust score that determines if a response should be routed to human review.

import logging
from typing import Literal

from src.rag.retriever import RetrievedMatch

logger = logging.getLogger(__name__)

# Trust score thresholds — customize based on business risk tolerance
REVIEW_THRESHOLD = 0.5  # Scores below this are routed for human review
HIGH_CONFIDENCE_THRESHOLD = 0.75  # Scores at/above this are "high confidence"
MEDIUM_CONFIDENCE_THRESHOLD = 0.5  # Scores at/above this are "medium confidence"

# Source credibility weights — policy sources carry more weight than FAQs
SOURCE_WEIGHTS = {
    "policy": 1.0,      # Authoritative, reviewed
    "contract": 1.0,    # Legally binding
    "manual": 0.9,      # Well-documented
    "report": 0.8,      # Factual but less formal
    "faq": 0.6,         # Helpful but less authoritative
}


def calculate_trust_score(
    *,
    retrieved_matches: list[RetrievedMatch],
    answer_confidence: Literal["low", "medium", "high"],
    answer_status: Literal["answered", "unsupported"],
) -> float:
    """Calculate a trust score for a RAG response (0.0-1.0).

    Factors considered:
      1. Relevance of retrieved documents (from embedding similarity)
      2. Credibility of sources (policy > contract > manual > report > faq)
      3. LLM confidence in the answer
      4. Whether the LLM marked the answer as "unsupported"

    Args:
        retrieved_matches: List of retrieved documents with similarity scores.
        answer_confidence: The LLM's confidence level in its answer.
        answer_status: Whether the LLM answered or refused.

    Returns:
        A normalized score from 0.0 (least trustworthy) to 1.0 (most trustworthy).
    """

    if not retrieved_matches:
        # No context → cannot trust the answer
        return 0.0

    if answer_status == "unsupported":
        # LLM explicitly said it cannot answer from context → low trust
        return 0.2

    # Each match contributes (credibility * relevance). Dividing by the count
    # (not the sum of weights) ensures higher-credibility sources produce a
    # higher average rather than normalizing back to plain relevance.
    total_weighted_score = 0.0

    for match in retrieved_matches:
        source_type = str(match.metadata.get("source_type", "")).lower()
        credibility_weight = SOURCE_WEIGHTS.get(source_type, 0.5)
        total_weighted_score += credibility_weight * match.score

    average_weighted_score = total_weighted_score / len(retrieved_matches)

    # Apply confidence boost
    confidence_multiplier = {
        "high": 1.0,      # Confidence 95%+
        "medium": 0.85,   # Confidence 60-94%
        "low": 0.5,       # Confidence <60%
    }.get(answer_confidence, 0.5)

    trust_score = average_weighted_score * confidence_multiplier

    # Clamp to [0, 1]
    trust_score = max(0.0, min(1.0, trust_score))

    logger.debug(
        f"Trust score calculated: {trust_score:.2f} "
        f"(confidence={answer_confidence}, status={answer_status}, "
        f"sources={len(retrieved_matches)})"
    )

    return trust_score


def should_route_for_review(trust_score: float) -> bool:
    """Determine if a response should be routed to a human for approval.

    Args:
        trust_score: The calculated trust score (0.0-1.0).

    Returns:
        True if the score is below the review threshold.
    """
    return trust_score < REVIEW_THRESHOLD


def get_review_reason(trust_score: float) -> str | None:
    """Generate a human-readable reason why a response needs review.

    Args:
        trust_score: The calculated trust score.

    Returns:
        A brief reason string, or None if review is not needed.
    """
    if trust_score >= REVIEW_THRESHOLD:
        return None

    if trust_score < 0.2:
        return "insufficient_context"
    elif trust_score < 0.4:
        return "low_source_confidence"
    else:
        return "below_review_threshold"
