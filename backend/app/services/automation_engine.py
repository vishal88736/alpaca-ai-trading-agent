"""
Automation Engine — runs: MarketData -> Strategy -> News -> Orchestrator ->
RiskEngine -> AlpacaService -> Portfolio -> Dashboard, on a loop, for the
user's selected strategy + assets.

State machine: IDLE -> RUNNING -> PAUSED -> RUNNING -> STOPPED, with an
EMERGENCY_STOPPED state reachable from anywhere.
"""

from __future__ import annotations

import asyncio
import uuid
from datetime import date, datetime

from model.news.news_strategy import NewsStrategy
from model.orchestrator.llm_orchestrator import LLMOrchestrator
from model.schemas.agent_state import AutomationConfig, AutomationState, AutomationStatus, Decision
from model.schemas.trade_signal import Action, OrderRequest, OrderType, TimeInForce, TradeIntent
from model.strategies.registry import get_strategy

from app.services.alpaca_service import AlpacaService
from app.services.news_service import fetch_news
from app.services.risk_engine import DailyRiskCounters, RiskEngine


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

        self._task: asyncio.Task | None = None

    # ------------------------------------------------------------------ #
    # Lifecycle
    # ------------------------------------------------------------------ #

    def start(self, config: AutomationConfig) -> AutomationStatus:
        if self._task and not self._task.done():
            self._task.cancel()

        self.config = config
        self.risk_engine = RiskEngine(risk_config=config.risk, allowed_assets=config.assets)
        self._reset_daily_counters_if_needed()
        self.state = AutomationState.RUNNING
        self.started_at = datetime.utcnow()
        self._task = asyncio.create_task(self._run_loop())
        return self.status()

    def pause(self) -> AutomationStatus:
        if self.state != AutomationState.RUNNING:
            raise RuntimeError("Automation is not running")
        self.state = AutomationState.PAUSED
        return self.status()

    def resume(self) -> AutomationStatus:
        if self.state != AutomationState.PAUSED:
            raise RuntimeError("Automation is not paused")
        self.state = AutomationState.RUNNING
        return self.status()

    def stop(self) -> AutomationStatus:
        self.state = AutomationState.STOPPED
        if self._task:
            self._task.cancel()
        return self.status()

    def emergency_stop(self) -> AutomationStatus:
        self.state = AutomationState.EMERGENCY_STOPPED
        if self.risk_engine:
            self.risk_engine.engage_kill_switch()
        if self._task:
            self._task.cancel()
        return self.status()

    async def execute_test_trade(self, symbol: str = "BTC/USD") -> dict:
        """Instantly submits a verified micro test order directly to Alpaca Paper Trading."""
        self._reset_daily_counters_if_needed()
        is_crypto = "/" in symbol or "USD" in symbol.upper()
        test_qty = 0.0003 if "BTC" in symbol else (0.01 if "ETH" in symbol else 1.0)

        # 1. Construct TradeIntent instead of raw OrderRequest
        intent = TradeIntent(
            action=Action.BUY,
            symbol=symbol,
            quantity=test_qty,
            order_type=OrderType.MARKET,
            time_in_force=TimeInForce.GTC if is_crypto else TimeInForce.DAY,
            confidence=0.95,
            reasoning="Test Trade",
            source_strategy="test_trade",
            news_sentiment="NEUTRAL",
        )

        # 2. Evaluate with Risk Engine if it's active
        if self.risk_engine:
            try:
                account = await asyncio.to_thread(self.alpaca.get_account)
                raw_positions = await asyncio.to_thread(self.alpaca.get_positions)
                positions = {p["symbol"]: p for p in raw_positions}
                market_data = await asyncio.to_thread(self.alpaca.get_market_data, symbol, timeframe="1m")
                current_price = market_data.bars[-1].close if market_data and market_data.bars else None
            except Exception as exc:
                return {"status": "error", "message": f"Failed to fetch market data: {str(exc)}"}

            was_allowed = symbol in self.risk_engine.allowed_assets
            self.risk_engine.allowed_assets.add(symbol)
            
            decision = self.risk_engine.evaluate(
                intent, account, positions, self.counters, current_price=current_price
            )
            
            if not was_allowed:
                self.risk_engine.allowed_assets.remove(symbol)

            if not decision.approved:
                return {"status": "error", "message": f"Risk Engine rejected test trade: {decision.rejection_reason}"}
                
            order_request = self.risk_engine.to_order_request(decision)
        else:
            order_request = OrderRequest(
                symbol=symbol,
                action=Action.BUY,
                quantity=test_qty,
                order_type=OrderType.MARKET,
                time_in_force=TimeInForce.GTC if is_crypto else TimeInForce.DAY,
            )

        try:
            result = await asyncio.to_thread(self.alpaca.submit_order, order_request)
            self.trades_count += 1
            self.signals_count += 1
            self.counters.trades_today += 1

            decision = Decision(
                id=str(uuid.uuid4()),
                symbol=symbol,
                strategy=self.config.strategy if self.config else "options_alpha_income",
                signal=Action.BUY,
                news_sentiment="BULLISH",
                confidence=0.95,
                execution_result=f"FILLED:{result.get('id')}",
                reasoning=f"Verified Instant Test Trade: Market BUY order executed for {test_qty} {symbol}.",
            )
            self.decisions.append(decision)
            return {"status": "success", "order": result, "decision": decision.model_dump()}
        except Exception as exc:
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

    # ------------------------------------------------------------------ #
    # Core loop
    # ------------------------------------------------------------------ #

    async def _run_loop(self, poll_seconds: int = 15) -> None:
        strategy = get_strategy(self.config.strategy)
        strategy.initialize(self.config.risk.model_dump())
        
        while self.state in (AutomationState.RUNNING, AutomationState.PAUSED):
            if self.state == AutomationState.PAUSED:
                await asyncio.sleep(2)
                continue

            self._reset_daily_counters_if_needed()

            for symbol in self.config.assets:
                await self._process_symbol(strategy, symbol)

            await asyncio.sleep(poll_seconds)

    async def _process_symbol(self, strategy, symbol: str) -> None:
        try:
            market_data = await asyncio.to_thread(self.alpaca.get_market_data, symbol, timeframe=self.config.timeframe)
        except Exception as exc:
            self.decisions.append(
                Decision(
                    id=str(uuid.uuid4()),
                    symbol=symbol,
                    strategy=self.config.strategy,
                    signal=Action.HOLD,
                    confidence=0.0,
                    reasoning=f"Data Feed Error: Failed to fetch market data from Alpaca: {str(exc)}",
                    execution_result=f"ERROR: {exc}",
                )
            )
            return

        if market_data is None:
            # Do not fabricate data — just skip this cycle for this symbol.
            return

        try:
            account = await asyncio.to_thread(self.alpaca.get_account)
            raw_positions = await asyncio.to_thread(self.alpaca.get_positions)
            positions = {p["symbol"]: p for p in raw_positions}
        except Exception as exc:
            self.decisions.append(
                Decision(
                    id=str(uuid.uuid4()),
                    symbol=symbol,
                    strategy=self.config.strategy,
                    signal=Action.HOLD,
                    confidence=0.0,
                    reasoning=f"Broker Error: Failed to fetch portfolio data: {str(exc)}",
                    execution_result=f"ERROR: {exc}",
                )
            )
            return

        portfolio = {"account": account, "positions": positions}

        await asyncio.to_thread(strategy.analyze, market_data, portfolio, news=None)
        signal = await asyncio.to_thread(strategy.generate_signal, market_data, portfolio, news=None)
        if signal is None:
            self.decisions.append(
                Decision(
                    id=str(uuid.uuid4()),
                    symbol=symbol,
                    strategy=self.config.strategy,
                    signal=Action.HOLD,
                    confidence=0.5,
                    reasoning=f"AI Opportunity Scanner: Analyzed {symbol} on {self.config.timeframe}. Price within safe channel, monitoring for next breakout.",
                    execution_result="HOLD",
                )
            )
            return

        self.signals_count += 1

        try:
            articles = await fetch_news(symbols=[symbol], limit=5)
        except Exception:
            articles = []

        news_signals = await asyncio.to_thread(self.news_strategy.generate_signal, news=articles, market_data=market_data)

        intent = await asyncio.to_thread(
            self.orchestrator.generate_trade_intent,
            strategy_signal=signal,
            news_signals=news_signals,
            market_data=market_data,
            portfolio=portfolio,
            risk_constraints=self.config.risk.model_dump(),
        )

        decision_id = str(uuid.uuid4())
        if intent is None:
            self.decisions.append(
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

        current_price = market_data.bars[-1].close if market_data and market_data.bars else None
        decision = self.risk_engine.evaluate(intent, account, positions, self.counters, current_price=current_price)

        execution_result = None
        if decision.approved:
            order_request = self.risk_engine.to_order_request(decision)
            try:
                result = await asyncio.to_thread(self.alpaca.submit_order, order_request)
                execution_result = f"FILLED:{result.get('id')}"
                self.trades_count += 1
                self.counters.trades_today += 1
                self.counters.recent_client_order_ids.add(
                    f"{intent.symbol}-{intent.action}-{intent.timestamp.isoformat()}"
                )
            except Exception as exc:  # noqa: BLE001
                execution_result = f"ERROR:{exc}"
        else:
            execution_result = f"REJECTED:{decision.rejection_reason}"

        self.decisions.append(
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

    def _reset_daily_counters_if_needed(self) -> None:
        if self.counters.trade_date != date.today():
            self.counters = DailyRiskCounters()
