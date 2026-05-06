# Splits document text into smaller overlapping chunks for vector search.
#
# Why chunk? LLMs and embedding models have token limits, so long documents
# must be split into smaller pieces. Overlap between chunks ensures that
# sentences near a boundary are not lost from context.

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class DocumentChunk:
    """A single piece of a document after chunking.

    Frozen (immutable) so chunks cannot be accidentally modified after creation.
    """

    chunk_id: str            # Unique ID, e.g. "policy_001_chunk_003"
    document_id: str         # ID of the parent document
    text: str                # The actual text content of this chunk
    metadata: dict[str, Any] # Carries title, source_type, department from the parent


def clean_text(text: str) -> str:
    # Collapse all whitespace (tabs, newlines, multiple spaces) into single spaces.
    # This prevents chunk boundaries from landing in the middle of whitespace noise.
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
        # Calculate where this chunk ends — try word boundary first, fall back to hard cut
        hard_end = min(start + chunk_size, len(cleaned))
        end = _nearest_word_boundary(cleaned, start, hard_end)
        chunk_text = cleaned[start:end].strip()

        if chunk_text:
            chunk_index = len(chunks) + 1
            # Zero-pad index to 3 digits so IDs sort correctly (001, 002, ... 010)
            chunks.append(
                DocumentChunk(
                    chunk_id=f"{document_id}_chunk_{chunk_index:03d}",
                    document_id=document_id,
                    text=chunk_text,
                    metadata=dict(metadata),  # copy so mutations don't affect other chunks
                )
            )

        if end >= len(cleaned):
            break

        # Step back by overlap to give the next chunk shared context with this one.
        # Guard against infinite loop: if next_start hasn't advanced, skip ahead.
        next_start = max(end - chunk_overlap, 0)
        if next_start <= start:
            next_start = end
        start = _advance_to_word_start(cleaned, next_start)

    return chunks


def _nearest_word_boundary(text: str, start: int, hard_end: int) -> int:
    # If we're already at the end of the text or at a space, no adjustment needed
    if hard_end >= len(text) or text[hard_end].isspace():
        return hard_end

    # Walk backwards from hard_end to find the last space in this window
    boundary = text.rfind(" ", start, hard_end)

    # If no space found in the window, use the hard cut to avoid an infinite loop
    if boundary <= start:
        return hard_end
    return boundary


def _advance_to_word_start(text: str, index: int) -> int:
    # Skip over any spaces so the next chunk starts at the first character of a word
    while index < len(text) and text[index].isspace():
        index += 1
    return index
