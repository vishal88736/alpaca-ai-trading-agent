"""
News Strategy (STUB — not implemented)

Responsible for converting raw news articles into structured market
sentiment/features (a `NewsSignal`) that strategies and the LLM Orchestrator
can consume. Does NOT decide trades on its own.

TODO(you): implement actual news intelligence — e.g. LLM-based sentiment
scoring, keyword/event extraction, source credibility weighting.
"""

from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel

from model.schemas.market_data import MarketData
from model.schemas.trade_signal import NewsSignal


class NewsArticle(BaseModel):
    """A single raw news article, as fetched by the backend's news service."""

    headline: str
    source: str
    url: Optional[str] = None
    published_at: str
    related_symbol: Optional[str] = None
    body: Optional[str] = None


class NewsStrategy:
    """
    Converts raw news into structured sentiment signals.

    Expected inputs:
        news:        list[NewsArticle] relevant to the symbols being traded
        market_data: MarketData for additional context (e.g. price reaction)

    Expected output:
        list[NewsSignal] — one per symbol with relevant news, or empty list.
    """

    POSITIVE_WORDS = {
        "surge", "surges", "rally", "rallies", "bull", "bullish", "high", "highs",
        "gain", "gains", "jump", "jumps", "breakout", "approval", "adoption", "inflow", "inflows"
    }
    NEGATIVE_WORDS = {
        "drop", "drops", "crash", "crashes", "bear", "bearish", "low", "lows",
        "loss", "losses", "fall", "falls", "ban", "bans", "hack", "hacked", "sec", "fine", "fines", "censure"
    }

    def analyze(self, news: list[NewsArticle], market_data: Optional[MarketData] = None) -> dict[str, Any]:
        """Group news by symbol and compute word sentiment frequency."""
        summary: dict[str, dict[str, Any]] = {}
        for article in news:
            sym = (article.related_symbol or "CRYPTO").upper()
            if sym not in summary:
                summary[sym] = {"pos": 0, "neg": 0, "articles": []}
            summary[sym]["articles"].append(article)

            text = f"{article.headline} {article.body or ''}".lower()
            words = set(text.split())
            summary[sym]["pos"] += len(words.intersection(self.POSITIVE_WORDS))
            summary[sym]["neg"] += len(words.intersection(self.NEGATIVE_WORDS))

        return summary

    def generate_signal(
        self, news: list[NewsArticle], market_data: Optional[MarketData] = None
    ) -> list[NewsSignal]:
        """Generate structured NewsSignal instances per related symbol."""
        if not news:
            return []

        analysis = self.analyze(news, market_data)
        signals: list[NewsSignal] = []

        for sym, data in analysis.items():
            pos = data["pos"]
            neg = data["neg"]
            total = pos + neg
            article_count = len(data["articles"])

            if total == 0:
                score = 0.0
                sentiment = "NEUTRAL"
            else:
                score = max(-1.0, min(1.0, (pos - neg) / total))
                if score >= 0.2:
                    sentiment = "POSITIVE"
                elif score <= -0.2:
                    sentiment = "NEGATIVE"
                else:
                    sentiment = "NEUTRAL"

            first_headline = data["articles"][0].headline if data["articles"] else "Recent crypto news update"
            signals.append(
                NewsSignal(
                    symbol=sym,
                    sentiment=sentiment,
                    sentiment_score=round(score, 2),
                    summary=f"Analysis of {article_count} headline(s). Lead: {first_headline[:100]}",
                    source_count=article_count,
                )
            )

        return signals

