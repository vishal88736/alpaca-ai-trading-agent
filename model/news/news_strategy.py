"""
News Strategy

Responsible for converting raw news articles into structured market
sentiment/features (a `NewsSignal`) that strategies and the LLM Orchestrator
can consume. Does NOT decide trades on its own.
"""

from __future__ import annotations

import json
import logging
from typing import Any, Optional

from pydantic import BaseModel

from model.schemas.market_data import MarketData
from model.schemas.trade_signal import NewsSignal
from model.orchestrator.llm_orchestrator import LLMProvider, GroqProvider, FallbackPassThroughProvider

logger = logging.getLogger(__name__)


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
    Converts raw news into structured sentiment signals using an LLM.

    Expected inputs:
        news:        list[NewsArticle] relevant to the symbols being traded
        market_data: MarketData for additional context (e.g. price reaction)

    Expected output:
        list[NewsSignal] — one per symbol with relevant news, or empty list.
    """

    def __init__(self, llm_provider: Optional[LLMProvider] = None) -> None:
        if llm_provider is not None:
            self.llm_provider = llm_provider
        else:
            groq = GroqProvider()
            self.llm_provider = groq if groq.is_configured() else FallbackPassThroughProvider()

    def generate_signal(
        self, news: list[NewsArticle], market_data: Optional[MarketData] = None
    ) -> list[NewsSignal]:
        """Generate structured NewsSignal instances per related symbol."""
        if not news:
            return []

        # Group news by symbol
        summary: dict[str, list[NewsArticle]] = {}
        for article in news:
            sym = (article.related_symbol or "CRYPTO").upper()
            if sym not in summary:
                summary[sym] = []
            summary[sym].append(article)

        signals: list[NewsSignal] = []

        for sym, articles in summary.items():
            article_count = len(articles)
            first_headline = articles[0].headline if articles else "Recent crypto news update"
            
            # Default signal in case of LLM failure or PassThrough
            sentiment = "NEUTRAL"
            score = 0.0
            llm_summary = f"Analysis of {article_count} headline(s). Lead: {first_headline[:100]}"

            # Attempt LLM evaluation
            if isinstance(self.llm_provider, GroqProvider) and self.llm_provider.is_configured():
                try:
                    news_payload = [
                        {"headline": a.headline, "body": a.body or ""} 
                        for a in articles
                    ]
                    
                    prompt_payload = {
                        "task": "Analyze sentiment of the provided news articles for the given financial asset.",
                        "symbol": sym,
                        "articles": news_payload,
                        "response_schema": {
                            "sentiment": "POSITIVE | NEGATIVE | NEUTRAL",
                            "sentiment_score": "float from -1.0 (extremely negative) to 1.0 (extremely positive)",
                            "summary": "Concise 1-2 sentence summary of the overall news impact on the asset"
                        }
                    }

                    system_prompt = (
                        "You are a quantitative trading news analyst. "
                        "Evaluate the sentiment of the provided news articles. "
                        "Always respond strictly with a valid JSON object matching the requested schema."
                    )

                    raw_response = self.llm_provider.complete(
                        prompt=json.dumps(prompt_payload, indent=2),
                        system_prompt=system_prompt
                    )
                    parsed = json.loads(raw_response)

                    if "sentiment" in parsed and parsed["sentiment"].upper() in ("POSITIVE", "NEGATIVE", "NEUTRAL"):
                        sentiment = parsed["sentiment"].upper()
                    if "sentiment_score" in parsed and isinstance(parsed["sentiment_score"], (int, float)):
                        score = max(-1.0, min(1.0, float(parsed["sentiment_score"])))
                    if "summary" in parsed and parsed["summary"]:
                        llm_summary = parsed["summary"]

                except Exception as e:
                    logger.warning(f"Failed to analyze news with LLM for {sym}, falling back to NEUTRAL: {e}")

            signals.append(
                NewsSignal(
                    symbol=sym,
                    sentiment=sentiment,
                    sentiment_score=round(score, 2),
                    summary=llm_summary,
                    source_count=article_count,
                )
            )

        return signals
