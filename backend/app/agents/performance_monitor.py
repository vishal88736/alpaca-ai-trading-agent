"""
Performance Monitoring Agent (deterministic).

Tracks live trade P&L per strategy and detects edge deterioration. When a
strategy strings together consecutive losses, its edge score is reduced and
allocation cut; if it falls below the viability floor it is killed.

Pure function over trade history — no global state, no LLM.
"""

from __future__ import annotations

from typing import Any


class PerformanceMonitoringAgent:
    def __init__(self, losing_streak_threshold: int = 3, floor_edge: float = 40.0, decay: float = 15.0) -> None:
        self.losing_streak_threshold = losing_streak_threshold
        self.floor_edge = floor_edge
        self.decay = decay

    def monitor_strategy_performance(self, strategy: dict[str, Any], live_trades: list[dict[str, Any]]) -> dict[str, Any]:
        strat_id = strategy.get("strategy_id", "UNKNOWN")
        current_edge = float(strategy.get("edge_score", 60.0))

        strat_pnls = [t.get("pnl", 0.0) for t in live_trades if t.get("strategy_id") == strat_id]
        if not strat_pnls:
            return {
                "strategy_id": strat_id,
                "edge_deteriorating": False,
                "previous_edge_score": current_edge,
                "current_edge_score": current_edge,
                "action": "NONE",
                "message": "Insufficient live trade history. Tracking active.",
            }

        recent = strat_pnls[-5:]
        losing_streak = 0
        streak = 0
        for p in strat_pnls:
            streak = streak + 1 if p < 0 else 0
            losing_streak = max(losing_streak, streak)

        if losing_streak >= self.losing_streak_threshold:
            losses = [p for p in recent if p < 0]
            total_loss = abs(sum(losses))
            new_edge = max(self.floor_edge - 10.0, current_edge - self.decay)
            if new_edge < 40.0:
                action = "KILL_STRATEGY"
                message = (
                    f"Strategy '{strat_id}' edge fell to {new_edge:.0f}; "
                    f"{losing_streak} consecutive losing windows (${total_loss:.2f} loss). KILLED."
                )
            else:
                action = "REDUCE_ALLOCATION"
                message = (
                    f"Strategy '{strat_id}' deteriorating ({losing_streak} losing windows). "
                    f"Edge {current_edge:.0f} -> {new_edge:.0f}; allocation reduced."
                )
            return {
                "strategy_id": strat_id,
                "edge_deteriorating": True,
                "previous_edge_score": current_edge,
                "current_edge_score": new_edge,
                "action": action,
                "message": message,
            }

        new_edge = min(98.0, current_edge + 2.0)
        return {
            "strategy_id": strat_id,
            "edge_deteriorating": False,
            "previous_edge_score": current_edge,
            "current_edge_score": new_edge,
            "action": "MAINTAIN",
            "message": f"Strategy '{strat_id}' stable (edge {new_edge:.0f}).",
        }


performance_monitor_agent = PerformanceMonitoringAgent()