"""
Session-scoped dependencies.

A `session_id` cookie identifies the caller. Credentials themselves never
leave the server (see app/services/session_store.py) and are never exposed
back to the frontend after the initial connect call.
"""

from __future__ import annotations

import uuid

from fastapi import Cookie, HTTPException, Response

from app.core.config import settings
from app.services.alpaca_service import AlpacaService
from app.services.automation_engine import AutomationEngine
from app.services.session_store import AlpacaSession, session_store

SESSION_COOKIE = "session_id"

_alpaca_services: dict[str, AlpacaService] = {}
_automation_engines: dict[str, AutomationEngine] = {}


def get_or_create_session_id(response: Response, session_id: str | None = Cookie(default=None)) -> str:
    if session_id is None:
        session_id = str(uuid.uuid4())
        response.set_cookie(SESSION_COOKIE, session_id, httponly=True, samesite="lax")
    return session_id


def get_alpaca_service(session_id: str | None = Cookie(default=None)) -> AlpacaService:
    effective_id = session_id or "default"

    # Check if session exists in memory
    if session_store.is_connected(effective_id):
        if effective_id in _alpaca_services:
            return _alpaca_services[effective_id]
        session = session_store.get(effective_id)
        service = AlpacaService(session.api_key, session.secret_key, paper=session.paper)
        _alpaca_services[effective_id] = service
        return service

    # Check if environment variables provide valid Alpaca credentials
    if settings.alpaca_api_key and settings.alpaca_secret_key:
        env_session = AlpacaSession(
            api_key=settings.alpaca_api_key,
            secret_key=settings.alpaca_secret_key,
            paper=settings.alpaca_paper,
        )
        session_store.set(effective_id, env_session)
        service = AlpacaService(env_session.api_key, env_session.secret_key, paper=env_session.paper)
        _alpaca_services[effective_id] = service
        return service

    raise HTTPException(status_code=401, detail="Not connected to Alpaca. Call /api/alpaca/connect first.")


def get_optional_alpaca_service(session_id: str | None = Cookie(default=None)) -> AlpacaService | None:
    if session_id is None or not session_store.is_connected(session_id):
        return None
    try:
        return get_alpaca_service(session_id)
    except Exception:
        return None


def get_automation_engine(session_id: str | None = Cookie(default=None)) -> AutomationEngine:
    alpaca = get_alpaca_service(session_id)
    if session_id not in _automation_engines:
        _automation_engines[session_id] = AutomationEngine(alpaca)
    return _automation_engines[session_id]


def clear_session_services(session_id: str) -> None:
    _alpaca_services.pop(session_id, None)
    _automation_engines.pop(session_id, None)


def peek_automation_engine(session_id: str) -> AutomationEngine | None:
    """Non-creating lookup, used by the WebSocket endpoint."""
    return _automation_engines.get(session_id)
