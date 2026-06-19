"""Central application configuration.

All settings are read from environment variables / `.env` in ONE place, so the
rest of the codebase never calls os.getenv directly and backends can be swapped
by configuration (the key idea behind making this service scalable).
"""
from functools import lru_cache
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # --- AWS / Bedrock ---
    aws_region: str = "us-east-1"
    bedrock_model_id: str = "anthropic.claude-3-haiku-20240307-v1:0"
    bedrock_embed_model_id: str = "amazon.titan-embed-text-v2:0"
    bedrock_image_model_id: str = "amazon.titan-image-generator-v2:0"

    # --- External tools ---
    serper_api_key: Optional[str] = None

    # --- Swappable backends (same code, chosen by env) ---
    vector_store: str = "chroma"      # chroma | pgvector
    image_backend: str = "bedrock"    # bedrock | local
    storage_backend: str = "local"    # local | s3
    job_store: str = "memory"         # memory | redis

    # --- Vector store ---
    chroma_dir: str = "./data/chroma"
    pg_connection: Optional[str] = None   # Phase 2 (pgvector)

    # --- Object storage ---
    s3_bucket: Optional[str] = None
    s3_presign_ttl: int = 3600
    local_files_dir: str = "./temp"

    # --- Jobs ---
    redis_url: str = "redis://localhost:6379/0"

    # --- Web ---
    frontend_origin: str = "http://localhost:8501"
    api_base: str = "http://localhost:8000"

    # --- RAG ---
    rag_top_k: int = 4
    chunk_size: int = 500
    chunk_overlap: int = 100


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
