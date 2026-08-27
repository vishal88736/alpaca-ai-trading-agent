from __future__ import annotations

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import account, alpaca, automation, decisions, market, news, strategies
from app.core.config import settings
from app.ws import live

logging.basicConfig(level=settings.log_level)

app = FastAPI(
    title="AI Trading Agent Platform (Alpaca Paper Trading)",
    version="0.1.0",
    description="Hackathon scaffold. Paper trading only. See /model for strategy stubs.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(alpaca.router)
app.include_router(account.router)
app.include_router(market.router)
app.include_router(news.router)
app.include_router(strategies.router)
app.include_router(automation.router)
app.include_router(decisions.router)
app.include_router(live.router)


@app.get("/api/health")
def health():
    return {"status": "ok", "mode": "paper_trading"}
