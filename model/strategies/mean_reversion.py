"""
Mean Reversion Strategy based on Alpaca's statistical arbitrage & pairs trading models.

Implements:
1. Rolling window mean & standard deviation.
2. Z-score deviation calculation ($Z = (Price - Mean) / StdDev$).
3. Oversold bounce buy triggers and overbought mean-reverting exit triggers.
"""

from __future__ import annotations

import math
from typing import Any, Optional

from pydantic import BaseModel, Field

from model.schemas.market_data import MarketData
from model.schemas.trade_signal import Action, NewsSignal, OrderType, TradeSignal
from model.strategies.base import BaseStrategy


class MeanReversionConfig(BaseModel):
    """Configuration schema for the Mean Reversion strategy."""

    lookback: int = Field(default=20, description="Number of bars used to compute the rolling mean/std")
    entry_z_score: float = Field(default=2.0, description="Absolute z-score threshold to trigger entry")
    exit_z_score: float = Field(default=0.5, description="Absolute z-score threshold to trigger exit")
    max_position: float = Field(default=500.0, description="Max position size (units of the asset)")
    stop_loss_pct: Optional[float] = Field(default=3.0, description="Stop loss percentage")
    position_size: float = Field(default=0.1, description="Position size as a fraction of buying power")


class MeanReversionStrategy(BaseStrategy):
    """
    Statistical mean-reversion strategy trading against short-term price extremes.
    """

    name = "mean_reversion"

    def initialize(self, config: Any) -> None:
        self.config = MeanReversionConfig(**config) if isinstance(config, dict) else config
        self.initialized = True

    def analyze(
        self,
        market_data: MarketData,
        portfolio: dict,
        news: Optional[list[NewsSignal]] = None,
    ) -> dict[str, Any]:
        bars = market_data.bars
        lookback = min(self.config.lookback, len(bars))
        if lookback < 5:
            return {}

        closes = [b.close for b in bars[-lookback:]]
        mean = sum(closes) / lookback
        variance = sum((x - mean) ** 2 for x in closes) / max(1, lookback - 1)
        std = math.sqrt(variance)

        current_price = closes[-1]
        z_score = (current_price - mean) / (std + 1e-8)

        return {
            "current_price": current_price,
            "mean": mean,
            "std": std,
            "z_score": z_score,
            "lookback": lookback,
        }

    def generate_signal(
        self,
        market_data: MarketData,
        portfolio: dict,
        news: Optional[list[NewsSignal]] = None,
    ) -> Optional[TradeSignal]:
        bars = market_data.bars
        if not bars or len(bars) < max(self.config.lookback, 5):
            return None

        analysis = self.analyze(market_data, portfolio, news)
        if not analysis:
            return None

        current_price = analysis["current_price"]
        mean = analysis["mean"]
        z_score = analysis["z_score"]

        # News veto: If breaking negative news, avoid buying dips prematurely
        if news:
            for n in news:
                if n.symbol.upper() in market_data.symbol.upper() and n.sentiment == "NEGATIVE" and z_score < 0:
                    return None

        is_crypto = "/" in market_data.symbol or "USD" in market_data.symbol.upper()
        target_usd = 500.0
        if is_crypto:
            order_qty = round(max(target_usd / max(current_price, 1e-6), 0.0001), 5)
        else:
            order_qty = max(1.0, round(target_usd / max(current_price, 1e-6), 2))

        # Buy condition: Price is statistically oversold (Z <= -entry_z_score)
        if z_score <= -self.config.entry_z_score:
            confidence = min(0.95, max(0.55, 0.5 + (abs(z_score) / 5.0)))
            stop_loss = round(current_price * (1.0 - (self.config.stop_loss_pct or 3.0) / 100.0), 2)
            take_profit = round(mean, 2)  # Target revert to rolling mean

            return TradeSignal(
                symbol=market_data.symbol,
                action=Action.BUY,
                quantity=order_qty,
                order_type=OrderType.MARKET,
                confidence=round(confidence, 2),
                strategy=self.name,
                reasoning=(
                    f"Statistical oversold extreme: Z-score={z_score:.2f} <= -{self.config.entry_z_score:.2f}. "
                    f"Targeting mean reversion to ${mean:.2f}."
                ),
                stop_loss=stop_loss,
                take_profit=take_profit,
            )

        # Sell / Exit condition: Price is overbought (Z >= entry_z_score) or reverted past exit target
        if z_score >= self.config.entry_z_score:
            confidence = min(0.90, max(0.55, 0.5 + (abs(z_score) / 5.0)))
            return TradeSignal(
                symbol=market_data.symbol,
                action=Action.SELL,
                quantity=order_qty,
                order_type=OrderType.MARKET,
                confidence=round(confidence, 2),
                strategy=self.name,
                reasoning=f"Statistical overbought extreme: Z-score={z_score:.2f} >= {self.config.entry_z_score:.2f}.",
                stop_loss=None,
                take_profit=None,
            )

        return None

