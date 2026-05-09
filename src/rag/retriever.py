# Vector retrieval layer.
#
# Two implementations:
#   - InMemoryVectorStore: local, deterministic, used in unit tests.
#   - PineconeVectorStore: production store backed by the Pinecone index.
#
# The module-level index_chunks() and retrieve() functions default to the
# in-memory store when called without settings (unit tests). When called with
# settings that include a Pinecone API key, they route to Pinecone.

from __future__ import annotations

from dataclasses import dataclass
import logging
import math
from typing import TYPE_CHECKING

from src.rag.chunking import DocumentChunk
from src.rag.embeddings import cosine_similarity, embed_text, tokenize

if TYPE_CHECKING:
    from src.utils.config import Settings

logger = logging.getLogger(__name__)

# Minimum score to include a result — keeps irrelevant chunks out of the answer
IN_MEMORY_MIN_SCORE = 0.12   # local deterministic embedder scores are low-range
PINECONE_MIN_SCORE = 0.30    # real cosine similarity with OpenAI embeddings


@dataclass(frozen=True)
class RetrievedMatch:
    chunk_id: str
    document_id: str
    title: str
    score: float
    text: str
    metadata: dict[str, object]


@dataclass(frozen=True)
class IndexedChunk:
    chunk: DocumentChunk
    embedding: list[float]


# ---------------------------------------------------------------------------
# In-memory store — used by unit tests (no API calls)
# ---------------------------------------------------------------------------

class InMemoryVectorStore:
    """Small vector store used for local development and tests."""

    def __init__(self) -> None:
        self._chunks: dict[str, IndexedChunk] = {}

    def upsert(self, chunks: list[DocumentChunk]) -> int:
        for chunk in chunks:
            self._chunks[chunk.chunk_id] = IndexedChunk(
                chunk=chunk,
                embedding=embed_text(_embedding_text(chunk)),
            )
        logger.info("Indexed %d chunks (in-memory)", len(chunks))
        return len(chunks)

    def search(self, query: str, top_k: int = 5) -> list[RetrievedMatch]:
        if top_k < 1:
            raise ValueError("top_k must be at least 1")
        if not query.strip():
            raise ValueError("query cannot be blank")

        query_embedding = embed_text(query)
        query_terms = set(tokenize(query))
        term_weights = self._term_weights(query_terms)
        matches: list[RetrievedMatch] = []

        for indexed in self._chunks.values():
            lexical_score = _lexical_overlap(query_terms, term_weights, indexed.chunk)
            vector_score = cosine_similarity(query_embedding, indexed.embedding)
            # Equal weighting: lexical catches exact keyword matches,
            # vector catches semantic matches (synonyms, paraphrasing)
            score = (lexical_score * 0.5) + (vector_score * 0.5)
            if score < IN_MEMORY_MIN_SCORE:
                continue

            chunk = indexed.chunk
            matches.append(
                RetrievedMatch(
                    chunk_id=chunk.chunk_id,
                    document_id=chunk.document_id,
                    title=str(chunk.metadata.get("title", "")),
                    score=round(score, 4),
                    text=chunk.text,
                    metadata=dict(chunk.metadata),
                )
            )

        matches.sort(key=lambda m: m.score, reverse=True)
        return matches[:top_k]

    def clear(self) -> None:
        self._chunks.clear()

    def count(self) -> int:
        return len(self._chunks)

    def _term_weights(self, query_terms: set[str]) -> dict[str, float]:
        if not query_terms:
            return {}
        total_chunks = max(len(self._chunks), 1)
        weights: dict[str, float] = {}
        for term in query_terms:
            document_frequency = sum(
                1
                for indexed in self._chunks.values()
                if term in set(tokenize(_embedding_text(indexed.chunk)))
            )
            weights[term] = 1.0 + math.log(
                (1 + total_chunks) / (1 + document_frequency)
            )
        return weights


# ---------------------------------------------------------------------------
# Pinecone store — used in production when API key is configured
# ---------------------------------------------------------------------------

