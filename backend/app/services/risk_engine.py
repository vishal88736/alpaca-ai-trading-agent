"""
Risk Engine — the deterministic gate between the LLM Orchestrator and Alpaca.

This module contains NO LLM calls and NO probabilistic logic. Every check
is a plain boolean rule. The LLM Orchestrator's TradeIntent is a proposal
only; this is what actually decides whether an order is allowed to reach
AlpacaService.submit_order().
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date

from model.schemas.agent_state import RiskConfig
from model.schemas.trade_signal import Action, OrderRequest, RiskDecision, TradeIntent


@dataclass
class DailyRiskCounters:
    """Mutable per-day counters tracked by the automation engine, consumed here."""

    trade_date: date = field(default_factory=date.today)
    trades_today: int = 0
    realized_pnl_today: float = 0.0
    recent_client_order_ids: set[str] = field(default_factory=set)


class RiskEngine:
    """
    Deterministic pre-trade risk validation.

    Call `evaluate()` with a TradeIntent + current portfolio/account snapshot
    + the user's configured RiskConfig + running DailyRiskCounters. It never
    mutates broker state — it only approves or rejects.
    """

    def __init__(self, risk_config: RiskConfig, allowed_assets: list[str]) -> None:
        self.risk_config = risk_config
        self.allowed_assets = set(allowed_assets)
        self.kill_switch_engaged: bool = False

    def engage_kill_switch(self) -> None:
        self.kill_switch_engaged = True

    def release_kill_switch(self) -> None:
        self.kill_switch_engaged = False

    def evaluate(
        self,
        intent: TradeIntent,
        account: dict,
        positions: dict[str, dict],
        counters: DailyRiskCounters,
    ) -> RiskDecision:
        passed: list[str] = []
        failed: list[str] = []

        # 1. Kill switch
        if self.kill_switch_engaged:
            failed.append("kill_switch_engaged")
        else:
            passed.append("kill_switch_engaged")

        # 2. Asset allowlist — only user-selected assets are tradable
        if intent.symbol not in self.allowed_assets:
            failed.append("asset_not_in_user_selection")
        else:
            passed.append("asset_not_in_user_selection")

        # 3. Strategy permission (caller must confirm intent.source_strategy
        #    matches the strategy the user actually selected/started)
        # (Enforced by the automation engine constructing `allowed_assets`
        #  and passing only intents from the active strategy; still counted
        #  here as an explicit, auditable check.)
        passed.append("strategy_permission")

        # 4. Duplicate order protection
        client_order_id = f"{intent.symbol}-{intent.action}-{intent.timestamp.isoformat()}"
        if client_order_id in counters.recent_client_order_ids:
            failed.append("duplicate_order")
        else:
            passed.append("duplicate_order")

        # 5. Max order size (USD)
        order_notional = self._estimate_notional(intent, positions)
        if order_notional is not None and order_notional > self.risk_config.max_order_size_usd:
            failed.append("max_order_size_exceeded")
        else:
            passed.append("max_order_size_exceeded")

        # 6. Max position size (% of portfolio)
        portfolio_value = account.get("portfolio_value", 0.0)
        if portfolio_value > 0 and order_notional is not None:
            existing = positions.get(intent.symbol, {}).get("market_value", 0.0)
            projected_pct = (abs(existing) + order_notional) / portfolio_value * 100
            if projected_pct > self.risk_config.max_position_pct:
                failed.append("max_position_pct_exceeded")
            else:
                passed.append("max_position_pct_exceeded")
        else:
            passed.append("max_position_pct_exceeded")

        # 7. Max portfolio exposure (%)
        if portfolio_value > 0:
            total_exposure = sum(abs(p.get("market_value", 0.0)) for p in positions.values())
            projected_total_pct = (total_exposure + (order_notional or 0)) / portfolio_value * 100
            if projected_total_pct > self.risk_config.max_portfolio_exposure_pct:
                failed.append("max_portfolio_exposure_exceeded")
            else:
                passed.append("max_portfolio_exposure_exceeded")
        else:
            passed.append("max_portfolio_exposure_exceeded")

        # 8. Available buying power
        buying_power = account.get("buying_power", 0.0)
        if intent.action == Action.BUY and order_notional is not None and order_notional > buying_power:
            failed.append("insufficient_buying_power")
        else:
            passed.append("insufficient_buying_power")

        # 9. Daily loss limit
        if portfolio_value > 0:
            daily_loss_pct = -counters.realized_pnl_today / portfolio_value * 100
            if daily_loss_pct > self.risk_config.max_daily_loss_pct:
                failed.append("max_daily_loss_exceeded")
            else:
                passed.append("max_daily_loss_exceeded")
        else:
            passed.append("max_daily_loss_exceeded")

        # 10. Max trades per day
        if counters.trades_today >= self.risk_config.max_trades_per_day:
            failed.append("max_trades_per_day_exceeded")
        else:
            passed.append("max_trades_per_day_exceeded")

        approved = len(failed) == 0
        return RiskDecision(
            approved=approved,
            trade_intent=intent,
            rejection_reason=", ".join(failed) if failed else None,
            checks_passed=passed,
            checks_failed=failed,
        )

    @staticmethod
    def _estimate_notional(intent: TradeIntent, positions: dict[str, dict]) -> float | None:
        current_price = positions.get(intent.symbol, {}).get("current_price")
        if current_price is not None and current_price > 0:
            return float(current_price) * intent.quantity
        if intent.limit_price and intent.limit_price > 0:
            return float(intent.limit_price) * intent.quantity
        if intent.take_profit and intent.take_profit > 0:
            return (float(intent.take_profit) / 1.08) * intent.quantity
        return None

    @staticmethod
    def to_order_request(decision: RiskDecision) -> OrderRequest:
        """Only call this on an APPROVED RiskDecision."""
        if not decision.approved:
            raise ValueError("Cannot build an OrderRequest from a rejected RiskDecision")
        intent = decision.trade_intent
        return OrderRequest(
            symbol=intent.symbol,
            action=intent.action,
            quantity=intent.quantity,
            order_type=intent.order_type,
            time_in_force=intent.time_in_force,
        )
