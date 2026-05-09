# Embedding utilities.
#
# Two modes:
#   - Local (deterministic): used by unit tests and when no API key is configured.
#     Fast, dependency-free, but low quality — only for development.
#   - OpenAI: used in production. Calls text-embedding-3-small and returns
#     real semantic vectors. Requires OPENAI_API_KEY to be set.

from __future__ import annotations

import hashlib
import math
import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.utils.config import Settings

VECTOR_DIMENSIONS = 256
TOKEN_PATTERN = re.compile(r"[a-z0-9]+")
STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "can", "do",
    "for", "from", "how", "in", "is", "it", "must", "of", "on", "or",
    "should", "the", "to", "what", "when", "where", "who", "why", "with",
}


# --- OpenAI embeddings ---

def embed_text_openai(text: str, settings: Settings) -> list[float]:
    """Embed a single text string using the OpenAI API.

    Uses the dimensions param to reduce output size to match the Pinecone index.
    text-embedding-3-small natively supports Matryoshka dimension reduction.
    """
    from openai import OpenAI
    client = OpenAI(api_key=settings.openai_api_key)
    response = client.embeddings.create(
        model=settings.openai_embedding_model,
        input=text,
        dimensions=settings.pinecone_dimensions,
    )
    return response.data[0].embedding


def embed_many_openai(texts: list[str], settings: Settings) -> list[list[float]]:
    """Embed a batch of texts in a single OpenAI API call.

    Batching is more efficient than calling embed_text_openai in a loop
    because OpenAI processes the batch server-side in parallel.
    """
    from openai import OpenAI
    client = OpenAI(api_key=settings.openai_api_key)
    response = client.embeddings.create(
        model=settings.openai_embedding_model,
        input=texts,
        dimensions=settings.pinecone_dimensions,
    )
    # Sort by index to guarantee order matches the input list
    return [item.embedding for item in sorted(response.data, key=lambda x: x.index)]


# --- Local deterministic embedder (used in tests) ---

def embed_text(text: str) -> list[float]:
    """Return a normalized deterministic vector for a text string.

    Not semantically meaningful — used only in unit tests and local dev
    where API calls are not available.
    """
    tokens = tokenize(text)
    if not tokens:
        return [0.0] * VECTOR_DIMENSIONS

    vector = [0.0] * VECTOR_DIMENSIONS
    for token in tokens:
        digest = hashlib.sha256(token.encode("utf-8")).digest()
        index = int.from_bytes(digest[:4], "big") % VECTOR_DIMENSIONS
        sign = 1.0 if digest[4] % 2 == 0 else -1.0
        vector[index] += sign

    return normalize(vector)


def embed_many(texts: list[str]) -> list[list[float]]:
    """Embed a batch of texts using the local deterministic embedder."""
    return [embed_text(text) for text in texts]


def cosine_similarity(left: list[float], right: list[float]) -> float:
    """Return cosine similarity for pre-normalized vectors (dot product)."""
    if len(left) != len(right):
        raise ValueError("Embedding vectors must have the same length")
    return sum(a * b for a, b in zip(left, right))


def tokenize(text: str) -> list[str]:
    """Tokenize text for the local embedding model."""
    return [
        normalize_token(token)
        for token in TOKEN_PATTERN.findall(text.lower())
        if token not in STOPWORDS and len(token) > 1
    ]


def normalize_token(token: str) -> str:
    """Apply lightweight suffix normalization for local lexical matching."""
    for suffix in ("ing", "ed", "es", "s"):
        if len(token) > len(suffix) + 3 and token.endswith(suffix):
            stem = token[: -len(suffix)]
            if len(stem) > 3 and stem[-1] == stem[-2]:
                stem = stem[:-1]
            return stem
    return token


def normalize(vector: list[float]) -> list[float]:
    norm = math.sqrt(sum(value * value for value in vector))
    if norm == 0:
        return vector
    return [value / norm for value in vector]
