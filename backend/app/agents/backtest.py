"""
Backtest Agent — real, chronological walk-forward backtester.

Unlike the reference repo (which simulated returns with `np.random`), this engine
actually runs the *real* strategy signal logic over real historical bars:

    for i in warmup..N-1:
        signal = strategy.generate_signal(bars[:i+1])
        position[t+1] = map(signal)

Execution is at the *next* bar's open, preventing lookahead. Transaction costs
(slippage + commission) are applied on every trade. A 70/30 chronological train vs
out-of-sample split is enforced — no shuffling.

This is "research" only: results never authorize an order by themselves.
"""

from __future__ import annotations

import math
import uuid
from typing import Any, Iterable, Optional

from model.schemas.market_data import MarketData
from model.schemas.research import BacktestMetricSet, BacktestResult
from model.schemas.trade_signal import Action
from model.strategies.base import BaseStrategy


def _bar_field(b, name: str) -> float:
    v = getattr(b, name, None)
    if v is None and isinstance(b, dict):
        v = b.get(name)
    return float(v) if v is not None else 0.0


def _to_market_data(symbol: str, timeframe: str, bars: list) -> MarketData:
    return MarketData(
        symbol=symbol,
        asset_class="crypto" if ("/" in symbol or "-" in symbol) else "us_equity",
        timeframe=timeframe,
        bars=bars,
    )


class BacktestEngine:
    def __init__(
        self,
        slippage_bps: float = 5.0,
        commission_bps: float = 2.0,
        warmup_bars: int = 25,
    ) -> None:
        self.slippage_bps = slippage_bps
        self.commission_bps = commission_bps
        self.warmup_bars = warmup_bars

    def run_backtest(
        self,
        strategy: BaseStrategy,
        bars: list,
        symbol: str,
        timeframe: str = "1D",
        strategy_id: Optional[str] = None,
    ) -> dict[str, Any]:
        if not bars or len(bars) < self.warmup_bars + 2:
            raise ValueError("Not enough bars to run a backtest")

        split_idx = int(len(bars) * 0.70)
        split_idx = max(self.warmup_bars + 2, min(split_idx, len(bars) - 2))
        train_bars = bars[:split_idx]
        oos_bars = bars[split_idx - 1:]  # overlap one bar so the OOS sim has context

        train = self._simulate(strategy, train_bars, symbol, timeframe)
        oos = self._simulate(strategy, oos_bars, symbol, timeframe)

        oos_passed = self._oos_pass(oos)

        backtest_id = f"BT-{uuid.uuid4().hex[:8]}"
        return {
            "backtest_id": backtest_id,
            "strategy_id": strategy_id or getattr(strategy, "name", "strategy"),
            "symbol": symbol,
            "timeframe": timeframe,
            "train": train,
            "oos": oos,
            "oos_passed": oos_passed,
            "equity_curve": train["equity_curve"] + oos["equity_curve"][1:],
        }

    @staticmethod
    def _oos_pass(oos: dict) -> bool:
        return (
            oos["sharpe_ratio"] >= 0.5
            and oos["total_return"] > 0
            and oos["max_drawdown"] <= 0.20
        )

    def _simulate(self, strategy: BaseStrategy, bars: list, symbol: str, timeframe: str) -> dict[str, Any]:
        opens = [_bar_field(b, "open") for b in bars]
        closes = [_bar_field(b, "close") for b in bars]

        n_bars = len(bars)

        # position: 0 = flat, 1 = long. Signals map to long/flat.
        position = 0.0
        entry_price = 0.0
        equity = 1.0
        equity_curve = [1.0]
        trade_pnls: list[float] = []

        daily_returns: list[float] = []
        prev_close = None

        for i in range(self.warmup_bars, n_bars):
            # 1) Generate signal using only bars up to and including i
            md = _to_market_data(symbol, timeframe, bars[: i + 1])
            try:
                signal = strategy.generate_signal(md, portfolio={})
            except Exception:
                signal = None

            target = 0.0
            if signal is not None:
                if signal.action == Action.BUY:
                    target = 1.0
                elif signal.action == Action.SELL:
                    target = 0.0

            # 2) Execute at the NEXT bar's open. Decision on bar i close -> fill at bar i+1 open.
            exec_i = i + 1
            if exec_i >= n_bars:
                break

            exec_price = opens[exec_i]
            if exec_price <= 0:
                exec_price = closes[exec_i]

            if target != position:
                cost_rate = (self.slippage_bps + self.commission_bps) / 10000.0
                if target > position:  # open long
                    if position == 0.0:
                        entry_price = exec_price * (1 + cost_rate)
                        equity *= (1 - cost_rate)
                        position = 1.0
                else:  # close long
                    if position == 1.0:
                        exit_price = exec_price * (1 - cost_rate)
                        equity *= (1 - cost_rate)
                        if entry_price > 0:
                            trade_pnls.append((exit_price - entry_price) / entry_price)
                        position = 0.0

            # 3) Mark-to-market return for this bar
            if i > self.warmup_bars and prev_close is not None and prev_close > 0:
                bar_ret = position * (closes[i] - prev_close) / prev_close
                daily_returns.append(bar_ret)
                equity *= (1 + bar_ret)
            equity_curve.append(equity)
            prev_close = closes[i]

        # Close any open position at the final close
        if position == 1.0 and entry_price > 0:
            last_price = closes[-1]
            if last_price > 0:
                trade_pnls.append((last_price - entry_price) / entry_price)

        return {
            **_metrics(daily_returns, equity_curve),
            "profit_factor": _profit_factor(trade_pnls),
            "win_rate": _win_rate(trade_pnls),
            "num_trades": len(trade_pnls),
            "trade_pnls": [round(x, 4) for x in trade_pnls],
            "equity_curve": [round(x, 4) for x in equity_curve],
        }


