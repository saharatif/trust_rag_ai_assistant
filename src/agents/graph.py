# LangGraph workflow for TrustRAG agent orchestration.
# Assembles nodes into a directed graph for execution.

import logging

from langgraph.graph import StateGraph, END

from src.agents.nodes import (
    node_generate_answer,
    node_retrieve,
    node_route_review,
    node_score_trust,
    should_review,
)
from src.agents.state import AgentState

logger = logging.getLogger(__name__)


def build_graph() -> StateGraph:
    """Build and return the LangGraph workflow.

    Graph structure:
        retrieve → generate_answer → score_trust → route_review →┐
                                                                   ├→ [review or ready]
    """
    graph = StateGraph(AgentState)

    # Add nodes
    graph.add_node("retrieve", node_retrieve)
    graph.add_node("generate_answer", node_generate_answer)
    graph.add_node("score_trust", node_score_trust)
    graph.add_node("route_review", node_route_review)

    # Add edges (connections between nodes)
    graph.add_edge("retrieve", "generate_answer")
    graph.add_edge("generate_answer", "score_trust")
    graph.add_edge("score_trust", "route_review")

    # Conditional edge: route_review branches to END
    graph.add_conditional_edges(
        "route_review",
        should_review,
        {
            "review": END,  # Response needs human review (handled by API)
            "ready": END,   # Response is approved for delivery
        },
    )

    # Set entry point
    graph.set_entry_point("retrieve")

    logger.info("LangGraph workflow built successfully")

    return graph


# Create the compiled workflow
_workflow = None


def get_workflow():
    """Get or create the compiled workflow."""
    global _workflow
    if _workflow is None:
        graph = build_graph()
        _workflow = graph.compile()
    return _workflow
