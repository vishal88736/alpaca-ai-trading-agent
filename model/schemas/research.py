"""
Research / multi-agent output schemas.

These structures flow between the deterministic research agents (market
intelligence, discovery, backtest, adversary, evolution/edge-score, portfolio
manager, performance monitor) and the API layer. They carry NO execution
authority — only the RiskEngine (see backend/app/services/risk_engine.py) can
gate an order.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class MarketRegime(BaseModel):
    regime: str = Field(description="BULLISH | BEARISH | SIDEWAYS | HIGH_VOLATILITY | LOW_VOLATILITY")
    confidence: float = Field(ge=0.0, le=1.0)
    volatility: str = "MEDIUM"
    momentum: str = "NEUTRAL"
    observations: list[str] = Field(default_factory=list)
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class BacktestMetricSet(BaseModel):
    total_return: float
    annualized_return: float
    win_rate: float
    profit_factor: float
    sharpe_ratio: float
    sortino_ratio: float
    max_drawdown: float
    num_trades: int
    volatility: float


class BacktestResult(BaseModel):
    backtest_id: str
    strategy_id: str
    symbol: str
    timeframe: str
    train: BacktestMetricSet
    oos: BacktestMetricSet
    oos_passed: bool
    equity_curve: list[float] = Field(default_factory=list)


class AdversaryReport(BaseModel):
    report_id: str
    strategy_id: str
    robustness_score: float = Field(ge=0.0, le=100.0)
    verdict: str = Field(description="PASS | WATCH | REJECT")
    weaknesses: list[str] = Field(default_factory=list)
    evidence: list[str] = Field(default_factory=list)
    failure_scenarios: list[str] = Field(default_factory=list)
    recommendation: str = ""


class StrategyRecord(BaseModel):
    strategy_id: str
    name: str
    hypothesis: str
    entry_rules: list[str] = Field(default_factory=list)
    exit_rules: list[str] = Field(default_factory=list)
    stop_loss_rules: list[str] = Field(default_factory=list)
    preferred_regime: str = "ANY"
    edge_score: float = Field(default=50.0, ge=0.0, le=100.0)
    status: str = Field(default="WATCH", description="ALIVE | WATCH | KILLED | REJECTED")
    status_reason: str = ""
    allocation_pct: float = 0.0
    parent_strategy_id: Optional[str] = None
    source: str = "builtin"


class Allocation(BaseModel):
    strategy_id: str
    allocation_pct: float
    allocation_amount: float


class AllocationPlan(BaseModel):
    allocations: list[Allocation] = Field(default_factory=list)
    cash_reserve_pct: float = 1.0
    cash_reserve_amount: float = 0.0
    deployed_pct: float = 0.0
    summary: str = ""


class PerformanceReport(BaseModel):
    strategy_id: str
    edge_deteriorating: bool
    previous_edge_score: float
    current_edge_score: float
    action: str
    message: str


class AgentEvent(BaseModel):
    agent: str
    action: str
    details: str
    strategy_id: Optional[str] = None
    symbol: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ExplainabilityReport(BaseModel):
    symbol: str
    action: str
    qty: float
    price: Optional[float] = None
    strategy_id: Optional[str] = None
    strategy_name: Optional[str] = None
    thesis: str
    evidence_checklist: list[dict] = Field(default_factory=list)
    signatures: list[dict] = Field(default_factory=list)