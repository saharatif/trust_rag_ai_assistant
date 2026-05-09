import pytest

from src.rag.chunking import DocumentChunk
from src.rag.retriever import index_chunks, reset_retriever, retrieve


def setup_function():
    reset_retriever()


def test_retriever_returns_relevant_chunks():
    index_chunks(
        [
            DocumentChunk(
                chunk_id="policy_001_chunk_001",
                document_id="policy_001",
                text=(
                    "Business class flights require director approval for "
                    "international trips longer than eight hours."
                ),
                metadata={"title": "Employee Travel Policy"},
            ),
            DocumentChunk(
                chunk_id="faq_001_chunk_001",
                document_id="faq_001",
                text="Password resets must use identity verification.",
                metadata={"title": "IT Support FAQ"},
            ),
        ]
    )

    matches = retrieve("Can employees book business class flights?", top_k=1)

    assert len(matches) == 1
    assert matches[0].chunk_id == "policy_001_chunk_001"
    assert matches[0].document_id == "policy_001"
    assert matches[0].title == "Employee Travel Policy"
    assert matches[0].score > 0


def test_retriever_handles_no_match():
    index_chunks(
        [
            DocumentChunk(
                chunk_id="faq_001_chunk_001",
                document_id="faq_001",
                text="Password resets must use identity verification.",
                metadata={"title": "IT Support FAQ"},
            )
        ]
    )

    matches = retrieve("What is the cafeteria lunch menu?", top_k=3)

    assert matches == []


def test_retriever_rejects_blank_query():
    with pytest.raises(ValueError, match="query cannot be blank"):
        retrieve("   ", top_k=3)
