"""
Market data schemas.

These are the shapes that flow FROM AlpacaService / the market-data layer
INTO strategies and the orchestrator. Keeping this schema separate from the
Alpaca SDK's own types keeps strategy code broker-agnostic — if a strategy
ever needs a non-Alpaca data source, only the adapter layer needs to change.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class AssetClass(str, Enum):
    US_EQUITY = "us_equity"
    CRYPTO = "crypto"


class Bar(BaseModel):
    """A single OHLCV bar."""

    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float


class Timeframe(str, Enum):
    MIN_1 = "1m"
    MIN_5 = "5m"
    MIN_15 = "15m"
    HOUR_1 = "1h"
    DAY_1 = "1D"


class Quote(BaseModel):
    symbol: str
    bid_price: float
    ask_price: float
    bid_size: float
    ask_size: float
    timestamp: datetime


class MarketData(BaseModel):
    """
    The bundle passed into `Strategy.analyze()` / `generate_signal()`.

    Deliberately generic — strategies should not need to know whether bars
    came from Alpaca's stock or crypto data feed.
    """

    symbol: str
    asset_class: AssetClass
    timeframe: Timeframe
    bars: list[Bar] = Field(default_factory=list)
    latest_quote: Optional[Quote] = None


class AssetInfo(BaseModel):
    """Tradability metadata for an asset, as surfaced by the asset selector UI."""

    symbol: str
    name: str
    asset_class: AssetClass
    exchange: str
    tradable: bool
    fractionable: bool = False
