"""
SQLite persistence layer (single-process deployment).

The live trading path does NOT depend on this: an order is only "executed" when
Alpaca returns a real order id/status (handled by alpaca_service). This database
is the audit trail — orders, decisions, research outputs, and agent events are
recorded here so the UI can display real history that survives a restart.
"""

from __future__ import annotations

import os
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

DEFAULT_DB_PATH = Path(__file__).resolve().parent.parent.parent / "trading_agent.db"
DATABASE_URL = os.environ.get("DATABASE_URL", f"sqlite:///{DEFAULT_DB_PATH}")

connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(DATABASE_URL, connect_args=connect_args, future=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, future=True)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    from app.db import models  # noqa: F401  (ensure models are registered)

    Base.metadata.create_all(bind=engine)