# Entry point for the TrustRAG FastAPI application.
# This file creates the app instance, registers routes, and sets up logging.
# It is the file uvicorn points to when starting the server:
#   uvicorn src.api.main:app --reload

from fastapi import FastAPI

from src.api.routes_ingest import router as ingest_router
from src.utils.config import get_settings
from src.utils.logging import configure_logging

# Load all settings from environment variables once at startup
settings = get_settings()

# Set up structured JSON logging before any request is handled
configure_logging(settings.log_level)

# Create the FastAPI app — title appears in the auto-generated /docs UI
app = FastAPI(title=settings.app_name)

# Register the ingest router so POST /ingest is available
app.include_router(ingest_router)


@app.get("/health")
def health() -> dict[str, str]:
    # No rate limit here — load balancers and Docker health checks call this
    # endpoint continuously from internal IPs. Rate limiting it would cause
    # the service to be marked unhealthy and trigger unwanted restarts.
    return {"status": "ok", "service": settings.app_name}
