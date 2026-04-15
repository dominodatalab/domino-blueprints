# config.py
"""Configuration and environment settings."""

import os
from pathlib import Path
from pydantic_settings import BaseSettings
from pydantic import model_validator
from functools import lru_cache
from typing import Literal
import requests


# Provider-specific model defaults
MODEL_DEFAULTS = {
    "openai": {
        "refinement": "gpt-4o-mini",
        "generation": "gpt-4o",
    },
    "anthropic": {
        "refinement": "claude-3-haiku-20240307",
        "generation": "claude-sonnet-4-20250514",
    },
}


class Settings(BaseSettings):
    """Application settings loaded from environment."""

    # API Keys
    openai_api_key: str = ""
    anthropic_api_key: str = ""

    # Vector DB
    qdrant_url: str = "http://localhost:6333"
    qdrant_api_key: str | None = None

    # Domino API Proxy (for fetching access tokens)
    domino_api_proxy: str | None = None

    # Collections
    incidents_collection: str = "ntsb_incidents"
    regulations_collection: str = "far_regulations"
    news_collection: str = "aviation_news"

    # Embedding configuration
    # embedder: "local" for sentence-transformers, "openai" for OpenAI API
    embedder: Literal["local", "openai"] = "local"
    # embedding_model: model name (varies by embedder)
    # Local models: all-MiniLM-L6-v2, BAAI/bge-base-en-v1.5, etc.
    # OpenAI models: text-embedding-3-small, text-embedding-3-large
    embedding_model: str = "BAAI/bge-base-en-v1.5"

    # LLM Provider: "openai" or "anthropic"
    llm_provider: Literal["openai", "anthropic"] = "anthropic"

    # LLM Models - set via environment variables or use provider-appropriate defaults
    # OpenAI: gpt-4o, gpt-4o-mini
    # Anthropic: claude-sonnet-4-20250514, claude-3-haiku-20240307
    # Empty string means "use provider default"
    refinement_model: str = ""
    generation_model: str = ""

    @model_validator(mode="after")
    def set_model_defaults(self) -> "Settings":
        """Set provider-appropriate model defaults if not explicitly configured."""
        defaults = MODEL_DEFAULTS.get(self.llm_provider, MODEL_DEFAULTS["anthropic"])

        if not self.refinement_model:
            object.__setattr__(self, "refinement_model", defaults["refinement"])
        if not self.generation_model:
            object.__setattr__(self, "generation_model", defaults["generation"])

        return self

    # Retrieval defaults
    default_top_k: int = 10
    default_refinement_mode: str = "dedup"

    # MLflow
    mlflow_tracking_uri: str = "http://localhost:5001"
    mlflow_enabled: bool = True
    mlflow_experiment_name: str = "agentic-rag-aviation"

    # Paths
    data_dir: Path = Path(__file__).parent.parent.parent.parent / "data" / "aviation"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


def get_domino_access_token() -> str | None:
    """
    Fetch access token from Domino API proxy.

    Returns None if DOMINO_API_PROXY is not set or token fetch fails.
    """
    settings = get_settings()
    if not settings.domino_api_proxy:
        return None

    try:
        response = requests.get(f"{settings.domino_api_proxy}/access-token", timeout=10)
        response.raise_for_status()
        return response.text.strip()
    except Exception as e:
        print(f"Warning: Failed to get Domino access token: {e}")
        return None
