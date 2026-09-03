"""
Market Making Strategy with inventory risk management.

Implements:
1. Mid-price and bid-ask spread tracking.
2. Inventory skew adjustment (Avellaneda-Stoikov micro-structure model).
3. Dynamic quote sizing within risk limits.
"""

from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, Field

from model.schemas.market_data import MarketData
from model.schemas.trade_signal import Action, NewsSignal, OrderType, TradeSignal
from model.strategies.base import BaseStrategy


class MarketMakingConfig(BaseModel):
    """Configuration schema for the Market Making strategy."""

    max_inventory: float = Field(default=100.0, description="Max net inventory (units of the asset)")
    spread_bps: float = Field(default=15.0, description="Target quoted spread, in basis points")
    order_size: float = Field(default=1.0, description="Size of each quote, in units of the asset")
    max_position: float = Field(default=500.0, description="Max absolute position size (units)")
    risk_limit_usd: float = Field(default=1000.0, description="Max USD exposure before pulling quotes")


class MarketMakingStrategy(BaseStrategy):
    """
    Bid/ask spread capture with inventory skew management.
    """

    name = "market_making"

    def initialize(self, config: Any) -> None:
        self.config = MarketMakingConfig(**config) if isinstance(config, dict) else config
        self.initialized = True

    def analyze(
        self,
        market_data: MarketData,
        portfolio: dict,
        news: Optional[list[NewsSignal]] = None,
    ) -> dict[str, Any]:
        # Determine current mid price
        quote = market_data.latest_quote
        bid = getattr(quote, "bid_price", getattr(quote, "bid", None)) if quote else None
        ask = getattr(quote, "ask_price", getattr(quote, "ask", None)) if quote else None

        if bid is not None and ask is not None:
            mid = (bid + ask) / 2.0
            market_spread = ask - bid
        elif market_data.bars:
            mid = market_data.bars[-1].close
            market_spread = mid * (self.config.spread_bps / 10000.0)
        else:
            return {}

        # Current inventory from portfolio
        positions = portfolio.get("positions", [])
        current_qty = 0.0
        for p in positions:
            if p.get("symbol") == market_data.symbol:
                current_qty = float(p.get("quantity", 0.0))
                break

        # Inventory skew factor (-1.0 to +1.0)
        inv_ratio = current_qty / (self.config.max_inventory + 1e-8)
        half_spread = mid * (self.config.spread_bps / 20000.0)

        # Adjusted reservation price
        reservation_price = mid - (inv_ratio * half_spread)
        target_bid = round(reservation_price - half_spread, 2)
        target_ask = round(reservation_price + half_spread, 2)

        return {
            "mid": mid,
            "market_spread": market_spread,
            "current_inventory": current_qty,
            "inv_ratio": inv_ratio,
            "target_bid": target_bid,
            "target_ask": target_ask,
        }

    def generate_signal(
        self,
        market_data: MarketData,
        portfolio: dict,
        news: Optional[list[NewsSignal]] = None,
    ) -> Optional[TradeSignal]:
        analysis = self.analyze(market_data, portfolio, news)
        if not analysis:
            return None

        current_inv = analysis["current_inventory"]
        mid = analysis["mid"]
        inv_ratio = analysis["inv_ratio"]

        # Risk check: total USD position
        if abs(current_inv * mid) >= self.config.risk_limit_usd:
            # Over risk limit, skew aggressively to reduce inventory
            if current_inv > 0:
                return TradeSignal(
                    symbol=market_data.symbol,
                    action=Action.SELL,
                    quantity=self.config.order_size,
                    order_type=OrderType.MARKET,
                    confidence=0.90,
                    strategy=self.name,
                    reasoning=f"Risk limit reached: reducing long inventory ({current_inv:.1f} units).",
                )
            return None

        # If short or neutral inventory, quote buy
        if inv_ratio < 0.5:
            return TradeSignal(
                symbol=market_data.symbol,
                action=Action.BUY,
                quantity=self.config.order_size,
                order_type=OrderType.MARKET,
                confidence=0.75,
                strategy=self.name,
                reasoning=(
                    f"Quoting spread: Mid=${mid:.2f}, Target Bid=${analysis['target_bid']:.2f}, "
                    f"Inventory={current_inv:.1f}/{self.config.max_inventory:.1f} units."
                ),
                take_profit=analysis["target_ask"],
                stop_loss=round(analysis["target_bid"] * 0.98, 2),
            )
        elif inv_ratio >= 0.5:
            # High inventory, quote sell / unload
            return TradeSignal(
                symbol=market_data.symbol,
                action=Action.SELL,
                quantity=self.config.order_size,
                order_type=OrderType.MARKET,
                confidence=0.80,
                strategy=self.name,
                reasoning=(
                    f"Skewed quoting: Rebalancing inventory at Target Ask=${analysis['target_ask']:.2f}. "
                    f"Inventory={current_inv:.1f} units."
                ),
                take_profit=None,
                stop_loss=None,
            )

        return None

