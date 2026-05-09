# Centralised application configuration.
# All settings are read from environment variables so the app can be configured
# differently in local, staging, and production without changing any code.
# Values come from the .env file locally, and from the cloud secrets manager in production.

from functools import lru_cache
import os

from dotenv import load_dotenv
from pydantic import BaseModel, Field, ValidationError


class Settings(BaseModel):
    """Holds all runtime configuration for the application.

    Pydantic validates every field on construction, so a misconfigured
    environment fails loudly at startup rather than silently at runtime.
    """

    # --- General ---
    app_name: str = "TrustRAG API"
    app_env: str = "local"       # local | staging | production
    log_level: str = "INFO"      # DEBUG | INFO | WARNING | ERROR

    # --- Chunking ---
    # chunk_size: how many characters per chunk (100–10000)
    # chunk_overlap: how many characters the next chunk shares with the previous one
    chunk_size: int = Field(default=800, ge=100, le=10000)
    chunk_overlap: int = Field(default=120, ge=0)

    # --- Rate limiting ---
    # /health is intentionally excluded — load balancers must not be rate-limited
    ingest_rate_limit_per_minute: int = Field(default=10, ge=1)
    retrieve_rate_limit_per_minute: int = Field(default=30, ge=1)
    chat_rate_limit_per_minute: int = Field(default=20, ge=1)

    # --- OpenAI ---
    openai_api_key: str = ""                                # Required for embeddings and chat
    openai_embedding_model: str = "text-embedding-3-small" # Model used to embed chunks
    openai_chat_model: str = "gpt-4o-mini"                 # Model used to generate answers

    # --- Pinecone ---
    pinecone_api_key: str = ""             # Required for vector storage and retrieval
    pinecone_index_name: str = "trustrag"  # Name of the Pinecone index to read/write
    pinecone_cloud: str = "aws"            # Cloud provider where the index is hosted
    pinecone_region: str = "us-east-1"    # Region of the Pinecone index
    # Must match the dimension the Pinecone index was created with.
    # text-embedding-3-small supports native dimension reduction via the dimensions param.
    pinecone_dimensions: int = Field(default=512, ge=64, le=3072)

    def model_post_init(self, __context: object) -> None:
        # Pydantic field constraints catch out-of-range values, but this cross-field
        # rule (overlap must be less than size) can only be checked here after both
        # values are set.
        if self.chunk_overlap >= self.chunk_size:
            raise ValueError("CHUNK_OVERLAP must be smaller than CHUNK_SIZE")


@lru_cache
def get_settings() -> Settings:
    """Load settings from environment variables and return a cached singleton.

    lru_cache ensures os.getenv is only called once per process, not on every request.
    Call get_settings.cache_clear() in tests to reset between test cases.
    """
    # Load .env file for local development; no-op in production where env vars are
    # injected directly by the container runtime or secrets manager.
    load_dotenv()
    try:
        return Settings(
            app_name=os.getenv("APP_NAME", "TrustRAG API"),
            app_env=os.getenv("APP_ENV", "local"),
            log_level=os.getenv("LOG_LEVEL", "INFO"),
            chunk_size=int(os.getenv("CHUNK_SIZE", "800")),
            chunk_overlap=int(os.getenv("CHUNK_OVERLAP", "120")),
            ingest_rate_limit_per_minute=int(os.getenv("INGEST_RATE_LIMIT_PER_MINUTE", "10")),
            retrieve_rate_limit_per_minute=int(os.getenv("RETRIEVE_RATE_LIMIT_PER_MINUTE", "30")),
            chat_rate_limit_per_minute=int(os.getenv("CHAT_RATE_LIMIT_PER_MINUTE", "20")),
            openai_api_key=os.getenv("OPENAI_API_KEY", ""),
            openai_embedding_model=os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small"),
            openai_chat_model=os.getenv("OPENAI_CHAT_MODEL", "gpt-4o-mini"),
            pinecone_api_key=os.getenv("PINECONE_API_KEY", ""),
            pinecone_index_name=os.getenv("PINECONE_INDEX_NAME", "trustrag"),
            pinecone_cloud=os.getenv("PINECONE_CLOUD", "aws"),
            pinecone_region=os.getenv("PINECONE_REGION", "us-east-1"),
            pinecone_dimensions=int(os.getenv("PINECONE_DIMENSIONS", "512")),
        )
    except (TypeError, ValueError, ValidationError) as exc:
        # Wrap in RuntimeError so callers don't need to handle Pydantic-specific exceptions
        raise RuntimeError(f"Invalid environment configuration: {exc}") from exc
