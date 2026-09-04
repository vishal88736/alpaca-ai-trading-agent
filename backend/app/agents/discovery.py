"""
Discovery Agent (deterministic).

Proposes research strategy hypotheses derived from the registered/builtin
strategies. It does NOT claim profitability — a hypothesis only becomes an
"ALIVE" strategy after it passes backtest + adversary + edge scoring.

No LLM, no random selection. Hypothesis templates are fixed and auditable.
"""

from __future__ import annotations

import uuid
from typing import Any

from model.strategies.registry import STRATEGY_METADATA

_HYPOTHESIS_TEMPLATES = {
    "momentum": "Trend-following signals persist when price, moving averages, and the {regime} regime agree.",
    "mean_reversion": "Short-term price extremes revert toward the rolling mean in {regime} conditions.",
    "market_making": "Bid/ask spread capture with inventory-skew management is viable when volatility is bounded.",
    "options_alpha_income": "Systematic volatility-premium harvesting (wheel-style income) has positive expectancy when implied volatility outpaces realized volatility.",
    "funding_arbitrage": "Market-neutral funding/basis carry is profitable when funding spread clears the hurdle rate (requires external venue).",
    "cross_exchange_arbitrage": "Venue price dislocations are exploitable when spread clears the hurdle rate after slippage (requires external venue).",
}


class DiscoveryAgent:
    def generate_strategy(self, strategy_key: str, regime: str = "SIDEWAYS") -> dict[str, Any]:
        hypothesis = _HYPOTHESIS_TEMPLATES.get(
            strategy_key, "Quantitative hypothesis derived from a registered strategy."
        ).format(regime=regime)

        meta = STRATEGY_METADATA.get(strategy_key, {})
        entry_rules = meta.get("entry_rules", [])
        exit_rules = meta.get("exit_rules", [])
        preferred_regime = meta.get("preferred_regime", regime)

        return {
            "strategy_id": f"DISC-{strategy_key}-{uuid.uuid4().hex[:6]}",
            "name": f"{meta.get('display_name', strategy_key)} (research)",
            "hypothesis": hypothesis,
            "entry_rules": entry_rules,
            "exit_rules": exit_rules,
            "stop_loss_rules": ["Fixed stop-loss percentage derived from strategy config"],
            "preferred_regime": preferred_regime,
            "edge_score": 50.0,
            "status": "WATCH",
            "status_reason": "New hypothesis; pending backtest and adversarial validation.",
            "allocation_pct": 0.0,
            "parent_strategy_id": strategy_key,
            "source": "discovery",
        }


discovery_agent = DiscoveryAgent()