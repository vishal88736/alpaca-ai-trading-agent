"""
Trade signal / trade intent schemas.

These are the ONLY structured objects allowed to flow between:

    Strategy  ->  TradeSignal
    News      ->  NewsSignal
    Orchestrator -> TradeIntent
    Risk Engine  -> RiskDecision

No free-form natural language is ever allowed to reach the Alpaca execution
layer. Every action that could touch the broker must first be represented as
one of these validated Pydantic models.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class Action(str, Enum):
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"


class OrderType(str, Enum):
    MARKET = "MARKET"
    LIMIT = "LIMIT"
    STOP = "STOP"
    STOP_LIMIT = "STOP_LIMIT"


class TimeInForce(str, Enum):
    DAY = "DAY"
    GTC = "GTC"
    IOC = "IOC"
    FOK = "FOK"


class TradeSignal(BaseModel):
    """
    Output of a Strategy's `generate_signal()`.

    This represents the strategy's *opinion* about an asset. It is NOT
    an order and cannot be sent to Alpaca directly — it must pass through
    the LLM Orchestrator (for context fusion) and the Risk Engine (for
    hard validation) first.
    """

    symbol: str
    action: Action
    quantity: Optional[float] = Field(
        default=None, description="Suggested quantity. May be refined downstream."
    )
    order_type: OrderType = OrderType.MARKET
    confidence: float = Field(ge=0.0, le=1.0)
    strategy: str = Field(description="Registry key of the strategy that produced this signal")
    reasoning: str = Field(description="Concise, user-facing explanation. No hidden chain-of-thought.")
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    limit_price: Optional[float] = None
    stop_price: Optional[float] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    @field_validator("quantity")
    @classmethod
    def quantity_must_be_positive(cls, v: Optional[float]) -> Optional[float]:
        if v is not None and v <= 0:
            raise ValueError("quantity must be positive")
        return v


class NewsSignal(BaseModel):
    """Output of the News Strategy — structured sentiment/features, not raw text opinions."""

    symbol: str
    sentiment: str = Field(description="POSITIVE | NEGATIVE | NEUTRAL")
    sentiment_score: float = Field(ge=-1.0, le=1.0)
    summary: str
    source_count: int = 0
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class TradeIntent(BaseModel):
    """
    Output of the LLM Orchestrator.

    This fuses a TradeSignal + NewsSignal + portfolio/risk context into a
    single structured intent. It is still NOT an order — it must pass the
    deterministic Risk Engine before it can reach AlpacaService.
    """

    action: Action
    symbol: str
    quantity: float = Field(gt=0)
    order_type: OrderType = OrderType.MARKET
    time_in_force: TimeInForce = TimeInForce.DAY
    confidence: float = Field(ge=0.0, le=1.0)
    reasoning: str
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    limit_price: Optional[float] = None
    stop_price: Optional[float] = None
    source_strategy: str
    news_sentiment: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class RiskDecision(BaseModel):
    """Output of the Risk Engine — the final gate before Alpaca."""

    approved: bool
    trade_intent: TradeIntent
    rejection_reason: Optional[str] = None
    checks_passed: list[str] = Field(default_factory=list)
    checks_failed: list[str] = Field(default_factory=list)
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class OrderRequest(BaseModel):
    """
    Final, broker-ready order. Only ever constructed from an *approved*
    RiskDecision. This is the only object AlpacaService.submit_order()
    should accept.
    """

    symbol: str
    action: Action
    quantity: float = Field(gt=0)
    order_type: OrderType = OrderType.MARKET
    time_in_force: TimeInForce = TimeInForce.DAY
    limit_price: Optional[float] = None
    stop_price: Optional[float] = None
    client_order_id: Optional[str] = None
