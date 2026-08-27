"""
Strategy registry.

The backend's /api/strategies endpoint reads from this registry so the
frontend can dynamically discover available strategies rather than having
them hardcoded in the UI.
"""

from __future__ import annotations

from model.strategies.base import BaseStrategy
from model.strategies.cross_exchange_arbitrage import CrossExchangeArbitrageStrategy
from model.strategies.funding_arbitrage import FundingArbitrageStrategy
from model.strategies.market_making import MarketMakingStrategy
from model.strategies.mean_reversion import MeanReversionStrategy
from model.strategies.momentum import MomentumStrategy

STRATEGIES: dict[str, type[BaseStrategy]] = {
    "funding_arbitrage": FundingArbitrageStrategy,
    "cross_exchange_arbitrage": CrossExchangeArbitrageStrategy,
    "market_making": MarketMakingStrategy,
    "momentum": MomentumStrategy,
    "mean_reversion": MeanReversionStrategy,
}

STRATEGY_METADATA: dict[str, dict] = {
    "funding_arbitrage": {
        "display_name": "Funding-Rate Arbitrage",
        "description": "Market-neutral strategy capturing funding/basis opportunities.",
        "requires_external_venue": True,
    },
    "cross_exchange_arbitrage": {
        "display_name": "Cross-Exchange Arbitrage",
        "description": "Looks for price discrepancies across supported venues/data sources.",
        "requires_external_venue": True,
    },
    "market_making": {
        "display_name": "Market Making",
        "description": "Captures bid/ask spread while managing inventory and risk.",
        "requires_external_venue": False,
    },
    "momentum": {
        "display_name": "Momentum",
        "description": "Trend-following strategy trading in the direction of momentum.",
        "requires_external_venue": False,
    },
    "mean_reversion": {
        "display_name": "Mean Reversion",
        "description": "Trades against short-term price extremes back toward the mean.",
        "requires_external_venue": False,
    },
}


def get_strategy(key: str) -> BaseStrategy:
    """Instantiate a strategy by its registry key."""
    if key not in STRATEGIES:
        raise KeyError(f"Unknown strategy: {key}")
    return STRATEGIES[key]()
