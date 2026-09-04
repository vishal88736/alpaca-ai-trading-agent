"""
Strategy Evolution / Edge Scoring (deterministic).

Combines backtest OOS metrics with adversarial robustness into a single
EDGE SCORE (0-100), then maps it to a lifecycle state.

Formula (auditable, no LLM):
    edge = 0.35*sharpe_score + 0.30*robustness + 0.20*pf_score + 0.15*dd_score
"""

from __future__ import annotations

from typing import Any


class StrategyEvolutionEngine:
    def calculate_edge_score(self, backtest: dict[str, Any], adversary_report: dict[str, Any]) -> float:
        oos = backtest.get("oos", {})
        oos_sharpe = max(0.0, float(oos.get("sharpe_ratio", 0.0)))
        robustness = float(adversary_report.get("robustness_score", 50.0))
        profit_factor = float(oos.get("profit_factor", 1.0))
        max_dd = float(oos.get("max_drawdown", 0.10))

        sharpe_score = min(100.0, oos_sharpe / 2.5 * 100.0)
        pf_score = min(100.0, profit_factor / 2.2 * 100.0)
        dd_score = max(0.0, 100.0 - (max_dd / 0.25) * 100.0)

        edge = (
            0.35 * sharpe_score
            + 0.30 * robustness
            + 0.20 * pf_score
            + 0.15 * dd_score
        )
        return round(max(0.0, min(100.0, edge)), 1)

    def determine_lifecycle_state(self, edge_score: float, adversary_verdict: str) -> tuple[str, str]:
        if adversary_verdict == "REJECT":
            return "REJECTED", "Adversary identified structural weaknesses; edge not robust."
        if edge_score >= 70.0 and adversary_verdict == "PASS":
            return "ALIVE", "Strong out-of-sample edge and high adversarial robustness."
        if edge_score >= 45.0:
            return "WATCH", "Moderate edge; on watch for regime confirmation."
        return "KILLED", "Edge below the minimum viable threshold."


evolution_engine = StrategyEvolutionEngine()