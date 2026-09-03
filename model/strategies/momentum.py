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
    """Configuration schema for the upgraded Momentum strategy."""

    lookback_period: int = Field(default=20, description="Number of bars used to compute momentum")
    momentum_threshold: float = Field(default=0.015, description="Minimum momentum (fraction) to trigger a signal")
    supertrend_period: int = Field(default=7, description="ATR period for Supertrend indicator")
    supertrend_multiplier: float = Field(default=3.0, description="ATR multiplier for Supertrend bands")
    trend_filter: bool = Field(default=True, description="Whether to require alignment with a longer-term trend")
    volatility_filter: bool = Field(default=True, description="Whether to filter signals during extreme volatility")
    
    # ATR-Based Risk Management Settings
    atr_period: int = Field(default=14, description="Period for base ATR calculation")
    risk_per_trade_usd: float = Field(default=25.0, description="Target dollar risk per trade")
    atr_stop_multiplier: float = Field(default=2.0, description="Multiplier for ATR-based stop loss")
    risk_reward_ratio: float = Field(default=2.0, description="Target Risk/Reward ratio for take profit")


class MomentumStrategy(BaseStrategy):
    """
    Trend-following momentum strategy combining Supertrend and Rate-of-Change,
    upgraded with ATR-based dynamic stop-losses and position sizing.
    """

    name = "momentum"

    def initialize(self, config: Any) -> None:
        self.config = MomentumConfig(**config) if isinstance(config, dict) else config
        self.initialized = True

    def _compute_atr(self, bars: list, period: int) -> float:
        """Computes the Average True Range (ATR)."""
        if len(bars) < 2:
            return 0.0
        tr_list = []
        for i in range(1, len(bars)):
            h = bars[i].high
            l = bars[i].low
            prev_c = bars[i - 1].close
            tr = max(h - l, abs(h - prev_c), abs(l - prev_c))
            tr_list.append(tr)
        return sum(tr_list[-period:]) / min(period, len(tr_list))

    def _compute_supertrend(self, bars: list) -> tuple[float, int]:
        """
        Computes the Supertrend indicator for the series of bars.
        Returns (current_supertrend_val, trend_direction) where 1 is Bullish and -1 is Bearish.
        """
        period = self.config.supertrend_period
        multiplier = self.config.supertrend_multiplier
        if len(bars) < period + 2:
            return bars[-1].close, 1

        atr = self._compute_atr(bars, period)

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

        # Baseline ATR for sizing and stops
        atr = self._compute_atr(bars, self.config.atr_period)
        normalized_volatility = (atr / current_price) if current_price else 0.0

        return {
            "current_price": current_price,
            "roc": roc,
            "fast_sma": fast_sma,
            "slow_sma": slow_sma,
            "supertrend_val": st_val,
            "supertrend_trend": st_trend,
            "atr": atr,
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
        atr = analysis["atr"]

        # Optional Volatility filter (abort if extremely chaotic)
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
            
            # --- DYNAMIC ATR RISK MANAGEMENT ---
            stop_loss_distance = atr * self.config.atr_stop_multiplier
            if stop_loss_distance <= 0:
                return None
                
            stop_loss = round(current_price - stop_loss_distance, 4)
            take_profit = round(current_price + (stop_loss_distance * self.config.risk_reward_ratio), 4)
            
            # Volatility-adjusted position sizing: (Risk Amount) / (Risk per Share)
            is_crypto = "/" in market_data.symbol or "USD" in market_data.symbol.upper()
            qty_unrounded = self.config.risk_per_trade_usd / stop_loss_distance
            order_qty = round(qty_unrounded, 5) if is_crypto else max(1.0, round(qty_unrounded, 2))
            
            # Use Limit Order to avoid unbounded slippage, giving a 0.25% buffer
            limit_price = round(current_price * 1.0025, 4)

            return TradeSignal(
                symbol=market_data.symbol,
                action=Action.BUY,
                quantity=order_qty,
                order_type=OrderType.LIMIT,
                limit_price=limit_price,
                confidence=round(confidence, 2),
                strategy=self.name,
                reasoning=(
                    f"Bullish breakout: ROC={roc:.2%}. ATR sizing: {order_qty} units to risk ${self.config.risk_per_trade_usd}. "
                    f"Stop: ${stop_loss}, Target: ${take_profit}."
                ),
                stop_loss=stop_loss,
                take_profit=take_profit,
            )

        # Check for Bearish Exit / Reversal
        if st_trend == -1 or (roc < -self.config.momentum_threshold and fast_sma < slow_sma):
            confidence = min(0.90, max(0.5, 0.6 + (abs(roc) * 5)))
            
            # For exits, we typically just want out immediately, but we can use a limit to protect from flashes.
            limit_price = round(current_price * 0.995, 4)
            
            # Calculate a dummy quantity if we were just emitting a sell signal to close an unknown position
            # (In a real system, the orchestrator should map this to closing the open position size)
            is_crypto = "/" in market_data.symbol or "USD" in market_data.symbol.upper()
            order_qty = 1.0 if not is_crypto else 0.01 

            return TradeSignal(
                symbol=market_data.symbol,
                action=Action.SELL,
                quantity=order_qty,
                order_type=OrderType.LIMIT,
                limit_price=limit_price,
                confidence=round(confidence, 2),
                strategy=self.name,
                reasoning=f"Bearish trend reversal: Supertrend flipped bearish, ROC={roc:.2%}. Exiting via limit.",
                stop_loss=None,
                take_profit=None,
            )

        return None

