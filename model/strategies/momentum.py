"""
Momentum / Trend-Following Strategy based on Alpaca's Supertrend and Momentum algorithms.

Implements:
1. Average True Range (ATR) & Supertrend Indicator (from alpacahq supertrend_indicator.ipynb).
2. Moving Average crossover and Rate of Change (ROC) momentum calculation.
3. Volatility filter and dynamic stop-loss / take-profit levels.
"""

from __future__ import annotations

import math
from typing import Any, Optional

from pydantic import BaseModel, Field

from model.schemas.market_data import MarketData
from model.schemas.trade_signal import Action, NewsSignal, OrderType, TradeSignal
from model.strategies.base import BaseStrategy


class MomentumConfig(BaseModel):
    """Configuration schema for the Momentum strategy."""

    lookback_period: int = Field(default=20, description="Number of bars used to compute momentum")
    momentum_threshold: float = Field(default=0.015, description="Minimum momentum (fraction) to trigger a signal")
    supertrend_period: int = Field(default=7, description="ATR period for Supertrend indicator")
    supertrend_multiplier: float = Field(default=3.0, description="ATR multiplier for Supertrend bands")
    trend_filter: bool = Field(default=True, description="Whether to require alignment with a longer-term trend")
    volatility_filter: bool = Field(default=True, description="Whether to filter signals during extreme volatility")
    position_size: float = Field(default=0.1, description="Position size as a fraction of buying power")
    stop_loss_pct: Optional[float] = Field(default=2.0, description="Stop loss percentage")
    take_profit_pct: Optional[float] = Field(default=4.0, description="Take profit percentage")


class MomentumStrategy(BaseStrategy):
    """
    Trend-following momentum strategy combining Supertrend and Rate-of-Change.
    """

    name = "momentum"

    def initialize(self, config: Any) -> None:
        self.config = MomentumConfig(**config) if isinstance(config, dict) else config
        self.initialized = True

    def _compute_supertrend(self, bars: list) -> tuple[float, int]:
        """
        Computes the Supertrend indicator for the series of bars.
        Returns (current_supertrend_val, trend_direction) where 1 is Bullish and -1 is Bearish.
        """
        period = self.config.supertrend_period
        multiplier = self.config.supertrend_multiplier
        if len(bars) < period + 2:
            return bars[-1].close, 1

        tr_list = []
        for i in range(1, len(bars)):
            h = bars[i].high
            l = bars[i].low
            prev_c = bars[i - 1].close
            tr = max(h - l, abs(h - prev_c), abs(l - prev_c))
            tr_list.append(tr)

        # Rolling ATR
        atr = sum(tr_list[-period:]) / period

        curr = bars[-1]
        hl2 = (curr.high + curr.low) / 2.0
        upper_band = hl2 + (multiplier * atr)
        lower_band = hl2 - (multiplier * atr)

        close = curr.close
        if close > upper_band:
            trend = 1
            st_val = lower_band
        elif close < lower_band:
            trend = -1
            st_val = upper_band
        else:
            trend = 1 if close >= hl2 else -1
            st_val = lower_band if trend == 1 else upper_band

        return st_val, trend

    def analyze(
        self,
        market_data: MarketData,
        portfolio: dict,
        news: Optional[list[NewsSignal]] = None,
    ) -> dict[str, Any]:
        bars = market_data.bars
        lookback = min(self.config.lookback_period, len(bars))
        if lookback < 5:
            return {}

        closes = [b.close for b in bars]
        current_price = closes[-1]
        past_price = closes[-lookback]

        # Rate of Change (Momentum)
        roc = (current_price - past_price) / past_price if past_price else 0.0

        # Moving averages
        fast_sma = sum(closes[-min(9, len(closes)):]) / min(9, len(closes))
        slow_sma = sum(closes[-min(21, len(closes)):]) / min(21, len(closes))

        # Supertrend
        st_val, st_trend = self._compute_supertrend(bars)

        # Volatility check (normalized ATR)
        highs = [b.high for b in bars[-lookback:]]
        lows = [b.low for b in bars[-lookback:]]
        avg_range = sum(h - l for h, l in zip(highs, lows)) / lookback
        normalized_volatility = (avg_range / current_price) if current_price else 0.0

        return {
            "current_price": current_price,
            "roc": roc,
            "fast_sma": fast_sma,
            "slow_sma": slow_sma,
            "supertrend_val": st_val,
            "supertrend_trend": st_trend,
            "volatility": normalized_volatility,
        }

    def generate_signal(
        self,
        market_data: MarketData,
        portfolio: dict,
        news: Optional[list[NewsSignal]] = None,
    ) -> Optional[TradeSignal]:
        bars = market_data.bars
        if not bars or len(bars) < max(self.config.supertrend_period + 2, 5):
            return None

        analysis = self.analyze(market_data, portfolio, news)
        if not analysis:
            return None

        current_price = analysis["current_price"]
        roc = analysis["roc"]
        st_trend = analysis["supertrend_trend"]
        fast_sma = analysis["fast_sma"]
        slow_sma = analysis["slow_sma"]

        # Optional Volatility filter
        if self.config.volatility_filter and analysis["volatility"] > 0.08:
            return None

        # News alignment modifier
        news_boost = 0.0
        if news:
            for n in news:
                if n.symbol.upper() in market_data.symbol.upper():
                    if n.sentiment == "POSITIVE":
                        news_boost += 0.1
                    elif n.sentiment == "NEGATIVE":
                        news_boost -= 0.15

        # Check for Bullish Entry (Supertrend Bullish + Positive ROC)
        trend_aligned = (fast_sma >= slow_sma) if self.config.trend_filter else True
        if st_trend == 1 and roc >= self.config.momentum_threshold and trend_aligned:
            confidence = min(0.95, max(0.5, 0.6 + (roc * 5) + news_boost))
            stop_loss = round(current_price * (1.0 - (self.config.stop_loss_pct or 2.0) / 100.0), 2)
            take_profit = round(current_price * (1.0 + (self.config.take_profit_pct or 4.0) / 100.0), 2)

            return TradeSignal(
                symbol=market_data.symbol,
                action=Action.BUY,
                quantity=1.0,
                order_type=OrderType.MARKET,
                confidence=round(confidence, 2),
                strategy=self.name,
                reasoning=(
                    f"Bullish momentum breakout: ROC={roc:.2%}, Supertrend={analysis['supertrend_val']:.2f} "
                    f"aligned with trend ({'SMA9 > SMA21' if trend_aligned else 'Trend Active'})."
                ),
                stop_loss=stop_loss,
                take_profit=take_profit,
            )

        # Check for Bearish Exit / Reversal
        if st_trend == -1 or (roc < -self.config.momentum_threshold and fast_sma < slow_sma):
            confidence = min(0.90, max(0.5, 0.6 + (abs(roc) * 5)))
            return TradeSignal(
                symbol=market_data.symbol,
                action=Action.SELL,
                quantity=1.0,
                order_type=OrderType.MARKET,
                confidence=round(confidence, 2),
                strategy=self.name,
                reasoning=f"Bearish trend reversal: Supertrend flipped bearish, ROC={roc:.2%}.",
                stop_loss=None,
                take_profit=None,
            )

        return None

