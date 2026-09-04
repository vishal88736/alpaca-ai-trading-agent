"""Backtest, adversary, and portfolio manager tests."""

from app.agents.backtest import BacktestEngine
from app.agents.adversary import adversary_agent
from app.agents.portfolio_manager import portfolio_manager_agent
from app.agents.evolution import evolution_engine
from model.strategies.registry import get_strategy


def test_backtest_chronological_split_and_metrics(trend_market_data):
    strategy = get_strategy("momentum")
    strategy.initialize({})
    bt = BacktestEngine().run_backtest(strategy, trend_market_data.bars, symbol="TEST/USD", timeframe="1h", strategy_id="momentum")

    assert bt["backtest_id"].startswith("BT-")
    assert "oos_passed" in bt
    for section in ("train", "oos"):
        for key in ("sharpe_ratio", "sortino_ratio", "win_rate", "profit_factor", "max_drawdown", "num_trades"):
            assert key in bt[section]
    # equity curve is non-empty and chronological (train + oos concatenated)
    assert len(bt["equity_curve"]) > 0


def test_backtest_requires_enough_bars(trend_market_data):
    import pytest
    strategy = get_strategy("momentum")
    strategy.initialize({})
    with pytest.raises(ValueError):
        BacktestEngine().run_backtest(strategy, trend_market_data.bars[:10], symbol="TEST/USD", timeframe="1h")


def test_adversary_produces_structured_report(trend_market_data):
    strategy = get_strategy("momentum")
    strategy.initialize({})
    bt = BacktestEngine().run_backtest(strategy, trend_market_data.bars, symbol="TEST/USD", timeframe="1h")
    report = adversary_agent.stress_test_strategy({"strategy_id": "momentum"}, bt)
    assert report["report_id"].startswith("ADV-")
    assert 0.0 <= report["robustness_score"] <= 100.0
    assert report["verdict"] in ("PASS", "WATCH", "REJECT")


def test_edge_score_and_lifecycle(trend_market_data):
    strategy = get_strategy("momentum")
    strategy.initialize({})
    bt = BacktestEngine().run_backtest(strategy, trend_market_data.bars, symbol="TEST/USD", timeframe="1h")
    adv = adversary_agent.stress_test_strategy({"strategy_id": "momentum"}, bt)
    edge = evolution_engine.calculate_edge_score(bt, adv)
    assert 0.0 <= edge <= 100.0
    state, _reason = evolution_engine.determine_lifecycle_state(edge, adv["verdict"])
    assert state in ("ALIVE", "WATCH", "KILLED", "REJECTED")


def test_portfolio_manager_allocates_and_keeps_cash_buffer():
    strategies = [
        {"strategy_id": "A", "status": "ALIVE", "edge_score": 90.0},
        {"strategy_id": "B", "status": "ALIVE", "edge_score": 60.0},
        {"strategy_id": "C", "status": "REJECTED", "edge_score": 20.0},
    ]
    plan = portfolio_manager_agent.allocate_capital(strategies, 100000.0)
    allocs = {a["strategy_id"]: a for a in plan["allocations"]}
    assert allocs["A"]["allocation_amount"] > allocs["B"]["allocation_amount"]
    assert "C" not in allocs  # REJECTED strategies receive no capital entry
    assert plan["cash_reserve_pct"] >= 0.20


def test_portfolio_manager_no_alive_strategies_returns_all_cash():
    plan = portfolio_manager_agent.allocate_capital(
        [{"strategy_id": "X", "status": "REJECTED", "edge_score": 10.0}], 100000.0
    )
    assert plan["cash_reserve_pct"] == 1.0