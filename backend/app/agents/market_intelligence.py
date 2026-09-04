"""
Market Intelligence Agent (deterministic).

Analyzes real OHLCV bars to produce a structured market regime:
BULLISH / BEARISH / SIDEWAYS / HIGH_VOLATILITY / LOW_VOLATILITY.

No LLM, no random numbers, no fabricated data. If insufficient bars are supplied,
it returns an honest SIDEWAYS regime with low confidence rather than guessing.
"""

from __future__ import annotations

import math
from datetime import datetime
from typing import Any, Iterable

from model.schemas.research import MarketRegime


def _iter_closes(bars: Iterable[Any]) -> list[float]:
    out: list[float] = []
    for b in bars:
        c = getattr(b, "close", None)
        if c is None and isinstance(b, dict):
            c = b.get("close")
        if c is not None:
            out.append(float(c))
    return out


class MarketIntelligenceAgent:
    def analyze_market_regime(
        self,
        bars: Iterable[Any],
        benchmark_symbol: str | None = None,
    ) -> MarketRegime:
        closes = _iter_closes(bars)

        observations: list[str] = []
        prefix = f"{benchmark_symbol}: " if benchmark_symbol else ""

        if len(closes) < 20:
            return MarketRegime(
                regime="SIDEWAYS",
                confidence=0.5,
                volatility="UNKNOWN",
                momentum="NEUTRAL",
                observations=[f"{prefix}Insufficient historical bars for regime classification"],
            )

        current = closes[-1]
        sma20 = sum(closes[-20:]) / 20.0
        sma50 = sum(closes[-50:]) / 50.0 if len(closes) >= 50 else sum(closes) / len(closes)

        log_returns = [math.log(closes[i] / closes[i - 1]) for i in range(1, len(closes)) if closes[i - 1] > 0]
        if len(log_returns) < 2:
            return MarketRegime(regime="SIDEWAYS", confidence=0.5, volatility="UNKNOWN", momentum="NEUTRAL", observations=[])

        mean_r = sum(log_returns) / len(log_returns)
        var_r = sum((r - mean_r) ** 2 for r in log_returns) / (len(log_returns) - 1)
        vol = math.sqrt(max(var_r, 1e-12))
        annualized_vol = vol * math.sqrt(252)

        momentum_20d = (current - closes[-20]) / closes[-20] if closes[-20] else 0.0

        if annualized_vol > 0.40:
            regime, vol_str, conf = "HIGH_VOLATILITY", "HIGH", 0.80
            observations.append(f"{prefix}Annualized volatility elevated at {annualized_vol:.1%}")
        elif annualized_vol < 0.15:
            regime, vol_str, conf = "LOW_VOLATILITY", "LOW", 0.75
            observations.append(f"{prefix}Volatility compressed at {annualized_vol:.1%}")
        elif current > sma20 and sma20 > sma50 and momentum_20d > 0.02:
            regime, vol_str, conf = "BULLISH", "MEDIUM", 0.80
            observations.append(f"{prefix}Price above 20d & 50d SMA with positive 20d momentum ({momentum_20d:+.1%})")
        elif current < sma20 and sma20 < sma50 and momentum_20d < -0.02:
            regime, vol_str, conf = "BEARISH", "MEDIUM", 0.80
            observations.append(f"{prefix}Price below 20d & 50d SMA with negative 20d momentum ({momentum_20d:+.1%})")
        else:
            regime, vol_str, conf = "SIDEWAYS", "MEDIUM", 0.65
            observations.append(f"{prefix}Price consolidating around 20d/50d SMAs")

        momentum_str = "POSITIVE" if momentum_20d > 0.01 else ("NEGATIVE" if momentum_20d < -0.01 else "NEUTRAL")

        return MarketRegime(
            regime=regime,
            confidence=round(conf, 2),
            volatility=vol_str,
            momentum=momentum_str,
            observations=observations,
            timestamp=datetime.utcnow(),
        )


market_intel_agent = MarketIntelligenceAgent()