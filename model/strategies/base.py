"""
BaseStrategy — the interface every strategy in model/strategies/ must implement.

Design contract
----------------
1. `initialize(config)` is called once when the user starts automation with
   this strategy selected. `config` is the validated Pydantic config for
   that specific strategy (see each strategy file's `*Config` class).

2. `analyze(market_data, portfolio, news)` is called on every automation
   cycle BEFORE `generate_signal`. It exists as a separate step so
   implementations can cache indicators / intermediate state
   (e.g. rolling z-scores, order book imbalance) without recomputing them
   inside `generate_signal`. It should return whatever internal
   representation is useful to `generate_signal` — the base class does not
   constrain its return type.

3. `generate_signal(market_data, portfolio, news)` must return a
   `model.schemas.trade_signal.TradeSignal` or `None` (no signal this
   cycle). This is the ONLY output that leaves the strategy layer, and it
   flows into the LLM Orchestrator — never directly to Alpaca.

Strategies must be broker-agnostic: they only see `MarketData`, portfolio
state, and `NewsSignal` objects, never the Alpaca SDK directly.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Optional

from model.schemas.market_data import MarketData
from model.schemas.trade_signal import NewsSignal, TradeSignal


class BaseStrategy(ABC):
    name: str = "base"

    def __init__(self) -> None:
        self.config: Any = None
        self.initialized: bool = False

    @abstractmethod
    def initialize(self, config: Any) -> None:
        """Validate and store strategy configuration. Called once on automation start."""
        raise NotImplementedError

    @abstractmethod
    def analyze(
        self,
        market_data: MarketData,
        portfolio: dict,
        news: Optional[list[NewsSignal]] = None,
    ) -> Any:
        """
        Compute indicators / internal state for this cycle.

        Returns whatever intermediate representation `generate_signal` needs.
        Implementations decide the shape; the automation engine treats it as
        opaque and just forwards it.
        """
        raise NotImplementedError

    @abstractmethod
    def generate_signal(
        self,
        market_data: MarketData,
        portfolio: dict,
        news: Optional[list[NewsSignal]] = None,
    ) -> Optional[TradeSignal]:
        """Return a TradeSignal for this cycle, or None if there is no actionable signal."""
        raise NotImplementedError