class PineconeVectorStore:
    """Production vector store backed by Pinecone.

    Embeds chunks with OpenAI before upserting, and embeds the query before
    searching. Pinecone handles ANN (approximate nearest neighbour) search
    at scale — no need for hybrid lexical scoring here.
    """

    def __init__(self, settings: Settings) -> None:
        from pinecone import Pinecone
        pc = Pinecone(api_key=settings.pinecone_api_key)
        self._index = pc.Index(settings.pinecone_index_name)
        self._settings = settings

    def upsert(self, chunks: list[DocumentChunk]) -> int:
        from src.rag.embeddings import embed_many_openai

        texts = [_embedding_text(chunk) for chunk in chunks]
        embeddings = embed_many_openai(texts, self._settings)

        vectors = [
            {
                "id": chunk.chunk_id,
                "values": embedding,
                # Store metadata in Pinecone so it comes back with query results
                "metadata": {
                    "document_id": chunk.document_id,
                    "title": str(chunk.metadata.get("title", "")),
                    "source_type": str(chunk.metadata.get("source_type", "")),
                    "department": str(chunk.metadata.get("department", "")),
                    "text": chunk.text,
                },
            }
            for chunk, embedding in zip(chunks, embeddings)
        ]

        # Upsert in batches of 100 — Pinecone's recommended batch size
        batch_size = 100
        for i in range(0, len(vectors), batch_size):
            self._index.upsert(vectors=vectors[i : i + batch_size])

        logger.info("Indexed %d chunks to Pinecone index '%s'",
                    len(chunks), self._settings.pinecone_index_name)
        return len(chunks)

    def search(self, query: str, top_k: int = 5) -> list[RetrievedMatch]:
        if top_k < 1:
            raise ValueError("top_k must be at least 1")
        if not query.strip():
            raise ValueError("query cannot be blank")

        from src.rag.embeddings import embed_text_openai
        query_embedding = embed_text_openai(query, self._settings)

        results = self._index.query(
            vector=query_embedding,
            top_k=top_k,
            include_metadata=True,
        )

        matches = []
        for match in results.matches:
            if match.score < PINECONE_MIN_SCORE:
                continue
            meta = match.metadata or {}
            matches.append(
                RetrievedMatch(
                    chunk_id=match.id,
                    document_id=meta.get("document_id", ""),
                    title=meta.get("title", ""),
                    score=round(match.score, 4),
                    text=meta.get("text", ""),
                    metadata=dict(meta),
                )
            )
        return matches


# ---------------------------------------------------------------------------
# Module-level singleton and public API
# ---------------------------------------------------------------------------

# In-memory store for unit tests — routes pass settings to get Pinecone instead
vector_store = InMemoryVectorStore()


def index_chunks(chunks: list[DocumentChunk], settings: Settings | None = None) -> int:
    """Index chunks into the appropriate store.

    If settings are provided and include a Pinecone key, uses Pinecone.
    Otherwise falls back to the in-memory store (used by unit tests).
    """
    if settings and settings.pinecone_api_key:
        return PineconeVectorStore(settings).upsert(chunks)
    return vector_store.upsert(chunks)


def retrieve(
    query: str,
    top_k: int = 5,
    settings: Settings | None = None,
) -> list[RetrievedMatch]:
    """Retrieve the top-k most relevant chunks for a query.

    If settings are provided and include a Pinecone key, queries Pinecone.
    Otherwise queries the in-memory store (used by unit tests).
    """
    if settings and settings.pinecone_api_key:
        return PineconeVectorStore(settings).search(query, top_k)
    return vector_store.search(query=query, top_k=top_k)


def reset_retriever() -> None:
    """Clear the in-memory store — used between unit tests."""
    vector_store.clear()


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def _embedding_text(chunk: DocumentChunk) -> str:
    # Prepend metadata values so the embedding captures document context,
    # not just the raw text — improves retrieval accuracy.
    metadata_values = " ".join(str(v) for v in chunk.metadata.values())
    return f"{metadata_values} {chunk.text}"


def _lexical_overlap(
    query_terms: set[str],
    term_weights: dict[str, float],
    chunk: DocumentChunk,
) -> float:
    if not query_terms:
        return 0.0
    chunk_terms = set(tokenize(_embedding_text(chunk)))
    total_weight = sum(term_weights.values())
    if total_weight == 0:
        return 0.0
    matched_weight = sum(
        weight for term, weight in term_weights.items() if term in chunk_terms
    )
    return matched_weight / total_weight
