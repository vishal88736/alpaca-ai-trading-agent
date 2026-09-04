"""
Strategy registry.

The backend's /api/strategies endpoint reads from this registry so the
frontend can dynamically discover available strategies rather than having
them hardcoded in the UI.

`execution_mode` classifies each strategy honestly:
    live       — fully executable via Alpaca paper trading through the risk engine
    research   — kept and analyzable, but NOT auto-executed (e.g. market making
                 needs streaming quotes / bracket orders; funding & cross-exchange
                 arbitrage require an external venue/data source)
"""

from __future__ import annotations

from model.strategies.base import BaseStrategy
from model.strategies.cross_exchange_arbitrage import CrossExchangeArbitrageStrategy
from model.strategies.funding_arbitrage import FundingArbitrageStrategy
from model.strategies.market_making import MarketMakingStrategy
from model.strategies.mean_reversion import MeanReversionStrategy
from model.strategies.momentum import MomentumStrategy
from model.strategies.options_alpha_income import OptionsAlphaIncomeStrategy

STRATEGIES: dict[str, type[BaseStrategy]] = {
    "options_alpha_income": OptionsAlphaIncomeStrategy,
    "momentum": MomentumStrategy,
    "mean_reversion": MeanReversionStrategy,
    "market_making": MarketMakingStrategy,
    "funding_arbitrage": FundingArbitrageStrategy,
    "cross_exchange_arbitrage": CrossExchangeArbitrageStrategy,
}

STRATEGY_METADATA: dict[str, dict] = {
    "options_alpha_income": {
        "display_name": "Options Alpha & Portfolio Income",
        "description": "Systematic income engine (covered-call/cash-secured-put wheel, delta targeting, theta harvesting) executed as an equity approximation.",
        "requires_external_venue": False,
        "execution_mode": "live",
        "preferred_regime": "BULLISH",
        "entry_rules": ["Underlying owned for covered call, or cash available for CSP", "HV above minimum threshold"],
        "exit_rules": ["50% of premium captured", "2x premium stop loss"],
    },
    "momentum": {
        "display_name": "Momentum",
        "description": "Trend-following strategy trading in the direction of momentum (Supertrend + rate-of-change).",
        "requires_external_venue": False,
        "execution_mode": "live",
        "preferred_regime": "BULLISH",
        "entry_rules": ["Supertrend bullish", "Positive rate-of-change", "Optional trend alignment"],
        "exit_rules": ["Supertrend flips bearish", "Negative momentum with SMA crossover"],
    },
    "mean_reversion": {
        "display_name": "Mean Reversion",
        "description": "Trades against short-term price extremes back toward the rolling mean (z-score).",
        "requires_external_venue": False,
        "execution_mode": "live",
        "preferred_regime": "SIDEWAYS",
        "entry_rules": ["Z-score <= -entry threshold (oversold)"],
        "exit_rules": ["Z-score >= entry threshold (overbought)", "Price reverts to mean"],
    },
    "market_making": {
        "display_name": "Market Making",
        "description": "Captures bid/ask spread while managing inventory and risk. Requires streaming quotes + bracket/limit orders; kept as research.",
        "requires_external_venue": False,
        "execution_mode": "research",
        "preferred_regime": "SIDEWAYS",
        "entry_rules": ["Inventory skew below threshold -> quote buy"],
        "exit_rules": ["Inventory skew above threshold -> quote sell"],
    },
    "funding_arbitrage": {
        "display_name": "Funding-Rate Arbitrage",
        "description": "Market-neutral funding/basis carry. Requires an external perpetuals venue for funding-rate data + hedge execution.",
        "requires_external_venue": True,
        "execution_mode": "research",
        "preferred_regime": "ANY",
        "entry_rules": ["Funding spread clears hurdle rate"],
        "exit_rules": ["Funding spread converges or flips sign"],
    },
    "cross_exchange_arbitrage": {
        "display_name": "Cross-Exchange Arbitrage",
        "description": "Price-discrepancy spread capture across venues. Requires a second connected exchange to be executable.",
        "requires_external_venue": True,
        "execution_mode": "research",
        "preferred_regime": "ANY",
        "entry_rules": ["Cross-venue spread >= min spread %"],
        "exit_rules": ["Spread converges below hurdle"],
    },
}


def get_strategy(key: str) -> BaseStrategy:
    """Instantiate a strategy by its registry key."""
    if key not in STRATEGIES:
        raise KeyError(f"Unknown strategy: {key}")
    return STRATEGIES[key]()


def is_live_executable(key: str) -> bool:
    return STRATEGY_METADATA.get(key, {}).get("execution_mode") == "live"