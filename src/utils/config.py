from functools import lru_cache
import os

from pydantic import BaseModel, Field, ValidationError


class Settings(BaseModel):
    app_name: str = "TrustRAG API"
    app_env: str = "local"
    log_level: str = "INFO"
    chunk_size: int = Field(default=800, ge=100, le=10000)
    chunk_overlap: int = Field(default=120, ge=0)

    # OpenAI
    openai_api_key: str = ""
    openai_embedding_model: str = "text-embedding-3-small"
    openai_chat_model: str = "gpt-4o-mini"

    # Pinecone
    pinecone_api_key: str = ""
    pinecone_index_name: str = "trustrag"
    pinecone_cloud: str = "aws"
    pinecone_region: str = "us-east-1"

    def model_post_init(self, __context: object) -> None:
        if self.chunk_overlap >= self.chunk_size:
            raise ValueError("CHUNK_OVERLAP must be smaller than CHUNK_SIZE")


@lru_cache
def get_settings() -> Settings:
    try:
        return Settings(
            app_name=os.getenv("APP_NAME", "TrustRAG API"),
            app_env=os.getenv("APP_ENV", "local"),
            log_level=os.getenv("LOG_LEVEL", "INFO"),
            chunk_size=int(os.getenv("CHUNK_SIZE", "800")),
            chunk_overlap=int(os.getenv("CHUNK_OVERLAP", "120")),
            openai_api_key=os.getenv("OPENAI_API_KEY", ""),
            openai_embedding_model=os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small"),
            openai_chat_model=os.getenv("OPENAI_CHAT_MODEL", "gpt-4o-mini"),
            pinecone_api_key=os.getenv("PINECONE_API_KEY", ""),
            pinecone_index_name=os.getenv("PINECONE_INDEX_NAME", "trustrag"),
            pinecone_cloud=os.getenv("PINECONE_CLOUD", "aws"),
            pinecone_region=os.getenv("PINECONE_REGION", "us-east-1"),
        )
    except (TypeError, ValueError, ValidationError) as exc:
        raise RuntimeError(f"Invalid environment configuration: {exc}") from exc
