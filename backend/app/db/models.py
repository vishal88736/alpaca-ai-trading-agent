"""ORM models for the audit trail / research persistence."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Float, Integer, String, Text

from app.db.session import Base


def _now() -> datetime:
    return datetime.utcnow()


class OrderRecord(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(String, index=True, nullable=False)          # Alpaca order id
    client_order_id = Column(String, nullable=True)
    symbol = Column(String, index=True)
    side = Column(String)
    qty = Column(Float, default=0.0)
    order_type = Column(String, default="market")
    time_in_force = Column(String, default="day")
    status = Column(String, default="submitted")                   # submitted/filled/rejected/cancelled
    filled_avg_price = Column(Float, nullable=True)
    strategy = Column(String, nullable=True)
    paper = Column(Boolean, default=True)
    submitted_at = Column(DateTime, default=_now)
    updated_at = Column(DateTime, default=_now, onupdate=_now)


class TradeRecord(Base):
    __tablename__ = "trades"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(String, index=True)
    symbol = Column(String, index=True)
    side = Column(String)
    qty = Column(Float, default=0.0)
    price = Column(Float, default=0.0)
    strategy = Column(String, nullable=True)
    confidence = Column(Float, default=0.0)
    status = Column(String, default="filled")
    timestamp = Column(DateTime, default=_now, index=True)


class DecisionRecord(Base):
    __tablename__ = "decisions"

    id = Column(String, primary_key=True, index=True)
    symbol = Column(String, index=True)
    strategy = Column(String, index=True)
    signal = Column(String)
    news_sentiment = Column(String, nullable=True)
    confidence = Column(Float, default=0.0)
    risk_decision = Column(String, nullable=True)   # APPROVED / REJECTED / ERROR
    execution_result = Column(Text, nullable=True)
    reasoning = Column(Text, default="")
    timestamp = Column(DateTime, default=_now, index=True)


class StrategyRecordModel(Base):
    __tablename__ = "strategies"

    strategy_id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False)
    hypothesis = Column(Text, default="")
    entry_rules_json = Column(Text, default="[]")
    exit_rules_json = Column(Text, default="[]")
    stop_loss_rules_json = Column(Text, default="[]")
    preferred_regime = Column(String, default="ANY")
    edge_score = Column(Float, default=50.0)
    status = Column(String, default="WATCH")
    status_reason = Column(Text, default="")
    allocation_pct = Column(Float, default=0.0)
    parent_strategy_id = Column(String, nullable=True)
    source = Column(String, default="builtin")
    created_at = Column(DateTime, default=_now)
    updated_at = Column(DateTime, default=_now, onupdate=_now)


class BacktestRecord(Base):
    __tablename__ = "backtests"

    backtest_id = Column(String, primary_key=True, index=True)
    strategy_id = Column(String, index=True)
    symbol = Column(String)
    timeframe = Column(String, default="1D")
    result_json = Column(Text, default="{}")
    created_at = Column(DateTime, default=_now, index=True)


class AdversaryRecord(Base):
    __tablename__ = "adversary_reports"

    report_id = Column(String, primary_key=True, index=True)
    strategy_id = Column(String, index=True)
    robustness_score = Column(Float, default=50.0)
    verdict = Column(String, default="WATCH")
    report_json = Column(Text, default="{}")
    created_at = Column(DateTime, default=_now)


class PortfolioSnapshot(Base):
    __tablename__ = "portfolio_snapshots"

    id = Column(Integer, primary_key=True, index=True)
    portfolio_value = Column(Float, default=0.0)
    cash = Column(Float, default=0.0)
    buying_power = Column(Float, default=0.0)
    equity = Column(Float, default=0.0)
    daily_pnl = Column(Float, default=0.0)
    timestamp = Column(DateTime, default=_now, index=True)


class AgentEventRecord(Base):
    __tablename__ = "agent_events"

    id = Column(Integer, primary_key=True, index=True)
    agent = Column(String, index=True)
    action = Column(String)
    details = Column(Text)
    strategy_id = Column(String, nullable=True)
    symbol = Column(String, nullable=True)
    timestamp = Column(DateTime, default=_now, index=True)