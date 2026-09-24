"""Runtime configuration, loaded from environment / .env.

The model id is configurable; it defaults to a current Claude model. Every
setting can be overridden from the environment so deployments need no code change.
"""

from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings (see .env.example)."""

    anthropic_api_key: str = ""
    model: str = "claude-sonnet-4-6"
    temperature: float = 0.0
    max_retrieved_docs: int = 4
    chroma_collection: str = "electra_charging_kb"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance."""
    return Settings()
