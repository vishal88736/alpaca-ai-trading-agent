"""
In-memory server-side session store.

Alpaca credentials submitted via POST /api/alpaca/connect are held ONLY
here — never written to disk, never logged, never echoed back to the
frontend. The frontend only ever sees a `connected: bool` status.

This is intentionally a simple in-memory dict, keyed by session id, which
is sufficient for a single-process hackathon deployment. For a
multi-process/production deployment, replace this with a proper encrypted
server-side session store (e.g. Redis with encryption at rest) — do not
move credential storage to the client.
"""

from __future__ import annotations

import threading
from dataclasses import dataclass
from typing import Optional


@dataclass
class AlpacaSession:
    api_key: str
    secret_key: str
    paper: bool = True


class SessionStore:
    def __init__(self) -> None:
        self._sessions: dict[str, AlpacaSession] = {}
        self._lock = threading.Lock()

    def set(self, session_id: str, session: AlpacaSession) -> None:
        with self._lock:
            self._sessions[session_id] = session

    def get(self, session_id: str) -> Optional[AlpacaSession]:
        with self._lock:
            return self._sessions.get(session_id)

    def clear(self, session_id: str) -> None:
        with self._lock:
            self._sessions.pop(session_id, None)

    def is_connected(self, session_id: str) -> bool:
        return self.get(session_id) is not None


session_store = SessionStore()
