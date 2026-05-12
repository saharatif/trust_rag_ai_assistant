# Agent state schema for LangGraph workflow.
# Defines the shape of data flowing through the agentic orchestration.

from dataclasses import dataclass, field
from typing import Literal

from src.rag.retriever import RetrievedMatch


@dataclass
class AgentState:
    """Represents the complete state of an agent workflow execution.

    This state flows through LangGraph nodes, accumulating results as it moves
    from retrieval → trust scoring → answer generation → review routing.
    """

    # === Input ===
    question: str
    """The user's question to answer."""

    top_k: int = 5
    """Number of top documents to retrieve."""

    # === Retrieval Results ===
    retrieved_matches: list[RetrievedMatch] = field(default_factory=list)
    """List of documents retrieved from vector store, sorted by relevance."""

    # === Trust & Risk Assessment ===
    trust_score: float | None = None
    """Trust score (0.0-1.0) indicating confidence in retrieved context.
    Calculated based on relevance, source type, and answer grounding."""

    needs_review: bool = False
    """Whether the response should be routed to a human for approval."""

    review_reason: str | None = None
    """If needs_review is True, explains why (e.g., 'low_trust', 'sensitive_topic')."""

    # === Generated Answer ===
    answer: str | None = None
    """The LLM-generated answer grounded in retrieved documents."""

    confidence: Literal["low", "medium", "high"] | None = None
    """Confidence level of the answer: 'low', 'medium', or 'high'."""

    answer_status: Literal["answered", "unsupported"] | None = None
    """Whether the LLM could answer ('answered') or had to refuse ('unsupported')."""

    # === Sources ===
    cited_chunks: list[str] = field(default_factory=list)
    """Chunks from retrieved documents that were used in the answer."""

    # === Workflow Tracking ===
    workflow_status: Literal[
        "init", "retrieved", "scored", "generated", "ready", "approved", "rejected"
    ] = "init"
    """Current stage in the workflow."""

    error: str | None = None
    """If any step fails, the error message is stored here."""
