"""Thin repository helpers over the SQLite audit trail.

Every write here is fire-and-forget from the perspective of the trading path:
if persistence fails we log it and continue (an order is real if Alpaca
returned a real id, irrespective of whether the audit write succeeded).
"""

from __future__ import annotations

import json
import logging
from typing import Any, Optional

from app.db.models import (
    AdversaryRecord,
    AgentEventRecord,
    BacktestRecord,
    DecisionRecord,
    OrderRecord,
    PortfolioSnapshot,
    StrategyRecordModel,
    TradeRecord,
)
from app.db.session import SessionLocal

logger = logging.getLogger("repository")


def save_order(order: dict, strategy: Optional[str] = None, paper: bool = True) -> None:
    try:
        with SessionLocal() as db:
            rec = OrderRecord(
                order_id=str(order.get("id")),
                client_order_id=order.get("client_order_id"),
                symbol=order.get("symbol"),
                side=order.get("side"),
                qty=float(order.get("qty") or 0.0),
                order_type=order.get("order_type", "market"),
                time_in_force=order.get("time_in_force", "day"),
                status=order.get("status", "submitted"),
                filled_avg_price=order.get("filled_avg_price"),
                strategy=strategy,
                paper=paper,
            )
            db.add(rec)
            db.commit()
    except Exception as exc:  # noqa: BLE001
        logger.warning("Failed to persist order: %s", exc)


def save_trade(order: dict, strategy: Optional[str], confidence: float = 0.0) -> None:
    try:
        with SessionLocal() as db:
            db.add(
                TradeRecord(
                    order_id=str(order.get("id")),
                    symbol=order.get("symbol"),
                    side=order.get("side"),
                    qty=float(order.get("qty") or 0.0),
                    price=float(order.get("filled_avg_price") or 0.0),
                    strategy=strategy,
                    confidence=confidence,
                    status=order.get("status", "filled"),
                )
            )
            db.commit()
    except Exception as exc:  # noqa: BLE001
        logger.warning("Failed to persist trade: %s", exc)


def save_decision(decision: dict) -> None:
    try:
        with SessionLocal() as db:
            db.add(
                DecisionRecord(
                    id=str(decision.get("id")),
                    symbol=decision.get("symbol"),
                    strategy=decision.get("strategy"),
                    signal=decision.get("signal"),
                    news_sentiment=decision.get("news_sentiment"),
                    confidence=float(decision.get("confidence") or 0.0),
                    risk_decision=decision.get("risk_decision"),
                    execution_result=decision.get("execution_result"),
                    reasoning=decision.get("reasoning", ""),
                )
            )
            db.commit()
    except Exception as exc:  # noqa: BLE001
        logger.warning("Failed to persist decision: %s", exc)


def save_strategy(strategy: dict) -> None:
    try:
        with SessionLocal() as db:
            rec = db.get(StrategyRecordModel, strategy.get("strategy_id"))
            if rec is None:
                rec = StrategyRecordModel(strategy_id=strategy.get("strategy_id"))
                db.add(rec)
            rec.name = strategy.get("name", rec.name or "")
            rec.hypothesis = strategy.get("hypothesis", "")
            rec.entry_rules_json = json.dumps(strategy.get("entry_rules", []))
            rec.exit_rules_json = json.dumps(strategy.get("exit_rules", []))
            rec.stop_loss_rules_json = json.dumps(strategy.get("stop_loss_rules", []))
            rec.preferred_regime = strategy.get("preferred_regime", "ANY")
            rec.edge_score = float(strategy.get("edge_score", 50.0))
            rec.status = strategy.get("status", "WATCH")
            rec.status_reason = strategy.get("status_reason", "")
            rec.allocation_pct = float(strategy.get("allocation_pct", 0.0))
            rec.parent_strategy_id = strategy.get("parent_strategy_id")
            rec.source = strategy.get("source", "builtin")
            db.commit()
    except Exception as exc:  # noqa: BLE001
        logger.warning("Failed to persist strategy: %s", exc)


def save_agent_event(event: dict) -> None:
    try:
        with SessionLocal() as db:
            db.add(
                AgentEventRecord(
                    agent=event.get("agent"),
                    action=event.get("action"),
                    details=event.get("details", ""),
                    strategy_id=event.get("strategy_id"),
                    symbol=event.get("symbol"),
                )
            )
            db.commit()
    except Exception as exc:  # noqa: BLE001
        logger.warning("Failed to persist agent event: %s", exc)


def save_backtest(backtest_id: str, result: dict) -> None:
    try:
        with SessionLocal() as db:
            db.add(
                BacktestRecord(
                    backtest_id=backtest_id,
                    strategy_id=result.get("strategy_id"),
                    symbol=result.get("symbol"),
                    timeframe=result.get("timeframe"),
                    result_json=json.dumps(result, default=str),
                )
            )
            db.commit()
    except Exception as exc:  # noqa: BLE001
        logger.warning("Failed to persist backtest: %s", exc)


def save_adversary_report(report: dict) -> None:
    try:
        with SessionLocal() as db:
            db.add(
                AdversaryRecord(
                    report_id=report.get("report_id"),
                    strategy_id=report.get("strategy_id"),
                    robustness_score=float(report.get("robustness_score", 50.0)),
                    verdict=report.get("verdict", "WATCH"),
                    report_json=json.dumps(report, default=str),
                )
            )
            db.commit()
    except Exception as exc:  # noqa: BLE001
        logger.warning("Failed to persist adversary report: %s", exc)


def save_portfolio_snapshot(snapshot: dict) -> None:
    try:
        with SessionLocal() as db:
            db.add(
                PortfolioSnapshot(
                    portfolio_value=float(snapshot.get("portfolio_value", 0.0)),
                    cash=float(snapshot.get("cash", 0.0)),
                    buying_power=float(snapshot.get("buying_power", 0.0)),
                    equity=float(snapshot.get("equity", 0.0)),
                    daily_pnl=float(snapshot.get("daily_pnl", 0.0)),
                )
            )
            db.commit()
    except Exception as exc:  # noqa: BLE001
        logger.warning("Failed to persist portfolio snapshot: %s", exc)


def list_records(model, limit: int = 50) -> list[Any]:
    try:
        with SessionLocal() as db:
            rows = db.query(model).order_by(model.timestamp.desc()).limit(limit).all() if hasattr(model, "timestamp") else db.query(model).limit(limit).all()
            return rows
    except Exception as exc:  # noqa: BLE001
        logger.warning("Failed to read records: %s", exc)
        return []