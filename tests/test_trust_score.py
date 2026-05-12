# Tests for trust score calculation.

import pytest

from src.rag.retriever import RetrievedMatch
from src.trust.trust_score import (
    MEDIUM_CONFIDENCE_THRESHOLD,
    REVIEW_THRESHOLD,
    calculate_trust_score,
    get_review_reason,
    should_route_for_review,
)


def make_match(
    chunk_id: str,
    document_id: str,
    title: str,
    source_type: str,
    score: float,
    department: str,
    text: str = "Sample text",
) -> RetrievedMatch:
    return RetrievedMatch(
        chunk_id=chunk_id,
        document_id=document_id,
        title=title,
        score=score,
        text=text,
        metadata={"source_type": source_type, "department": department},
    )


class TestCalculateTrustScore:
    """Test trust score calculation under various conditions."""

    def test_no_retrieved_matches(self):
        """Score should be 0.0 when no documents are retrieved."""
        score = calculate_trust_score(
            retrieved_matches=[],
            answer_confidence="high",
            answer_status="answered",
        )
        assert score == 0.0

    def test_unsupported_answer(self):
        """Score should be low (0.2) when LLM cannot answer."""
        matches = [
            make_match(
                chunk_id="1",
                document_id="doc1",
                title="Policy",
                source_type="policy",
                score=0.9,
                department="HR",
            ),
        ]
        score = calculate_trust_score(
            retrieved_matches=matches,
            answer_confidence="high",
            answer_status="unsupported",
        )
        assert score == 0.2

    def test_high_confidence_high_relevance_policy(self):
        """High confidence + high relevance policy should score high."""
        matches = [
            make_match(
                chunk_id="1",
                document_id="doc1",
                title="HR Policy",
                source_type="policy",
                score=0.95,
                department="HR",
            ),
        ]
        score = calculate_trust_score(
            retrieved_matches=matches,
            answer_confidence="high",
            answer_status="answered",
        )
        assert score > 0.85  # Should be quite high

    def test_low_confidence_lowers_score(self):
        """Low confidence should reduce trust score."""
        matches = [
            make_match(
                chunk_id="1",
                document_id="doc1",
                title="Policy",
                source_type="policy",
                score=0.9,
                department="HR",
            ),
        ]

        high_conf = calculate_trust_score(
            retrieved_matches=matches,
            answer_confidence="high",
            answer_status="answered",
        )

        low_conf = calculate_trust_score(
            retrieved_matches=matches,
            answer_confidence="low",
            answer_status="answered",
        )

        assert low_conf < high_conf

    def test_source_type_weights_impact(self):
        """Policy sources should score higher than FAQ sources."""
        policy_match = make_match(
            chunk_id="1",
            document_id="doc1",
            title="Policy",
            source_type="policy",
            score=0.8,
            department="HR",
        )

        faq_match = make_match(
            chunk_id="2",
            document_id="doc2",
            title="FAQ",
            source_type="faq",
            score=0.8,
            department="HR",
        )

        policy_score = calculate_trust_score(
            retrieved_matches=[policy_match],
            answer_confidence="high",
            answer_status="answered",
        )

        faq_score = calculate_trust_score(
            retrieved_matches=[faq_match],
            answer_confidence="high",
            answer_status="answered",
        )

        assert policy_score > faq_score

    def test_multiple_sources_average(self):
        """Multiple sources should average their weights."""
        matches = [
            make_match(
                chunk_id="1",
                document_id="doc1",
                title="Policy",
                source_type="policy",
                score=0.9,
                department="HR",
            ),
            make_match(
                chunk_id="2",
                document_id="doc2",
                title="FAQ",
                source_type="faq",
                score=0.9,
                department="HR",
            ),
        ]

        score = calculate_trust_score(
            retrieved_matches=matches,
            answer_confidence="high",
            answer_status="answered",
        )

        # Score should be between policy-only and faq-only scores
        policy_only = calculate_trust_score(
            retrieved_matches=[matches[0]],
            answer_confidence="high",
            answer_status="answered",
        )
        faq_only = calculate_trust_score(
            retrieved_matches=[matches[1]],
            answer_confidence="high",
            answer_status="answered",
        )

        assert faq_only < score < policy_only

    def test_low_relevance_reduces_score(self):
        """Low similarity scores should reduce trust."""
        high_relevance = [
            make_match(
                chunk_id="1",
                document_id="doc1",
                title="Policy",
                source_type="policy",
                score=0.95,
                department="HR",
            ),
        ]

        low_relevance = [
            make_match(
                chunk_id="2",
                document_id="doc2",
                title="Policy",
                source_type="policy",
                score=0.55,
                department="HR",
            ),
        ]

        high_score = calculate_trust_score(
            retrieved_matches=high_relevance,
            answer_confidence="high",
            answer_status="answered",
        )

        low_score = calculate_trust_score(
            retrieved_matches=low_relevance,
            answer_confidence="high",
            answer_status="answered",
        )

        assert low_score < high_score

    def test_score_is_normalized(self):
        """Score should always be between 0.0 and 1.0."""
        for confidence in ["low", "medium", "high"]:
            for status in ["answered", "unsupported"]:
                score = calculate_trust_score(
                    retrieved_matches=[
                        make_match(
                            chunk_id="1",
                            document_id="doc1",
                            title="Policy",
                            source_type="policy",
                            score=0.9,
                            department="HR",
                        ),
                    ],
                    answer_confidence=confidence,
                    answer_status=status,
                )
                assert 0.0 <= score <= 1.0


class TestShouldRouteForReview:
    """Test review routing decision."""

    def test_below_threshold_routes_for_review(self):
        """Scores below threshold should be routed for review."""
        assert should_route_for_review(REVIEW_THRESHOLD - 0.1)

    def test_at_threshold_does_not_route(self):
        """Scores at threshold should not be routed."""
        assert not should_route_for_review(REVIEW_THRESHOLD)

    def test_above_threshold_does_not_route(self):
        """Scores above threshold should not be routed."""
        assert not should_route_for_review(REVIEW_THRESHOLD + 0.1)

    def test_zero_score_routes_for_review(self):
        """Zero score should be routed for review."""
        assert should_route_for_review(0.0)

    def test_perfect_score_does_not_route(self):
        """Perfect score (1.0) should not be routed."""
        assert not should_route_for_review(1.0)


class TestGetReviewReason:
    """Test review reason generation."""

    def test_high_score_no_reason(self):
        """High scores should return None."""
        reason = get_review_reason(REVIEW_THRESHOLD + 0.1)
        assert reason is None

    def test_very_low_score_insufficient_context(self):
        """Very low scores should be 'insufficient_context'."""
        reason = get_review_reason(0.1)
        assert reason == "insufficient_context"

    def test_low_score_low_source_confidence(self):
        """Low-medium scores should be 'low_source_confidence'."""
        reason = get_review_reason(0.35)
        assert reason == "low_source_confidence"

    def test_below_threshold_review_threshold(self):
        """Scores below threshold should return a reason."""
        reason = get_review_reason(REVIEW_THRESHOLD - 0.01)
        assert reason in [
            "insufficient_context",
            "low_source_confidence",
            "below_review_threshold",
        ]

    def test_exact_threshold_no_reason(self):
        """Score exactly at threshold should have no reason."""
        reason = get_review_reason(REVIEW_THRESHOLD)
        assert reason is None
