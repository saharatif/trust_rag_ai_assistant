# Grounded answer generation.
#
# Two modes:
#   - OpenAI (production): sends the RAG prompt to GPT and returns a grounded answer.
#   - Local fallback (tests/no key): extracts the best-matching sentences from
#     retrieved chunks without an LLM call.

from __future__ import annotations

import logging
import re
from typing import TYPE_CHECKING

from src.rag.embeddings import tokenize
from src.rag.prompt_builder import build_rag_prompt
from src.rag.retriever import RetrievedMatch

if TYPE_CHECKING:
    from src.utils.config import Settings

logger = logging.getLogger(__name__)

UNSUPPORTED_ANSWER = (
    "I don't have enough information in the approved documents to answer that."
)

# Phrases the LLM uses to signal it cannot answer from the provided context
_UNSUPPORTED_PHRASES = (
    "don't have enough information",
    "do not have enough information",
    "cannot find",
    "not found in",
    "documents do not contain",
    "no information",
    "not enough information",
)


def generate_answer(
    *,
    question: str,
    matches: list[RetrievedMatch],
    settings: Settings | None = None,
) -> tuple[str, str, str]:
    """Generate a grounded answer, confidence level, and status.

    Returns a tuple of (answer, confidence, status) where:
      confidence: "low" | "medium" | "high"
      status:     "answered" | "unsupported"

    Uses OpenAI when settings with a valid API key are provided.
    Falls back to local sentence extraction otherwise (used in unit tests).
    """
    if settings and settings.openai_api_key:
        return _generate_with_openai(question, matches, settings)
    return _generate_local(question, matches)


# ---------------------------------------------------------------------------
# OpenAI path
# ---------------------------------------------------------------------------

def _generate_with_openai(
    question: str,
    matches: list[RetrievedMatch],
    settings: Settings,
) -> tuple[str, str, str]:
    if not matches:
        logger.info("No matches found for question: %s", question)
        return UNSUPPORTED_ANSWER, "low", "unsupported"

    prompt = build_rag_prompt(question, matches)

    from openai import OpenAI
    client = OpenAI(api_key=settings.openai_api_key)
    response = client.chat.completions.create(
        model=settings.openai_chat_model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0,      # deterministic — we want grounded answers, not creative ones
        max_tokens=500,
    )

    answer = response.choices[0].message.content.strip()

    # If the LLM signals it cannot answer from the context, return the safe fallback
    if _is_unsupported_response(answer):
        logger.info("LLM reported unsupported question: %s", question)
        return UNSUPPORTED_ANSWER, "low", "unsupported"

    confidence = _confidence_from_score(matches[0].score)
    logger.info("Generated answer with confidence=%s for question: %s", confidence, question)
    return answer, confidence, "answered"


def _is_unsupported_response(answer: str) -> bool:
    lower = answer.lower()
    return any(phrase in lower for phrase in _UNSUPPORTED_PHRASES)


# ---------------------------------------------------------------------------
# Local fallback path (used in unit tests — no API call)
# ---------------------------------------------------------------------------

def _generate_local(
    question: str,
    matches: list[RetrievedMatch],
) -> tuple[str, str, str]:
    if not matches or matches[0].score < 0.18:
        logger.info("Unsupported chat question (local): %s", question)
        return UNSUPPORTED_ANSWER, "low", "unsupported"

    sentences = _rank_sentences(question, matches)
    if not sentences:
        return UNSUPPORTED_ANSWER, "low", "unsupported"

    confidence = _confidence_from_score(matches[0].score)
    answer = " ".join(sentences[:2])
    return answer, confidence, "answered"


def _rank_sentences(
    question: str,
    matches: list[RetrievedMatch],
) -> list[str]:
    question_terms = set(tokenize(question))
    ranked: list[tuple[int, float, str]] = []

    for match in matches:
        for sentence in _split_sentences(match.text):
            sentence_terms = set(tokenize(sentence))
            overlap = len(question_terms & sentence_terms)
            if overlap == 0:
                continue
            ranked.append((overlap, match.score, sentence))

    ranked.sort(key=lambda item: (item[0], item[1]), reverse=True)
    return [sentence for _, _, sentence in ranked]


def _split_sentences(text: str) -> list[str]:
    return [
        s.strip()
        for s in re.split(r"(?<=[.!?])\s+", text)
        if s.strip()
    ]


def _confidence_from_score(score: float) -> str:
    if score >= 0.5:
        return "high"
    if score >= 0.25:
        return "medium"
    return "low"
