"""
Automation / agent state schemas.

These describe the runtime state of the automation engine — what the
"AUTOMATION RUNNING" panel in the dashboard renders from.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field

from model.schemas.trade_signal import Action, RiskDecision


class AutomationState(str, Enum):
    IDLE = "IDLE"
    RUNNING = "RUNNING"
    PAUSED = "PAUSED"
    STOPPED = "STOPPED"
    EMERGENCY_STOPPED = "EMERGENCY_STOPPED"


class RiskConfig(BaseModel):
    """User-configured risk limits, set on the Automation Configuration screen."""

    max_position_pct: float = Field(default=10.0, description="Max % of portfolio in one asset")
    max_portfolio_exposure_pct: float = Field(default=50.0)
    max_order_size_usd: float = Field(default=1000.0)
    max_daily_loss_pct: float = Field(default=2.0)
    max_trades_per_day: int = Field(default=20)
    max_open_positions: int = Field(default=10, description="Max distinct open positions")
    max_drawdown_pct: float = Field(default=10.0, description="Max portfolio drawdown from peak before trading halts")
    require_market_open: bool = Field(default=True, description="Block equity orders while the market is closed")
    stop_loss_pct: Optional[float] = None
    take_profit_pct: Optional[float] = None


class AutomationConfig(BaseModel):
    """Full configuration submitted from the Automation Configuration UI."""

    strategy: str
    assets: list[str]
    timeframe: str = "15m"
    risk: RiskConfig = Field(default_factory=RiskConfig)
    paper_trading: bool = True
    strategy_params: dict = Field(default_factory=dict, description="Optional per-strategy parameter overrides")


class Decision(BaseModel):
    """A single entry in the AI Decision Log."""

    id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    symbol: str
    strategy: str
    signal: Action
    news_sentiment: Optional[str] = None
    confidence: float
    risk_decision: Optional[RiskDecision] = None
    execution_result: Optional[str] = None
    reasoning: str


class AutomationStatus(BaseModel):
    """Snapshot returned by GET /api/automation/status."""

    state: AutomationState
    strategy: Optional[str] = None
    assets: list[str] = Field(default_factory=list)
    started_at: Optional[datetime] = None
    signals_count: int = 0
    trades_count: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    current_pnl: float = 0.0
    latest_decision: Optional[Decision] = None
