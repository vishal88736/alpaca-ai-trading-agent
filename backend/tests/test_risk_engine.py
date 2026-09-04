"""Deterministic risk-engine unit tests."""

from datetime import datetime

from model.schemas.agent_state import RiskConfig
from model.schemas.trade_signal import Action, TradeIntent
from app.services.risk_engine import DailyRiskCounters, RiskEngine


def _intent(symbol="AAPL", qty=10, action=Action.BUY, limit=None):
    return TradeIntent(
        action=action,
        symbol=symbol,
        quantity=qty,
        confidence=0.8,
        reasoning="test",
        source_strategy="momentum",
        limit_price=limit,
        timestamp=datetime(2024, 1, 1, 12, 0, 0),
    )


def _account(portfolio_value=100000.0, buying_power=50000.0):
    return {"portfolio_value": portfolio_value, "buying_power": buying_power}


def _positions():
    return {"NVDA": {"symbol": "NVDA", "market_value": 5000.0, "current_price": 100.0}}


def test_rejects_non_selected_asset():
    engine = RiskEngine(RiskConfig(), allowed_assets=["NVDA"])
    dec = engine.evaluate(_intent("AAPL"), _account(), _positions(), DailyRiskCounters())
    assert dec.approved is False
    assert "asset_not_in_user_selection" in dec.checks_failed


def test_rejects_invalid_symbol():
    engine = RiskEngine(RiskConfig(), allowed_assets=["!!!bad"])
    dec = engine.evaluate(_intent("!!!bad"), _account(), _positions(), DailyRiskCounters())
    assert "invalid_symbol" in dec.checks_failed


def test_rejects_insufficient_buying_power():
    engine = RiskEngine(RiskConfig(max_order_size_usd=1_000_000.0, max_position_pct=100.0), allowed_assets=["AAPL"])
    positions = {"AAPL": {"market_value": 0.0, "current_price": 200.0}}
    dec = engine.evaluate(_intent("AAPL", qty=1000), _account(buying_power=1000.0), positions, DailyRiskCounters())
    assert "insufficient_buying_power" in dec.checks_failed


def test_rejects_exceeding_max_order_size():
    engine = RiskEngine(RiskConfig(max_order_size_usd=100.0), allowed_assets=["AAPL"])
    positions = {"AAPL": {"market_value": 0.0, "current_price": 200.0}}
    dec = engine.evaluate(_intent("AAPL", qty=10), _account(), positions, DailyRiskCounters())
    assert "max_order_size_exceeded" in dec.checks_failed


def test_rejects_closed_market_for_equity():
    engine = RiskEngine(RiskConfig(require_market_open=True), allowed_assets=["AAPL"])
    positions = {"AAPL": {"market_value": 0.0, "current_price": 10.0}}
    dec = engine.evaluate(_intent("AAPL", qty=1), _account(), positions, DailyRiskCounters(), market_open=False)
    assert "market_closed" in dec.checks_failed


def test_crypto_ignores_market_hours():
    engine = RiskEngine(RiskConfig(require_market_open=True), allowed_assets=["BTC/USD"])
    positions = {"BTC/USD": {"market_value": 0.0, "current_price": 10.0}}
    dec = engine.evaluate(_intent("BTC/USD", qty=1), _account(), positions, DailyRiskCounters(), market_open=False)
    assert "market_closed" not in dec.checks_failed


def test_rejects_max_open_positions():
    engine = RiskEngine(RiskConfig(max_open_positions=1), allowed_assets=["AAPL"])
    positions = {"NVDA": {"market_value": 100.0, "current_price": 50.0}}
    dec = engine.evaluate(_intent("AAPL", qty=1), _account(), positions, DailyRiskCounters())
    assert "max_open_positions_exceeded" in dec.checks_failed


def test_kill_switch_blocks_everything():
    engine = RiskEngine(RiskConfig(), allowed_assets=["AAPL"])
    engine.engage_kill_switch()
    positions = {"AAPL": {"market_value": 0.0, "current_price": 10.0}}
    dec = engine.evaluate(_intent("AAPL", qty=1), _account(), positions, DailyRiskCounters())
    assert "kill_switch_engaged" in dec.checks_failed


def test_approves_valid_trade_and_builds_order_request():
    engine = RiskEngine(RiskConfig(max_open_positions=10, max_position_pct=50.0), allowed_assets=["AAPL"])
    positions = {"AAPL": {"market_value": 1000.0, "current_price": 100.0}}
    dec = engine.evaluate(_intent("AAPL", qty=5), _account(buying_power=100000.0), positions, DailyRiskCounters())
    assert dec.approved is True
    req = RiskEngine.to_order_request(dec)
    assert req.symbol == "AAPL"
    assert req.quantity == 5


def test_to_order_request_rejects_rejected_decision():
    engine = RiskEngine(RiskConfig(), allowed_assets=["NVDA"])
    dec = engine.evaluate(_intent("AAPL"), _account(), _positions(), DailyRiskCounters())
    try:
        RiskEngine.to_order_request(dec)
        assert False, "expected ValueError"
    except ValueError:
        pass