import pytest

from src.rag.chunking import chunk_document, clean_text


def test_clean_text_normalizes_whitespace():
    assert clean_text("  alpha\n\n beta\tgamma  ") == "alpha beta gamma"


def test_chunk_document_preserves_metadata_and_ids():
    chunks = chunk_document(
        document_id="policy_001",
        text="Alpha beta gamma delta epsilon zeta eta theta iota kappa lambda mu.",
        metadata={"title": "Policy", "department": "HR"},
        chunk_size=25,
        chunk_overlap=5,
    )

    assert len(chunks) > 1
    assert chunks[0].chunk_id == "policy_001_chunk_001"
    assert chunks[0].document_id == "policy_001"
    assert chunks[0].metadata == {"title": "Policy", "department": "HR"}
    assert all(chunk.text for chunk in chunks)


def test_chunk_document_rejects_empty_text():
    with pytest.raises(ValueError, match="Document text cannot be empty"):
        chunk_document(
            document_id="empty",
            text="   ",
            metadata={},
            chunk_size=100,
            chunk_overlap=10,
        )


def test_chunk_document_rejects_invalid_overlap():
    with pytest.raises(ValueError, match="chunk_overlap must be smaller"):
        chunk_document(
            document_id="bad",
            text="Valid text",
            metadata={},
            chunk_size=10,
            chunk_overlap=10,
        )
