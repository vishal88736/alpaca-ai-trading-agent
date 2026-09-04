"""
Mandatory end-to-end paper-trading test.

Proves the full real execution path against an isolated broker test double that
reproduces the AlpacaService contract:

    MarketData -> Strategy (signal) -> LLM orchestrator (intent)
      -> Deterministic RiskEngine (approve) -> OrderRequest
      -> broker.submit_order() -> real order id + status
      -> decision recorded with execution result

This test FAILS if the system only generates a signal but never submits an order.
"""

import asyncio

from model.schemas.agent_state import AutomationConfig
from model.strategies.registry import get_strategy
from app.services.automation_engine import AutomationEngine
from app.services.risk_engine import RiskEngine
from tests.conftest import FakeAlpacaBroker


async def _fake_fetch_news(symbols=None, limit=20):
    return []  # no network, no fake sentiment


def _make_engine(broker, strategy_key):
    engine = AutomationEngine(broker)
    engine.config = AutomationConfig(strategy=strategy_key, assets=["TEST/USD"], timeframe="1h")
    engine.risk_engine = RiskEngine(engine.config.risk, allowed_assets=["TEST/USD"])
    return engine


def test_signal_flows_all_the_way_to_submitted_order(monkeypatch):
    monkeypatch.setattr("app.services.automation_engine.fetch_news", _fake_fetch_news)

    broker = FakeAlpacaBroker(buying_power=100000.0)
    engine = _make_engine(broker, "momentum")
    strategy = get_strategy("momentum")
    strategy.initialize({})

    # Before processing, no orders have been submitted.
    assert broker.submitted == []

    asyncio.run(engine._process_symbol(strategy, "TEST/USD"))

    # The broker actually received an order request -> real submission happened.
    assert len(broker.submitted) == 1, "Expected exactly one order to be submitted to the broker"
    order = broker.submitted[0]
    assert order["id"].startswith("fake-order-")
    assert order["symbol"] == "TEST/USD"
    assert order["status"] in ("accepted", "filled")

    # The engine counts it and records a decision with a real execution result.
    assert engine.trades_count == 1
    assert engine.decisions, "A decision should have been recorded"
    last = engine.decisions[-1]
    assert last.execution_result and not last.execution_result.startswith("REJECTED")
    assert order["id"] in last.execution_result


def test_rejected_signal_never_submits_order(monkeypatch):
    monkeypatch.setattr("app.services.automation_engine.fetch_news", _fake_fetch_news)

    broker = FakeAlpacaBroker(buying_power=100000.0)
    engine = _make_engine(broker, "momentum")
    # Allow-list excludes the scanned symbol -> risk must reject before submission.
    engine.risk_engine = RiskEngine(engine.config.risk, allowed_assets=["OTHER/USD"])
    strategy = get_strategy("momentum")
    strategy.initialize({})

    asyncio.run(engine._process_symbol(strategy, "TEST/USD"))

    assert broker.submitted == [], "Risk must block the order entirely"
    assert engine.trades_count == 0


def test_research_strategy_is_never_auto_executed(monkeypatch):
    monkeypatch.setattr("app.services.automation_engine.fetch_news", _fake_fetch_news)

    broker = FakeAlpacaBroker(buying_power=100000.0)
    engine = _make_engine(broker, "market_making")
    strategy = get_strategy("market_making")
    strategy.initialize({})

    asyncio.run(engine._process_symbol(strategy, "TEST/USD"))

    # market_making is `research` mode: may analyze but must NOT submit orders.
    assert broker.submitted == [], "Research strategies must not auto-execute"
    if engine.decisions:
        assert engine.decisions[-1].execution_result in ("HOLD", "NO_INTENT", "RESEARCH_ONLY", None) or engine.decisions[-1].execution_result in ("RESEARCH_ONLY",)


def test_kill_switch_blocks_all_submissions(monkeypatch):
    monkeypatch.setattr("app.services.automation_engine.fetch_news", _fake_fetch_news)

    broker = FakeAlpacaBroker(buying_power=100000.0)
    engine = _make_engine(broker, "momentum")
    engine.risk_engine.engage_kill_switch()
    strategy = get_strategy("momentum")
    strategy.initialize({})

    asyncio.run(engine._process_symbol(strategy, "TEST/USD"))

    assert broker.submitted == []
    assert engine.trades_count == 0