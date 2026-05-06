# Pydantic models that define the shape and validation rules for API requests and responses.
# FastAPI uses these models to automatically validate incoming JSON and return clean errors.

from typing import Literal

from pydantic import BaseModel, Field, field_validator

# Only these document types are accepted — keeps source classification consistent
SOURCE_TYPES = Literal["policy", "faq", "manual", "contract", "report"]


class DocumentIngestItem(BaseModel):
    """Represents a single document submitted for ingestion."""

    id: str = Field(min_length=1)           # Unique identifier for the document
    title: str = Field(min_length=1)        # Human-readable document title
    source_type: SOURCE_TYPES               # Category of the document
    department: str = Field(min_length=1)   # Owning department (e.g. HR, Legal)
    text: str = Field(min_length=1)         # Full document text to be chunked

    @field_validator("id", "title", "source_type", "department", "text")
    @classmethod
    def reject_blank_strings(cls, value: str) -> str:
        # min_length=1 catches empty strings but not whitespace-only strings like "   "
        # This validator catches that gap and also strips leading/trailing whitespace
        stripped = value.strip()
        if not stripped:
            raise ValueError("Field cannot be blank")
        return stripped


class IngestRequest(BaseModel):
    """Request body for POST /ingest — must contain at least one document."""

    documents: list[DocumentIngestItem] = Field(min_length=1)


class IngestResponse(BaseModel):
    """Response returned after a successful ingestion."""

    documents_received: int   # Number of documents in the request
    chunks_created: int       # Total chunks produced across all documents
    status: str               # Always "success" when no error is raised
