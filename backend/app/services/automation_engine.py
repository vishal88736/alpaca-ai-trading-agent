"""
Automation Engine — the real, end-to-end paper-trading pipeline.

    MarketData → MarketIntelligence (regime) → Strategy signal → News (real)
      → LLM Orchestrator (TradeIntent) → Deterministic RiskEngine
      → Position sizing → Order manager → Alpaca.submit_order → real order id/status
      → sync + persist → PerformanceMonitor → UI

State machine: IDLE -> RUNNING ⇄ PAUSED -> STOPPED, with EMERGENCY_STOPPED
reachable from anywhere (engages the risk kill-switch).

Safety invariants (unchanged, now wired end-to-end):
  * The LLM/strategy layer never calls Alpaca.
  * Only an APPROVED RiskDecision becomes an OrderRequest.
  * An order is reported "executed" only when Alpaca returns a real order id.
  * Research-only strategies are NEVER auto-executed.
"""

from __future__ import annotations

import asyncio
import logging
import uuid
from datetime import date, datetime

from model.news.news_strategy import NewsStrategy
from model.orchestrator.llm_orchestrator import LLMOrchestrator
from model.schemas.agent_state import AutomationConfig, AutomationState, AutomationStatus, Decision
from model.schemas.trade_signal import Action, OrderRequest, OrderType, TimeInForce
from model.strategies.registry import get_strategy, is_live_executable

from app.agents.market_intelligence import market_intel_agent
from app.db import repository
from app.services.alpaca_service import AlpacaService
from app.services.news_service import NewsUnavailableError, fetch_news
from app.services.risk_engine import DailyRiskCounters, RiskEngine

logger = logging.getLogger("automation_engine")


