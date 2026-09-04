"""Deterministic research agents.

These are stateless by design: each method receives its inputs as arguments and
returns a structured result. They hold no global broker state, so they are safe
to use across user sessions. They never place orders — execution remains gated by
the deterministic RiskEngine.
"""

from app.agents.adversary import adversary_agent
from app.agents.backtest import backtest_engine
from app.agents.discovery import discovery_agent
from app.agents.evolution import evolution_engine
from app.agents.explainability import explainability_engine
from app.agents.market_intelligence import market_intel_agent
from app.agents.performance_monitor import performance_monitor_agent
from app.agents.portfolio_manager import portfolio_manager_agent

__all__ = [
    "adversary_agent",
    "backtest_engine",
    "discovery_agent",
    "evolution_engine",
    "explainability_engine",
    "market_intel_agent",
    "performance_monitor_agent",
    "portfolio_manager_agent",
]