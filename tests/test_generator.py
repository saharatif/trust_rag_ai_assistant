import pytest

from src.rag.generator import generate_answer, _confidence_from_score, _is_unsupported_response
from src.rag.prompt_builder import build_rag_prompt
from src.rag.retriever import RetrievedMatch


# --- Helpers ---

def make_match(chunk_id="doc_001_chunk_001", score=0.6, text="Receipts must be submitted within 30 days."):
    return RetrievedMatch(
        chunk_id=chunk_id,
        document_id="doc_001",
        title="Travel Policy",
        score=score,
        text=text,
        metadata={"title": "Travel Policy"},
    )


# --- generate_answer (local fallback, no settings) ---

def test_generate_answer_returns_unsupported_when_no_matches():
    answer, confidence, status = generate_answer(question="What is X?", matches=[])
    assert status == "unsupported"
    assert confidence == "low"
    assert "don't have enough information" in answer.lower()


def test_generate_answer_returns_unsupported_when_score_too_low():
    low_match = make_match(score=0.05)
    answer, confidence, status = generate_answer(question="What is X?", matches=[low_match])
    assert status == "unsupported"
    assert confidence == "low"


def test_generate_answer_returns_answered_with_relevant_match():
    match = make_match(
        score=0.7,
        text="Receipts must be submitted within 30 days of travel.",
    )
    answer, confidence, status = generate_answer(
        question="When must receipts be submitted?",
        matches=[match],
    )
    assert status == "answered"
    assert confidence in ("low", "medium", "high")
    assert len(answer) > 0


def test_generate_answer_confidence_reflects_score():
    high = make_match(score=0.9)
    medium = make_match(score=0.35)
    low = make_match(score=0.22)

    _, c_high, _ = generate_answer(question="When must receipts be submitted?", matches=[high])
    _, c_medium, _ = generate_answer(question="When must receipts be submitted?", matches=[medium])
    _, c_low, _ = generate_answer(question="When must receipts be submitted?", matches=[low])

    assert c_high == "high"
    assert c_medium == "medium"
    assert c_low == "low"


# --- _confidence_from_score ---

def test_confidence_from_score_high():
    assert _confidence_from_score(0.5) == "high"
    assert _confidence_from_score(0.99) == "high"


def test_confidence_from_score_medium():
    assert _confidence_from_score(0.25) == "medium"
    assert _confidence_from_score(0.49) == "medium"


def test_confidence_from_score_low():
    assert _confidence_from_score(0.0) == "low"
    assert _confidence_from_score(0.24) == "low"


# --- _is_unsupported_response ---

def test_is_unsupported_response_detects_phrases():
    assert _is_unsupported_response("I don't have enough information to answer.")
    assert _is_unsupported_response("The documents do not contain this information.")
    assert _is_unsupported_response("I cannot find any relevant information.")


def test_is_unsupported_response_passes_valid_answer():
    assert not _is_unsupported_response("Receipts must be submitted within 30 days.")
    assert not _is_unsupported_response("Director approval is required for business class.")


# --- build_rag_prompt ---

def test_build_rag_prompt_contains_question_and_context():
    match = make_match(text="Receipts must be submitted within 30 days.")
    prompt = build_rag_prompt("When are receipts due?", [match])

    assert "When are receipts due?" in prompt
    assert "Receipts must be submitted within 30 days." in prompt
    assert "Travel Policy" in prompt


def test_build_rag_prompt_handles_empty_matches():
    prompt = build_rag_prompt("What is X?", [])
    assert "No relevant document context found." in prompt
    assert "What is X?" in prompt


def test_build_rag_prompt_numbers_sources():
    matches = [make_match(chunk_id=f"doc_chunk_00{i}") for i in range(1, 4)]
    prompt = build_rag_prompt("question", matches)
    assert "Source 1:" in prompt
    assert "Source 2:" in prompt
    assert "Source 3:" in prompt
