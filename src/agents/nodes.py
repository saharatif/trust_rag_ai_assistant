# Agent node functions for LangGraph workflow.
# Each node handles one step of the RAG + review pipeline.

import logging
from typing import Literal

from src.agents.state import AgentState
from src.rag.generator import generate_answer
from src.rag.retriever import retrieve
from src.trust.trust_score import calculate_trust_score, get_review_reason, should_route_for_review
from src.utils.config import get_settings

logger = logging.getLogger(__name__)


def node_retrieve(state: AgentState) -> AgentState:
    """Retrieve relevant documents from the vector store.

    This is the first node in the workflow. It takes the user's question
    and retrieves the top_k most similar documents.
    """
    logger.info(f"Retrieving documents for: {state.question[:50]}...")

    try:
        matches = retrieve(query=state.question, top_k=state.top_k)
        state.retrieved_matches = matches
        state.workflow_status = "retrieved"

        logger.info(f"Retrieved {len(matches)} documents")

    except Exception as e:
        logger.error(f"Retrieval failed: {e}")
        state.error = str(e)
        state.workflow_status = "init"

    return state


def node_generate_answer(state: AgentState) -> AgentState:
    """Generate an answer using the LLM, grounded in retrieved documents."""
    if not state.retrieved_matches:
        state.answer = "No relevant documents found."
        state.confidence = "low"
        state.answer_status = "unsupported"
        state.workflow_status = "generated"
        return state

    logger.info("Generating answer...")

    try:
        settings = get_settings()
        answer, confidence, answer_status = generate_answer(
            question=state.question,
            matches=state.retrieved_matches,
            settings=settings,
        )

        state.answer = answer
        state.confidence = confidence
        state.answer_status = answer_status
        state.workflow_status = "generated"

        logger.info(f"Answer generated (confidence={confidence}, status={answer_status})")

    except Exception as e:
        logger.error(f"Answer generation failed: {e}")
        state.error = str(e)
        state.answer = "Error generating answer."
        state.confidence = "low"
        state.answer_status = "unsupported"

    return state


def node_score_trust(state: AgentState) -> AgentState:
    """Calculate trust score for the generated answer."""
    if state.error or not state.retrieved_matches:
        state.trust_score = 0.0
        state.workflow_status = "scored"
        return state

    logger.info("Calculating trust score...")

    try:
        trust_score = calculate_trust_score(
            retrieved_matches=state.retrieved_matches,
            answer_confidence=state.confidence or "low",
            answer_status=state.answer_status or "unsupported",
        )

        state.trust_score = trust_score
        state.workflow_status = "scored"

        logger.info(f"Trust score: {trust_score:.2f}")

    except Exception as e:
        logger.error(f"Trust scoring failed: {e}")
        state.error = str(e)
        state.trust_score = 0.0

    return state


def node_route_review(state: AgentState) -> AgentState:
    """Determine if the response needs human review based on trust score."""
    if state.trust_score is None:
        state.needs_review = False
        state.workflow_status = "ready"
        return state

    logger.info(f"Checking if review is needed (trust_score={state.trust_score:.2f})...")

    state.needs_review = should_route_for_review(state.trust_score)
    state.review_reason = get_review_reason(state.trust_score)

    if state.needs_review:
        logger.info(f"Response marked for review: {state.review_reason}")
    else:
        logger.info("Response approved for direct delivery")

    state.workflow_status = "ready"
    return state


def should_review(state: AgentState) -> Literal["review", "ready"]:
    """Router function: decide whether to go to review or mark as ready."""
    if state.needs_review:
        return "review"
    return "ready"
