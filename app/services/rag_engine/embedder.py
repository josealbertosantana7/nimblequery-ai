"""Bedrock embeddings, built once from config."""
from functools import lru_cache

from langchain_aws import BedrockEmbeddings

from app.core.config import settings


@lru_cache
def get_embedder() -> BedrockEmbeddings:
    return BedrockEmbeddings(
        model_id=settings.bedrock_embed_model_id,
        region_name=settings.aws_region,
    )
