from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class DocumentChunk:
    chunk_id: str
    document_id: str
    text: str
    metadata: dict[str, Any]


def clean_text(text: str) -> str:
    return " ".join(text.split())


def chunk_document(
    *,
    document_id: str,
    text: str,
    metadata: dict[str, Any],
    chunk_size: int,
    chunk_overlap: int,
) -> list[DocumentChunk]:
    """Split text into overlapping chunks bounded by word boundaries.

    Attempts to end each chunk at the nearest space before `chunk_size`
    (hard_end). If no space exists in the window, the hard character boundary
    is used instead. The next chunk starts `chunk_overlap` characters before
    the previous end, advanced forward to the next word start so chunks never
    begin mid-word.
    """
    cleaned = clean_text(text)
    if not cleaned:
        raise ValueError("Document text cannot be empty")
    if chunk_size <= 0:
        raise ValueError("chunk_size must be greater than zero")
    if chunk_overlap < 0:
        raise ValueError("chunk_overlap cannot be negative")
    if chunk_overlap >= chunk_size:
        raise ValueError("chunk_overlap must be smaller than chunk_size")

    chunks: list[DocumentChunk] = []
    start = 0

    while start < len(cleaned):
        hard_end = min(start + chunk_size, len(cleaned))
        end = _nearest_word_boundary(cleaned, start, hard_end)
        chunk_text = cleaned[start:end].strip()

        if chunk_text:
            chunk_index = len(chunks) + 1
            chunks.append(
                DocumentChunk(
                    chunk_id=f"{document_id}_chunk_{chunk_index:03d}",
                    document_id=document_id,
                    text=chunk_text,
                    metadata=dict(metadata),
                )
            )

        if end >= len(cleaned):
            break

        next_start = max(end - chunk_overlap, 0)
        if next_start <= start:
            next_start = end
        start = _advance_to_word_start(cleaned, next_start)

    return chunks


def _nearest_word_boundary(text: str, start: int, hard_end: int) -> int:
    if hard_end >= len(text) or text[hard_end].isspace():
        return hard_end

    boundary = text.rfind(" ", start, hard_end)
    if boundary <= start:
        return hard_end
    return boundary


def _advance_to_word_start(text: str, index: int) -> int:
    while index < len(text) and text[index].isspace():
        index += 1
    return index
