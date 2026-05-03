import logging

from fastapi import APIRouter, HTTPException

from src.api.schemas import IngestRequest, IngestResponse
from src.rag.ingest import ingest_documents
from src.utils.config import get_settings

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/ingest", response_model=IngestResponse)
def ingest(request: IngestRequest) -> IngestResponse:
    try:
        _, summary = ingest_documents(request.documents, get_settings())
        return IngestResponse(**summary)
    except (ValueError, RuntimeError) as exc:
        logger.exception("Invalid ingestion request")
        raise HTTPException(status_code=422, detail=str(exc)) from exc
