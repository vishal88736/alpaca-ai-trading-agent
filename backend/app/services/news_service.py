"""
News service powered by cryptocurrency.cv (free crypto news aggregator).

Fetches real-time crypto headlines, trending topics, and market news
without requiring third-party API keys.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional
import httpx

from model.news.news_strategy import NewsArticle

CRYPTOCURRENCY_CV_BASE_URL = "https://cryptocurrency.cv"
DEFAULT_USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"


class NewsUnavailableError(Exception):
    """Raised when the news provider call fails or data is unavailable."""


async def fetch_news(symbols: list[str] | None = None, limit: int = 20) -> list[NewsArticle]:
    """
    Fetch crypto market news and trending headlines from cryptocurrency.cv.
    """
    headers = {
        "User-Agent": DEFAULT_USER_AGENT,
        "Accept": "application/json",
    }

    articles: list[NewsArticle] = []
    seen_headlines: set[str] = set()

    async with httpx.AsyncClient(timeout=10.0) as client:
        # 1. Fetch trending crypto topics and recent headlines
        try:
            resp = await client.get(f"{CRYPTOCURRENCY_CV_BASE_URL}/api/trending", headers=headers)
            if resp.status_code == 200:
                data = resp.json()
                for item in data.get("trending", []):
                    topic = item.get("topic", "Crypto")
                    sentiment = item.get("sentiment", "neutral")
                    count = item.get("count", 1)
                    for headline in item.get("recentHeadlines", []):
                        cleaned = headline.strip()
                        if cleaned and cleaned not in seen_headlines:
                            seen_headlines.add(cleaned)
                            articles.append(
                                NewsArticle(
                                    headline=cleaned,
                                    source="cryptocurrency.cv",
                                    url=f"{CRYPTOCURRENCY_CV_BASE_URL}",
                                    published_at=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                                    related_symbol=topic.upper(),
                                    body=f"Trending Topic: {topic} (Sentiment: {sentiment}, Mentions: {count})",
                                )
                            )
        except Exception:
            pass

        # 2. Fetch international crypto news feed
        try:
            resp = await client.get(f"{CRYPTOCURRENCY_CV_BASE_URL}/api/news/international", headers=headers)
            if resp.status_code == 200:
                data = resp.json()
                for item in data.get("articles", []):
                    title = (item.get("title") or item.get("description") or "").strip()
                    if title and title not in seen_headlines:
                        seen_headlines.add(title)
                        articles.append(
                            NewsArticle(
                                headline=title,
                                source=item.get("source") or "cryptocurrency.cv",
                                url=item.get("link") or f"{CRYPTOCURRENCY_CV_BASE_URL}",
                                published_at=item.get("pubDate") or datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                                related_symbol=(item.get("category") or "CRYPTO").upper(),
                                body=item.get("description"),
                            )
                        )
        except Exception:
            pass

    if not articles:
        raise NewsUnavailableError("Unable to reach cryptocurrency.cv news feed")

    # Filter by symbols if requested
    if symbols:
        normalized_symbols = [s.replace("/", "").replace("-", "").upper() for s in symbols]
        filtered = [
            a for a in articles
            if any(sym in (a.related_symbol or "").upper() or sym in a.headline.upper() for sym in normalized_symbols)
        ]
        if filtered:
            return filtered[:limit]

    return articles[:limit]

