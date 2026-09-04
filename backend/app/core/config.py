"""
Application configuration, loaded from environment variables.

Secrets are never hardcoded. Alpaca credentials are normally supplied
interactively via POST /api/alpaca/connect and held only in the server-side
session (app/services/session_store.py) — never persisted to disk or logs.
Environment variables provide an optional fallback for startup.

The root `.env` is loaded explicitly so that running from any working directory
(the repo root via `run.py`, or `backend/` directly) picks up the same config.
"""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict

# Load the repo-root .env (and backend/.env) if present.
_ROOT = Path(__file__).resolve().parent.parent.parent
for _p in (_ROOT / ".env", _ROOT / "backend" / ".env"):
    if _p.exists():
        load_dotenv(dotenv_path=_p, override=False)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Alpaca — optional at startup. Users may instead connect interactively
    # via POST /api/alpaca/connect, in which case credentials live only in
    # the server-side session, never in this Settings object.
    alpaca_api_key: str | None = None
    alpaca_secret_key: str | None = None
    alpaca_paper: bool = True

    # Groq LLM Intelligence Settings (optional; deterministic fallback when unset)
    groq_api_key: str | None = None
    groq_model: str = "llama-3.3-70b-versatile"
    llm_api_key: str | None = None
    llm_model: str | None = None

    # App
    cors_origins: list[str] = ["http://localhost:5173", "http://localhost:3000"]
    session_secret: str = "dev-only-change-me"
    log_level: str = "INFO"

    # Execution safety
    trading_enabled: bool = False
    database_url: str | None = None


settings = Settings()