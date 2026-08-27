"""
LLM Orchestrator (STUB — not implemented)

Combines:
    Strategy Signal (TradeSignal)
    + News Signal (NewsSignal)
    + Market Data
    + Portfolio State
    + Risk Constraints (context only — NOT enforcement)

...into a single structured `TradeIntent`.

CRITICAL SAFETY BOUNDARY
------------------------
The LLM orchestrator NEVER calls Alpaca directly and NEVER bypasses the
deterministic Risk Engine. Its only job is context fusion: taking a
strategy's signal plus news/portfolio context and producing a TradeIntent.
The TradeIntent it produces is still just a proposal — the Risk Engine
(model/../backend/app/services/risk_engine.py) is the sole gate before an
order can reach AlpacaService.

This file intentionally does not hardcode any LLM provider or API key.
`LLMProvider` below is a thin interface — wire it up to whichever provider
you choose (Anthropic, OpenAI, local model, etc.) via environment variables.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Optional

from model.schemas.market_data import MarketData
from model.schemas.trade_signal import Action, NewsSignal, OrderType, TradeIntent, TradeSignal


class LLMProvider(ABC):
    """
    Minimal interface for pluggable LLM providers.

    TODO(you): implement a concrete provider, e.g.:

        class AnthropicProvider(LLMProvider):
            def __init__(self):
                self.api_key = os.environ["LLM_API_KEY"]
            def complete(self, prompt: str) -> str:
                ...

    Never hardcode an API key in this file — read it from environment
    configuration (see .env.example -> LLM_API_KEY).
    """

    @abstractmethod
    def complete(self, prompt: str) -> str:
        raise NotImplementedError


class NullLLMProvider(LLMProvider):
    """Default no-op provider so the orchestrator is importable/testable without a real LLM configured."""

    def complete(self, prompt: str) -> str:
        raise NotImplementedError(
            "No LLM provider configured. Set LLM_API_KEY and wire up a concrete "
            "LLMProvider implementation before enabling automation."
        )


class LLMOrchestrator:
    """
    Fuses strategy + news + portfolio + risk context into a TradeIntent.

    Expected inputs:
        strategy_signal: TradeSignal produced by the selected strategy
        news_signals:    list[NewsSignal] relevant to the symbol
        market_data:     MarketData for the symbol
        portfolio:       current portfolio state dict
        risk_constraints: dict describing current risk limits/usage (context
                          only — the orchestrator does not enforce these;
                          the Risk Engine does)

    Expected output:
        TradeIntent, or None if no actionable intent should be produced.
    """

    def __init__(self, llm_provider: Optional[LLMProvider] = None) -> None:
        self.llm_provider = llm_provider or NullLLMProvider()

    def build_prompt(
        self,
        strategy_signal: TradeSignal,
        news_signals: list[NewsSignal],
        market_data: MarketData,
        portfolio: dict,
        risk_constraints: dict,
    ) -> str:
        # TODO(you): construct the actual prompt fed to the LLM provider.
        # Keep it structured (e.g. JSON-in-JSON-out) so the response can be
        # parsed deterministically rather than relying on free text.
        return ""

    def generate_trade_intent(
        self,
        strategy_signal: TradeSignal,
        news_signals: Optional[list[NewsSignal]] = None,
        market_data: Optional[MarketData] = None,
        portfolio: Optional[dict] = None,
        risk_constraints: Optional[dict] = None,
    ) -> Optional[TradeIntent]:
        """
        Produce a TradeIntent from the fused context.

        TODO(you): call self.llm_provider.complete(...) with the prompt from
        build_prompt(), parse the structured response, and construct a
        validated TradeIntent. Until implemented, this passes the strategy
        signal through with no LLM fusion, purely so the pipeline is
        runnable end-to-end during development.
        """
        if strategy_signal is None or strategy_signal.action == Action.HOLD:
            return None
        if not strategy_signal.quantity or strategy_signal.quantity <= 0:
            # No sized quantity yet — a real implementation would size the
            # position here using portfolio/risk_constraints context.
            return None

        news_sentiment = None
        if news_signals:
            news_sentiment = news_signals[0].sentiment

        # NOTE: this pass-through is a development convenience, NOT the
        # real orchestration logic. Replace with actual LLM-fused reasoning.
        return TradeIntent(
            action=strategy_signal.action,
            symbol=strategy_signal.symbol,
            quantity=strategy_signal.quantity or 0,
            order_type=OrderType(strategy_signal.order_type.value),
            confidence=strategy_signal.confidence,
            reasoning=strategy_signal.reasoning,
            stop_loss=strategy_signal.stop_loss,
            take_profit=strategy_signal.take_profit,
            source_strategy=strategy_signal.strategy,
            news_sentiment=news_sentiment,
        )
