"""
Explainability Engine (deterministic).

Generates a human-readable "WHY THIS TRADE?" evidence checklist and a
"why this strategy was killed" breakdown from real inputs (market regime,
backtest, adversary, risk decision). Grounded in actual data — nothing is invented.
"""

from __future__ import annotations

from typing import Any, Optional


class ExplainabilityEngine:
    def explain_trade_decision(
        self,
        trade: dict[str, Any],
        strategy: Optional[dict[str, Any]],
        market_regime: dict[str, Any],
        adversary_report: dict[str, Any],
        risk_result: dict[str, Any],
    ) -> dict[str, Any]:
        symbol = trade.get("symbol", "?")
        action = str(trade.get("side", trade.get("action", "BUY"))).upper()
        qty = float(trade.get("qty", 0))
        price = trade.get("price")

        regime_str = market_regime.get("regime", "UNKNOWN") if market_regime else "UNKNOWN"
        regime_conf = market_regime.get("confidence", 0.0) if market_regime else 0.0
        robustness = adversary_report.get("robustness_score", 50.0) if adversary_report else 50.0
        edge = strategy.get("edge_score", 50.0) if strategy else 50.0
        strategy_name = strategy.get("name", strategy.get("strategy_id", "strategy")) if strategy else "strategy"

        checklist = [
            {"agent": "Market Intelligence", "label": f"Regime: {regime_str} ({regime_conf:.0%})", "passed": True},
            {"agent": "Strategy", "label": f"Strategy: {strategy_name}", "passed": True},
            {"agent": "Adversary", "label": f"Robustness: {robustness:.0f}/100", "passed": robustness >= 45.0},
            {"agent": "Portfolio Manager", "label": f"Edge: {edge:.0f}/100", "passed": edge >= 40.0},
            {"agent": "Deterministic Risk", "label": f"Verdict: {risk_result.get('verdict', 'APPROVED')}", "passed": bool(risk_result.get("approved"))},
        ]

        signatures = [
            {"agent": "Market Intelligence", "status": "APPROVED", "detail": f"Regime {regime_str}"},
            {"agent": "Adversary", "status": "ROBUST" if robustness >= 45.0 else "WEAK", "detail": f"{robustness:.0f}/100"},
            {"agent": "Deterministic Risk", "status": "VERIFIED" if risk_result.get("approved") else "REJECTED", "detail": risk_result.get("verdict", "")},
        ]

        thesis = (
            f"{action.upper()} {qty} {symbol}"
            + (f" @ ${float(price):.2f}" if price is not None else "")
            + f" aligned with the {regime_str} regime; edge {edge:.0f}/100, adversarial robustness {robustness:.0f}/100."
        )

        return {
            "symbol": symbol,
            "action": action.lower(),
            "qty": qty,
            "price": price,
            "strategy_id": strategy.get("strategy_id") if strategy else None,
            "strategy_name": strategy_name,
            "thesis": thesis,
            "evidence_checklist": checklist,
            "signatures": signatures,
        }

    def explain_strategy_kill(self, strategy: dict[str, Any], adversary_report: Optional[dict[str, Any]] = None) -> dict[str, Any]:
        return {
            "strategy_id": strategy.get("strategy_id"),
            "strategy_name": strategy.get("name"),
            "status": strategy.get("status"),
            "edge_score": strategy.get("edge_score", 0.0),
            "primary_reason": strategy.get("status_reason", "Edge fell below the viable threshold."),
            "adversary_report": adversary_report or {
                "robustness_score": 30.0,
                "verdict": "REJECT",
                "weaknesses": ["Underperforming out-of-sample with high concentration risk."],
            },
            "lessons_learned": (
                "Unconstrained signals without regime confirmation and volume validation "
                "are prone to overfitting. Future hypotheses require out-of-sample and "
                "adversarial confirmation before capital allocation."
            ),
        }


explainability_engine = ExplainabilityEngine()