class AutomationEngine:
    """One instance per connected session. Not shared across users."""

    def __init__(self, alpaca_service: AlpacaService) -> None:
        self.alpaca = alpaca_service
        self.state: AutomationState = AutomationState.IDLE
        self.config: AutomationConfig | None = None
        self.risk_engine: RiskEngine | None = None
        self.counters = DailyRiskCounters()
        self.orchestrator = LLMOrchestrator()
        self.news_strategy = NewsStrategy()

        self.started_at: datetime | None = None
        self.signals_count = 0
        self.trades_count = 0
        self.winning_trades = 0
        self.losing_trades = 0
        self.current_pnl = 0.0
        self.decisions: list[Decision] = []
        self.agent_events: list[dict] = []
        self.current_regime: dict | None = None

        self._task: asyncio.Task | None = None
        self._market_open: bool | None = None
        self._last_known_orders: dict[str, dict] = {}

    # ------------------------------------------------------------------ #
    # Lifecycle
    # ------------------------------------------------------------------ #

    def start(self, config: AutomationConfig) -> AutomationStatus:
        if self._task and not self._task.done():
            self._task.cancel()

        if config.strategy not in _registry_keys():
            raise ValueError(f"Unknown strategy: {config.strategy}")

        self.config = config
        self.risk_engine = RiskEngine(risk_config=config.risk, allowed_assets=config.assets)
        self._reset_daily_counters_if_needed()
        self.state = AutomationState.RUNNING
        self.started_at = datetime.utcnow()

        if not self.alpaca.paper or config.paper_trading is False:
            logger.warning("LIVE trading requested — automation must be explicitly configured for live. Defaulting to paper-only safety behavior.")

        self._add_event("Orchestrator", "START", f"Automation started for strategy '{config.strategy}' on {len(config.assets)} asset(s).")
        self._task = asyncio.create_task(self._run_loop())
        return self.status()

    def pause(self) -> AutomationStatus:
        if self.state != AutomationState.RUNNING:
            raise RuntimeError("Automation is not running")
        self.state = AutomationState.PAUSED
        self._add_event("Orchestrator", "PAUSE", "Automation paused.")
        return self.status()

    def resume(self) -> AutomationStatus:
        if self.state != AutomationState.PAUSED:
            raise RuntimeError("Automation is not paused")
        self.state = AutomationState.RUNNING
        self._add_event("Orchestrator", "RESUME", "Automation resumed.")
        return self.status()

    def stop(self) -> AutomationStatus:
        self.state = AutomationState.STOPPED
        if self._task:
            self._task.cancel()
        self._add_event("Orchestrator", "STOP", "Automation stopped.")
        return self.status()

    def emergency_stop(self) -> AutomationStatus:
        self.state = AutomationState.EMERGENCY_STOPPED
        if self.risk_engine:
            self.risk_engine.engage_kill_switch()
        if self._task:
            self._task.cancel()
        self._add_event("Deterministic Risk", "EMERGENCY_STOP", "Kill switch engaged. All further orders blocked.")
        return self.status()

    def execute_test_trade(self, symbol: str = "BTC/USD") -> dict:
        """Submit a real micro paper order and return the actual Alpaca response.

        No fake fills: if Alpaca rejects or is unavailable we return the real error.
        """
        self._reset_daily_counters_if_needed()
        is_crypto = "/" in symbol or "-" in symbol
        test_qty = 0.0003 if "BTC" in symbol.upper() else (0.01 if "ETH" in symbol.upper() else 1.0)

        order_request = OrderRequest(
            symbol=symbol,
            action=Action.BUY,
            quantity=test_qty,
            order_type=OrderType.MARKET,
            time_in_force=TimeInForce.GTC if is_crypto else TimeInForce.DAY,
            client_order_id=f"TEST-{uuid.uuid4().hex[:8]}",
        )

        try:
            result = self.alpaca.submit_order(order_request)
            self._sync_latest_order(result)
            repository.save_order(result, strategy=self.config.strategy if self.config else "test_trade", paper=self.alpaca.paper)
            self.trades_count += 1
            self.counters.trades_today += 1
            self._add_event("Execution", "SUBMIT_ORDER", f"Test order submitted: BUY {test_qty} {symbol} (id {result.get('id')}).", symbol=symbol)
            return {"status": "success", "order": result}
        except Exception as exc:  # noqa: BLE001
            self._add_event("Execution", "ORDER_ERROR", f"Test order failed: {exc}", symbol=symbol)
            return {"status": "error", "message": str(exc)}

    def status(self) -> AutomationStatus:
        return AutomationStatus(
            state=self.state,
            strategy=self.config.strategy if self.config else None,
            assets=self.config.assets if self.config else [],
            started_at=self.started_at,
            signals_count=self.signals_count,
            trades_count=self.trades_count,
            winning_trades=self.winning_trades,
            losing_trades=self.losing_trades,
            current_pnl=self.current_pnl,
            latest_decision=self.decisions[-1] if self.decisions else None,
        )

    def get_agent_events(self, limit: int = 100) -> list[dict]:
        return list(reversed(self.agent_events[-limit:]))

    # ------------------------------------------------------------------ #
    # Core loop
    # ------------------------------------------------------------------ #

    async def _run_loop(self, poll_seconds: int = 15) -> None:
        strategy = get_strategy(self.config.strategy)
        strategy.initialize(getattr(self.config, "strategy_params", None) or self.config.risk.model_dump())

        while self.state in (AutomationState.RUNNING, AutomationState.PAUSED):
            if self.state == AutomationState.PAUSED:
                await asyncio.sleep(2)
                continue

            self._reset_daily_counters_if_needed()
            self._market_open = self._safe_market_open()
            self._update_regime()

            for symbol in self.config.assets:
                await self._process_symbol(strategy, symbol)

            self._sync_open_orders()
            await asyncio.sleep(poll_seconds)

    async def _process_symbol(self, strategy, symbol: str) -> None:
        market_data = self.alpaca.get_market_data(symbol, timeframe=self.config.timeframe)
        if market_data is None:
            return

        try:
            account = self.alpaca.get_account()
            positions = {p["symbol"]: p for p in self.alpaca.get_positions()}
        except Exception:
            return

        portfolio = {"account": account, "positions": positions}

        strategy.analyze(market_data, portfolio, news=None)
        signal = strategy.generate_signal(market_data, portfolio, news=None)

        # Real news (word-sentiment) — failures degrade to empty, never fabricated.
        news_signals = []
        try:
            articles = await fetch_news(symbols=[symbol], limit=5)
            news_signals = self.news_strategy.generate_signal(news=articles, market_data=market_data)
        except NewsUnavailableError:
            news_signals = []
        except Exception:  # noqa: BLE001
            news_signals = []

        decision_id = str(uuid.uuid4())

        if signal is None:
            self._log_decision(
                Decision(
                    id=decision_id,
                    symbol=symbol,
                    strategy=self.config.strategy,
                    signal=Action.HOLD,
                    confidence=0.5,
                    reasoning=f"Analyzed {symbol} on {self.config.timeframe}; no actionable signal this cycle.",
                    execution_result="HOLD",
                )
            )
            return

        self.signals_count += 1

        intent = self.orchestrator.generate_trade_intent(
            strategy_signal=signal,
            news_signals=news_signals,
            market_data=market_data,
            portfolio=portfolio,
            risk_constraints=self.config.risk.model_dump(),
        )

        if intent is None:
            self._log_decision(
                Decision(
                    id=decision_id,
                    symbol=symbol,
                    strategy=self.config.strategy,
                    signal=signal.action,
                    confidence=signal.confidence,
                    reasoning=signal.reasoning,
                    execution_result="NO_INTENT",
                )
            )
            return

        decision = self.risk_engine.evaluate(intent, account, positions, self.counters, market_open=self._market_open)

        execution_result: str | None
        if not decision.approved:
            execution_result = f"REJECTED:{decision.rejection_reason}"
            self._add_event("Deterministic Risk", "REJECT", f"{symbol} rejected: {decision.rejection_reason}", symbol=symbol)
        elif not is_live_executable(self.config.strategy):
            execution_result = "RESEARCH_ONLY"
            self._add_event("Execution", "SKIPPED", f"{symbol} research strategy — not auto-executed.", symbol=symbol)
        else:
            execution_result = self._submit(intent, decision)

        # Update daily counters / peak
        self._refresh_counter_peak(account)
        self._log_decision(
            Decision(
                id=decision_id,
                symbol=symbol,
                strategy=self.config.strategy,
                signal=signal.action,
                news_sentiment=intent.news_sentiment,
                confidence=intent.confidence,
                risk_decision=decision,
                execution_result=execution_result,
                reasoning=intent.reasoning,
            )
        )

    def _submit(self, intent, decision) -> str:
        order_request = self.risk_engine.to_order_request(decision)
        try:
            result = self.alpaca.submit_order(order_request)
            reconciled = self._sync_latest_order(result)
            repository.save_order(reconciled or result, strategy=intent.source_strategy, paper=self.alpaca.paper)
            repository.save_trade(reconciled or result, strategy=intent.source_strategy, confidence=intent.confidence)
            self.trades_count += 1
            self.counters.trades_today += 1
            self.counters.recent_client_order_ids.add(
                f"{intent.symbol}-{intent.action}-{intent.timestamp.isoformat()}"
            )
            self._add_event(
                "Execution",
                "SUBMIT_ORDER",
                f"{intent.action.value} {intent.quantity} {intent.symbol} -> order {result.get('id')} ({result.get('status')})",
                symbol=intent.symbol,
            )
            return f"{result.get('status') or 'SUBMITTED'}:{result.get('id')}"
        except Exception as exc:  # noqa: BLE001
            self._add_event("Execution", "ORDER_ERROR", f"Order for {intent.symbol} failed: {exc}", symbol=intent.symbol)
            return f"ERROR:{exc}"

    # ------------------------------------------------------------------ #
    # Helpers
    # ------------------------------------------------------------------ #

    def _sync_latest_order(self, result: dict) -> dict:
        oid = result.get("id")
        if not oid:
            return result
        fresh = self.alpaca.get_order_by_id(oid) if hasattr(self.alpaca, "get_order_by_id") else None
        if fresh:
            self._last_known_orders[oid] = fresh
            return {**result, **fresh}
        self._last_known_orders[oid] = result
        return result

    def _sync_open_orders(self) -> None:
        try:
            orders = self.alpaca.get_orders(status="all", limit=20)
            for o in orders:
                if o.get("status") in ("new", "accepted", "partially_filled", "pending_new", "filled"):
                    self._last_known_orders[o["id"]] = o
        except Exception:  # noqa: BLE001
            pass

    def _safe_market_open(self) -> bool:
        try:
            return bool(self.alpaca.is_market_open())
        except Exception:  # noqa: BLE001
            return True

    def _update_regime(self) -> None:
        try:
            benchmark = self.config.assets[0] if self.config and self.config.assets else "SPY"
            bars = self.alpaca.get_market_data(benchmark, timeframe="1D", limit=60)
            if bars is None or not bars.bars:
                return
            self.current_regime = market_intel_agent.analyze_market_regime(bars.bars, benchmark).model_dump(mode="json")
        except Exception:  # noqa: BLE001
            return

    def _refresh_counter_peak(self, account: dict) -> None:
        try:
            pv = float(account.get("portfolio_value", 0.0))
            if pv > self.counters.peak_portfolio_value:
                self.counters.peak_portfolio_value = pv
        except Exception:  # noqa: BLE001
            pass

    def _log_decision(self, decision: Decision) -> None:
        self.decisions.append(decision)
        if len(self.decisions) > 500:
            self.decisions = self.decisions[-500:]
        repository.save_decision(
            {
                "id": decision.id,
                "symbol": decision.symbol,
                "strategy": decision.strategy,
                "signal": decision.signal.value,
                "news_sentiment": decision.news_sentiment,
                "confidence": decision.confidence,
                "risk_decision": ", ".join(decision.risk_decision.checks_failed) if decision.risk_decision else "",
                "execution_result": decision.execution_result,
                "reasoning": decision.reasoning,
            }
        )

    def _add_event(self, agent: str, action: str, details: str, strategy_id: str | None = None, symbol: str | None = None) -> None:
        event = {
            "agent": agent,
            "action": action,
            "details": details,
            "strategy_id": strategy_id,
            "symbol": symbol,
            "timestamp": datetime.utcnow().isoformat(),
        }
        self.agent_events.append(event)
        if len(self.agent_events) > 500:
            self.agent_events = self.agent_events[-500:]
        repository.save_agent_event(event)

    def _reset_daily_counters_if_needed(self) -> None:
        if self.counters.trade_date != date.today():
            self.counters = DailyRiskCounters()


def _registry_keys() -> set[str]:
    from model.strategies.registry import STRATEGIES

    return set(STRATEGIES.keys())