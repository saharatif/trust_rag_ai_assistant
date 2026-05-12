# Entry point for the TrustRAG FastAPI application.
# This file creates the app instance, registers routes, and sets up logging.
# It is the file uvicorn points to when starting the server:
#   uvicorn src.api.main:app --reload

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.routes_chat import router as chat_router
from src.api.routes_ingest import router as ingest_router
from src.api.routes_retrieve import router as retrieve_router
from src.utils.config import get_settings
from src.utils.logging import configure_logging

# Load all settings from environment variables once at startup
settings = get_settings()

# Set up structured JSON logging before any request is handled
configure_logging(settings.log_level)

# Create the FastAPI app — title appears in the auto-generated /docs UI
app = FastAPI(title=settings.app_name)

# Allow the Vite dev server and any configured frontend origin to call the API.
# In production, restrict allow_origins to the actual frontend domain.
_cors_origins = [
    "http://localhost:5173",   # Vite dev server
    "http://localhost:4173",   # Vite preview
    "http://localhost:8000",   # same-origin requests
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register the ingest router so POST /ingest is available
app.include_router(ingest_router)
app.include_router(retrieve_router)
app.include_router(chat_router)


@app.get("/health")
def health() -> dict[str, str]:
    # No rate limit here — load balancers and Docker health checks call this
    # endpoint continuously from internal IPs. Rate limiting it would cause
    # the service to be marked unhealthy and trigger unwanted restarts.
    return {"status": "ok", "service": settings.app_name}
