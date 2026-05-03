from fastapi import FastAPI

from src.api.routes_ingest import router as ingest_router
from src.utils.config import get_settings
from src.utils.logging import configure_logging

settings = get_settings()
configure_logging(settings.log_level)

app = FastAPI(title=settings.app_name)
app.include_router(ingest_router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": settings.app_name}
