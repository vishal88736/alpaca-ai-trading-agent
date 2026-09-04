"""Strategy signal + registry classification tests."""

from model.schemas.trade_signal import Action, TradeSignal
from model.strategies.registry import (
    STRATEGIES,
    STRATEGY_METADATA,
    get_strategy,
    is_live_executable,
)


def test_all_strategies_registered():
    expected = {
        "options_alpha_income",
        "momentum",
        "mean_reversion",
        "market_making",
        "funding_arbitrage",
        "cross_exchange_arbitrage",
    }
    assert set(STRATEGIES) >= expected


def test_execution_mode_classification():
    # Live-executable strategies
    assert is_live_executable("momentum")
    assert is_live_executable("mean_reversion")
    assert is_live_executable("options_alpha_income")
    # Research / external-venue strategies are NOT auto-executed
    assert not is_live_executable("market_making")
    assert not is_live_executable("funding_arbitrage")
    assert not is_live_executable("cross_exchange_arbitrage")


def test_get_strategy_instantiates():
    for key in STRATEGIES:
        s = get_strategy(key)
        assert s.name == key


def test_momentum_signal_on_uptrend(trend_market_data):
    s = get_strategy("momentum")
    s.initialize({})
    signal = s.generate_signal(trend_market_data, portfolio={}, news=None)
    assert isinstance(signal, TradeSignal)
    assert signal.action == Action.BUY
    assert signal.quantity > 0


def test_mean_reversion_returns_signal_or_none(trend_market_data):
    s = get_strategy("mean_reversion")
    s.initialize({})
    signal = s.generate_signal(trend_market_data, portfolio={}, news=None)
    # In a clean uptrend the z-score is high: expect a SELL (overbought) or None.
    if signal is not None:
        assert isinstance(signal, TradeSignal)
        assert signal.action in (Action.BUY, Action.SELL)


def test_funding_arbitrage_yields_no_fake_signal(trend_market_data):
    s = get_strategy("funding_arbitrage")
    s.initialize({})
    # No external funding-rate data -> must NOT fabricate a signal.
    assert s.generate_signal(trend_market_data, portfolio={}, news=None) is None


def test_cross_exchange_yields_no_fake_signal(trend_market_data):
    s = get_strategy("cross_exchange_arbitrage")
    s.initialize({})
    # No second venue -> must NOT fabricate a cross-exchange signal.
    assert s.generate_signal(trend_market_data, portfolio={}, news=None) is None