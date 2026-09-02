"""
Groq-Powered LLM Orchestrator

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
(backend/app/services/risk_engine.py) is the sole gate before an order
can reach AlpacaService.
"""

from __future__ import annotations

import json
import logging
import os
from abc import ABC, abstractmethod
from typing import Any, Optional

import httpx

from model.schemas.market_data import MarketData
from model.schemas.trade_signal import Action, NewsSignal, OrderType, TradeIntent, TradeSignal

logger = logging.getLogger(__name__)


class LLMProvider(ABC):
    """Minimal interface for pluggable LLM providers."""

    @abstractmethod
    def complete(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        raise NotImplementedError


class GroqProvider(LLMProvider):
    """
    High-performance, low-latency Groq LLM Provider.

    Uses Groq's OpenAI-compatible chat completion API.
    Model name and API key can be set via constructor arguments or
    environment variables (GROQ_API_KEY, GROQ_MODEL).
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        timeout: float = 12.0,
    ) -> None:
        self.api_key = api_key or os.environ.get("GROQ_API_KEY") or os.environ.get("LLM_API_KEY") or ""
        self.model = model or os.environ.get("GROQ_MODEL") or os.environ.get("LLM_MODEL") or "llama-3.3-70b-versatile"
        self.timeout = timeout
        self.endpoint = "https://api.groq.com/openai/v1/chat/completions"

    def is_configured(self) -> bool:
        return bool(self.api_key and len(self.api_key.strip()) > 0)

    def complete(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        if not self.is_configured():
            raise RuntimeError("GROQ_API_KEY is not configured.")

        system = system_prompt or (
            "You are an expert quantitative trading AI orchestrator. "
            "Analyze algorithmic signals, news sentiment, and portfolio context. "
            "Always respond strictly with a valid JSON object matching the requested schema."
        )

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": prompt},
            ],
            "response_format": {"type": "json_object"},
            "temperature": 0.2,
            "max_tokens": 512,
        }

        with httpx.Client(timeout=self.timeout) as client:
            response = client.post(self.endpoint, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]


class FallbackPassThroughProvider(LLMProvider):
    """Fallback provider when no external LLM key is configured."""

    def complete(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        return json.dumps({"action": "PASS", "confidence": 1.0, "reasoning": "Pass-through mode"})


class LLMOrchestrator:
    """
    Fuses strategy + news + portfolio + risk context into a TradeIntent.
    """

    def __init__(self, llm_provider: Optional[LLMProvider] = None) -> None:
        if llm_provider is not None:
            self.llm_provider = llm_provider
        else:
            groq = GroqProvider()
            self.llm_provider = groq if groq.is_configured() else FallbackPassThroughProvider()

    def build_prompt(
        self,
        strategy_signal: TradeSignal,
        news_signals: list[NewsSignal],
        market_data: Optional[MarketData],
        portfolio: Optional[dict],
        risk_constraints: Optional[dict],
    ) -> str:
        latest_price = market_data.bars[-1].close if market_data and market_data.bars else 0.0
        news_summary = [
            {"headline": n.headline, "sentiment": n.sentiment, "score": n.confidence}
            for n in (news_signals or [])
        ]

        payload = {
            "task": "Evaluate trading signal with news and risk context",
            "market_data": {
                "symbol": strategy_signal.symbol,
                "current_price": latest_price,
            },
            "strategy_proposal": {
                "strategy": strategy_signal.strategy,
                "action": strategy_signal.action.value,
                "quantity": strategy_signal.quantity,
                "confidence": strategy_signal.confidence,
                "reasoning": strategy_signal.reasoning,
                "stop_loss": strategy_signal.stop_loss,
                "take_profit": strategy_signal.take_profit,
            },
            "news_intelligence": news_summary,
            "portfolio_context": {
                "buying_power": portfolio.get("account", {}).get("buying_power", 0.0) if portfolio else 0.0,
                "existing_positions": list(portfolio.get("positions", {}).keys()) if portfolio else [],
            },
            "risk_limits": risk_constraints or {},
            "response_schema": {
                "action": "BUY | SELL | HOLD",
                "confidence": "float 0.0 - 1.0",
                "adjusted_quantity": "float or null",
                "reasoning": "concise synthesis explanation string",
                "news_sentiment": "BULLISH | BEARISH | NEUTRAL",
            },
        }

        return json.dumps(payload, indent=2)

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
        """
        if strategy_signal is None or strategy_signal.action == Action.HOLD:
            return None
        if not strategy_signal.quantity or strategy_signal.quantity <= 0:
            return None

        # Default fallback values from quantitative strategy
        intent_action = strategy_signal.action
        intent_confidence = strategy_signal.confidence
        intent_reasoning = strategy_signal.reasoning
        intent_qty = strategy_signal.quantity or 1.0
        news_sentiment = news_signals[0].sentiment if news_signals else "NEUTRAL"

        # If Groq provider is configured, query Groq for contextual reasoning
        if isinstance(self.llm_provider, GroqProvider) and self.llm_provider.is_configured():
            try:
                prompt = self.build_prompt(
                    strategy_signal=strategy_signal,
                    news_signals=news_signals or [],
                    market_data=market_data,
                    portfolio=portfolio,
                    risk_constraints=risk_constraints,
                )
                raw_response = self.llm_provider.complete(prompt)
                parsed = json.loads(raw_response)

                action_str = str(parsed.get("action", "")).upper()
                if action_str == "HOLD":
                    return None
                elif action_str in ("BUY", "SELL"):
                    intent_action = Action(action_str)

                if "confidence" in parsed and isinstance(parsed["confidence"], (int, float)):
                    intent_confidence = float(parsed["confidence"])

                if "reasoning" in parsed and parsed["reasoning"]:
                    intent_reasoning = f"[Groq {self.llm_provider.model}] {parsed['reasoning']}"

                if "news_sentiment" in parsed and parsed["news_sentiment"]:
                    news_sentiment = parsed["news_sentiment"]

                if parsed.get("adjusted_quantity") and float(parsed["adjusted_quantity"]) > 0:
                    intent_qty = float(parsed["adjusted_quantity"])

            except Exception as e:
                logger.warning(f"Groq LLM orchestration encountered an error, falling back to quantitative strategy signal: {e}")

        return TradeIntent(
            action=intent_action,
            symbol=strategy_signal.symbol,
            quantity=intent_qty,
            order_type=OrderType(strategy_signal.order_type.value),
            confidence=intent_confidence,
            reasoning=intent_reasoning,
            stop_loss=strategy_signal.stop_loss,
            take_profit=strategy_signal.take_profit,
            source_strategy=strategy_signal.strategy,
            news_sentiment=news_sentiment,
        )
