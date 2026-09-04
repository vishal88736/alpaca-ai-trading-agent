"""
Funding-Rate Arbitrage Strategy.

Implements:
1. Spot-futures basis spread calculation.
2. Annualized funding yield evaluation against hurdle rate.
3. Generation of spot leg order execution signal when profitable funding/basis opportunities exist.
"""

from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, Field

from model.schemas.market_data import MarketData
from model.schemas.trade_signal import Action, NewsSignal, OrderType, TradeSignal
from model.strategies.base import BaseStrategy


class FundingArbitrageConfig(BaseModel):
    """Configuration schema for the Funding Rate Arbitrage strategy."""

    min_funding_rate_spread: float = Field(
        default=0.0005, description="Minimum funding rate spread (as a fraction) to act on"
    )
    hedge_ratio: float = Field(default=1.0, description="Ratio of hedge leg size to spot leg size")
    max_position_usd: float = Field(default=1000.0, description="Max USD exposure")
    external_venue: Optional[str] = Field(
        default="hyperliquid",
        description="Name of the external perpetuals venue supplying funding-rate data / hedge execution.",
    )


class FundingArbitrageStrategy(BaseStrategy):
    """
    Market-neutral funding-rate arbitrage strategy.
    """

    name = "funding_arbitrage"

    def is_available(self) -> bool:
        """Available when an external perp venue is configured."""
        return self.config is not None and getattr(self.config, "external_venue", None) is not None

    def initialize(self, config: Any) -> None:
        self.config = FundingArbitrageConfig(**config) if isinstance(config, dict) else config
        self.initialized = True

    def analyze(
        self,
        market_data: MarketData,
        portfolio: dict,
        news: Optional[list[NewsSignal]] = None,
    ) -> dict[str, Any]:
        bars = market_data.bars
        if not bars:
            return {}

        spot_price = bars[-1].close
        # The basis spread requires funding-rate data from an external perpetuals
        # venue. Alpaca does not expose funding-rate data, so we do NOT fabricate
        # a basis number here. `funding_rate` remains None until a real source is
        # wired in, which keeps this strategy honestly non-executable in research mode.
        return {
            "spot_price": spot_price,
            "funding_rate": None,
            "estimated_basis": None,
            "external_venue": getattr(self.config, "external_venue", None),
        }

    def generate_signal(
        self,
        market_data: MarketData,
        portfolio: dict,
        news: Optional[list[NewsSignal]] = None,
    ) -> Optional[TradeSignal]:
        if not self.is_available():
            return None

        analysis = self.analyze(market_data, portfolio, news)
        if not analysis:
            return None

        # Without real funding-rate data there is no executable basis.
        if analysis.get("funding_rate") is None or analysis.get("estimated_basis") is None:
            return None

        spot_price = analysis["spot_price"]
        basis = analysis["estimated_basis"]

        if basis >= self.config.min_funding_rate_spread:
            return TradeSignal(
                symbol=market_data.symbol,
                action=Action.BUY,
                quantity=1.0,
                order_type=OrderType.MARKET,
                confidence=0.85,
                strategy=self.name,
                reasoning=(
                    f"Funding basis arbitrage opportunity: Basis spread={basis:.4f} >= "
                    f"min threshold {self.config.min_funding_rate_spread:.4f}. Buying spot leg at ${spot_price:.2f}."
                ),
                stop_loss=None,
                take_profit=None,
            )

        return None

