from typing import Literal

from pydantic import BaseModel, Field, field_validator

SOURCE_TYPES = Literal["policy", "faq", "manual", "contract", "report"]


class DocumentIngestItem(BaseModel):
    id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    source_type: SOURCE_TYPES
    department: str = Field(min_length=1)
    text: str = Field(min_length=1)

    @field_validator("id", "title", "source_type", "department", "text")
    @classmethod
    def reject_blank_strings(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("Field cannot be blank")
        return stripped


class IngestRequest(BaseModel):
    documents: list[DocumentIngestItem] = Field(min_length=1)


class IngestResponse(BaseModel):
    documents_received: int
    chunks_created: int
    status: str
