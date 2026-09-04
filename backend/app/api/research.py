"""
Research & agent-activity API — market regime, discovery, backtest, adversary,
edge scoring, and the agent event feed.

These are read/analysis endpoints: they never place orders. Execution remains
gated by the deterministic risk engine via the automation router.
"""

from __future__ import annotations

import json
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query

from app.agents.adversary import adversary_agent
from app.agents.backtest import backtest_engine
from app.agents.discovery import discovery_agent
from app.agents.evolution import evolution_engine
from app.agents.market_intelligence import market_intel_agent
from app.agents.portfolio_manager import portfolio_manager_agent
from app.core.deps import get_alpaca_service, get_automation_engine
from app.db import repository
from app.db.models import AdversaryRecord, BacktestRecord
from app.services.alpaca_service import AlpacaService
from app.services.automation_engine import AutomationEngine
from model.schemas.research import BacktestResult, MarketRegime
from model.strategies.registry import STRATEGIES, STRATEGY_METADATA, get_strategy

router = APIRouter(prefix="/api", tags=["research"])


@router.get("/market-regime", response_model=MarketRegime)
def get_market_regime(engine: AutomationEngine = Depends(get_automation_engine)):
    if engine.current_regime:
        return MarketRegime(**engine.current_regime)
    # Compute on-demand if the loop has not run yet
    benchmark = "SPY"
    try:
        alpaca = engine.alpaca
        bars = alpaca.get_market_data(benchmark, timeframe="1D", limit=60)
        if bars and bars.bars:
            return market_intel_agent.analyze_market_regime(bars.bars, benchmark)
    except Exception:  # noqa: BLE001
        pass
    return MarketRegime(regime="SIDEWAYS", confidence=0.5, volatility="UNKNOWN", momentum="NEUTRAL", observations=["Regime not yet computed"])


@router.post("/research/discover")
def run_discovery(engine: AutomationEngine = Depends(get_automation_engine)):
    strategy_key = engine.config.strategy if engine.config else "momentum"
    regime = (engine.current_regime or {}).get("regime", "SIDEWAYS")
    strat = discovery_agent.generate_strategy(strategy_key, regime)
    repository.save_strategy(strat)
    engine._add_event("Discovery", "PROPOSE_HYPOTHESIS", f"Proposed '{strat['name']}' for {regime} regime.", strat["strategy_id"])
    return {"status": "success", "strategy": strat}


@router.post("/research/backtest")
def run_backtest(
    strategy: str = Query(..., description="Strategy registry key"),
    symbol: str = Query("AAPL"),
    timeframe: str = Query("1D"),
    limit: int = Query(250, ge=60, le=1000),
    alpaca: AlpacaService = Depends(get_alpaca_service),
    engine: AutomationEngine = Depends(get_automation_engine),
):
    if strategy not in STRATEGIES:
        raise HTTPException(status_code=404, detail=f"Unknown strategy: {strategy}")

    data = alpaca.get_market_data(symbol, timeframe=timeframe, limit=limit)
    if data is None or not data.bars:
        raise HTTPException(status_code=422, detail=f"No historical data available for {symbol} ({timeframe})")

    strat = get_strategy(strategy)
    strat.initialize(getattr(engine.config, "strategy_params", {}) if engine.config else {})

    try:
        result = backtest_engine.run_backtest(strat, data.bars, symbol=symbol, timeframe=timeframe, strategy_id=strategy)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    repository.save_backtest(result["backtest_id"], result)
    engine._add_event("Backtest", "WALK_FORWARD_VALIDATE", f"{symbol}: OOS Sharpe {result['oos']['sharpe_ratio']}, passed={result['oos_passed']}", strategy)
    return result


@router.post("/research/run")
def run_research_cycle(
    strategy: str = Query(...),
    symbol: str = Query("AAPL"),
    timeframe: str = Query("1D"),
    limit: int = Query(250, ge=60, le=1000),
    alpaca: AlpacaService = Depends(get_alpaca_service),
    engine: AutomationEngine = Depends(get_automation_engine),
):
    """Full discovery → backtest → adversary → edge scoring cycle (read-only)."""
    if strategy not in STRATEGIES:
        raise HTTPException(status_code=404, detail=f"Unknown strategy: {strategy}")

    regime = (engine.current_regime or {}).get("regime", "SIDEWAYS")
    strat = discovery_agent.generate_strategy(strategy, regime)

    data = alpaca.get_market_data(symbol, timeframe=timeframe, limit=limit)
    if data is None or not data.bars:
        raise HTTPException(status_code=422, detail=f"No historical data available for {symbol}")

    instance = get_strategy(strategy)
    instance.initialize({})
    bt = backtest_engine.run_backtest(instance, data.bars, symbol=symbol, timeframe=timeframe, strategy_id=strategy)
    adv = adversary_agent.stress_test_strategy(strat, bt)
    edge = evolution_engine.calculate_edge_score(bt, adv)
    status, reason = evolution_engine.determine_lifecycle_state(edge, adv["verdict"])

    strat["edge_score"] = edge
    strat["status"] = status
    strat["status_reason"] = reason

    repository.save_strategy(strat)
    repository.save_backtest(bt["backtest_id"], bt)
    repository.save_adversary_report(adv)

    engine._add_event("Adversary", "STRESS_TEST", f"{symbol}: robustness {adv['robustness_score']}/100 ({adv['verdict']})", strategy)
    engine._add_event("Strategy Darwinism", "UPDATE_LIFECYCLE", f"'{strat['name']}' edge {edge}/100 -> {status}", strat["strategy_id"])

    return {"strategy": strat, "backtest": bt, "adversary_report": adv, "regime": regime}


@router.get("/research/backtests")
def list_backtests(limit: int = Query(20, ge=1, le=100)):
    rows = repository.list_records(BacktestRecord, limit)
    out = []
    for r in rows:
        item = {"backtest_id": r.backtest_id, "strategy_id": r.strategy_id, "symbol": r.symbol, "timeframe": r.timeframe, "created_at": r.created_at.isoformat() if r.created_at else None}
        try:
            item["result"] = json.loads(r.result_json)
        except Exception:  # noqa: BLE001
            item["result"] = {}
        out.append(item)
    return out


@router.get("/agents/events")
def agent_events(engine: AutomationEngine = Depends(get_automation_engine), limit: int = Query(100, ge=1, le=500)):
    return engine.get_agent_events(limit=limit)


@router.get("/research/strategies")
def research_strategies():
    return [
        {"key": key, "execution_mode": STRATEGY_METADATA.get(key, {}).get("execution_mode", "research"), **STRATEGY_METADATA.get(key, {})}
        for key in STRATEGIES
    ]