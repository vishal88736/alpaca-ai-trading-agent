"""
Portfolio Manager Agent (deterministic).

Allocates capital across ALIVE strategies based on Edge Score while enforcing
a mandatory cash buffer. Rejected/KILLED/WATCH strategies receive $0 or a
capped watch allocation.

Allocation is a *plan* — it never places orders. Execution is gated by the
deterministic risk engine.
"""

from __future__ import annotations

from typing import Any


class PortfolioManagerAgent:
    def __init__(self, cash_buffer_pct: float = 0.20, max_strategy_pct: float = 0.45) -> None:
        self.cash_buffer_pct = cash_buffer_pct
        self.max_strategy_pct = max_strategy_pct

    def allocate_capital(self, strategies: list[dict[str, Any]], total_portfolio_value: float) -> dict[str, Any]:
        if total_portfolio_value <= 0:
            total_portfolio_value = 100000.0

        alive = [s for s in strategies if s.get("status") == "ALIVE"]
        watch = [s for s in strategies if s.get("status") == "WATCH"]

        allocations: list[dict[str, Any]] = []
        if not alive:
            return {
                "allocations": allocations,
                "cash_reserve_pct": 1.0,
                "cash_reserve_amount": total_portfolio_value,
                "deployed_pct": 0.0,
                "summary": "No ALIVE strategies. 100% capital held in cash safety buffer.",
            }

        total_edge = sum(max(0.0, s.get("edge_score", 50.0)) for s in alive)
        max_deployable = 1.0 - self.cash_buffer_pct

        for s in alive:
            raw = (s.get("edge_score", 50.0) / total_edge) * max_deployable if total_edge > 0 else 0.0
            pct = min(self.max_strategy_pct, raw)
            allocations.append(
                {
                    "strategy_id": s.get("strategy_id"),
                    "allocation_pct": round(pct, 4),
                    "allocation_amount": round(pct * total_portfolio_value, 2),
                    "status": "ALIVE",
                }
            )

        # Watch strategies: no new capital, only record the current (capped) exposure.
        for s in watch:
            allocations.append(
                {
                    "strategy_id": s.get("strategy_id"),
                    "allocation_pct": 0.0,
                    "allocation_amount": 0.0,
                    "status": "WATCH",
                }
            )

        deployed_pct = sum(a["allocation_pct"] for a in allocations if a["status"] == "ALIVE")
        cash_pct = round(1.0 - deployed_pct, 4)

        return {
            "allocations": allocations,
            "cash_reserve_pct": cash_pct,
            "cash_reserve_amount": round(cash_pct * total_portfolio_value, 2),
            "deployed_pct": round(deployed_pct, 4),
            "summary": (
                f"Allocated capital across {len(alive)} ALIVE strateg(y/ies); "
                f"cash safety buffer at {cash_pct:.1%}."
            ),
        }


portfolio_manager_agent = PortfolioManagerAgent()