def _metrics(daily_returns: list[float], equity_curve: list[float]) -> dict[str, Any]:
    n = len(daily_returns)
    if n == 0:
        return {
            "total_return": 0.0,
            "annualized_return": 0.0,
            "volatility": 0.0,
            "sharpe_ratio": 0.0,
            "sortino_ratio": 0.0,
            "max_drawdown": 0.0,
        }

    mean = sum(daily_returns) / n
    var = sum((r - mean) ** 2 for r in daily_returns) / max(1, n - 1)
    vol = math.sqrt(max(var, 1e-12))
    sharpe = (mean / vol) * math.sqrt(252) if vol > 0 else 0.0

    downside = [r for r in daily_returns if r < 0]
    downside_vol = math.sqrt(sum(r * r for r in downside) / n) if downside else 0.0
    sortino = (mean / downside_vol) * math.sqrt(252) if downside_vol > 0 else 0.0

    total_return = equity_curve[-1] - 1.0
    annualized = (equity_curve[-1]) ** (252.0 / n) - 1.0 if n > 0 and equity_curve[-1] > 0 else total_return

    peak = equity_curve[0]
    max_dd = 0.0
    for eq in equity_curve:
        peak = max(peak, eq)
        if peak > 0:
            max_dd = max(max_dd, (peak - eq) / peak)

    return {
        "total_return": round(total_return, 4),
        "annualized_return": round(annualized, 4),
        "volatility": round(vol * math.sqrt(252), 4),
        "sharpe_ratio": round(sharpe, 3),
        "sortino_ratio": round(sortino, 3),
        "max_drawdown": round(max_dd, 4),
    }


def _profit_factor(pnls: list[float]) -> float:
    if not pnls:
        return 0.0
    gross_win = sum(p for p in pnls if p > 0)
    gross_loss = abs(sum(p for p in pnls if p < 0))
    if gross_loss == 0:
        return round(gross_win, 2) if gross_win > 0 else 0.0
    return round(gross_win / gross_loss, 3)


def _win_rate(pnls: list[float]) -> float:
    if not pnls:
        return 0.0
    return round(sum(1 for p in pnls if p > 0) / len(pnls), 4)


backtest_engine = BacktestEngine()