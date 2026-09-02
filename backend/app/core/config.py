"""
Application configuration, loaded from environment variables.

No secrets are hardcoded here. In production, session-scoped Alpaca
credentials (entered via the Connect screen) are kept server-side only —
see app/services/session_store.py — and are never persisted to disk or logs.
"""

from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Alpaca — optional at startup. Users may instead connect interactively
    # via POST /api/alpaca/connect, in which case credentials live only in
    # the server-side session, never in this Settings object.
    alpaca_api_key: str | None = None
    alpaca_secret_key: str | None = None
    alpaca_paper: bool = True

    # Groq LLM Intelligence Settings
    groq_api_key: str | None = None
    groq_model: str = "llama-3.3-70b-versatile"
    llm_api_key: str | None = None
    llm_model: str | None = None

    # App
    cors_origins: list[str] = ["http://localhost:5173", "http://localhost:3000"]
    session_secret: str = "dev-only-change-me"  # override via env in real deployments
    log_level: str = "INFO"


settings = Settings()
