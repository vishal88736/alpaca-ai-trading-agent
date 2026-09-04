"""Pydantic schema validation tests."""

import pytest
from pydantic import ValidationError

from model.schemas.agent_state import AutomationConfig, RiskConfig
from model.schemas.trade_signal import Action, OrderRequest, TradeIntent, TradeSignal


def test_trade_signal_requires_positive_quantity():
    with pytest.raises(ValidationError):
        TradeSignal(symbol="AAPL", action=Action.BUY, quantity=-1, confidence=0.9, strategy="m", reasoning="x")


def test_trade_signal_confidence_bounds():
    with pytest.raises(ValidationError):
        TradeSignal(symbol="AAPL", action=Action.BUY, quantity=1, confidence=1.5, strategy="m", reasoning="x")


def test_trade_intent_requires_positive_quantity():
    with pytest.raises(ValidationError):
        TradeIntent(action=Action.BUY, symbol="AAPL", quantity=0, confidence=0.9, reasoning="x", source_strategy="m")


def test_order_request_requires_positive_quantity():
    with pytest.raises(ValidationError):
        OrderRequest(symbol="AAPL", action=Action.BUY, quantity=0)


def test_automation_config_defaults_paper():
    cfg = AutomationConfig(strategy="momentum", assets=["AAPL"])
    assert cfg.paper_trading is True
    assert isinstance(cfg.risk, RiskConfig)