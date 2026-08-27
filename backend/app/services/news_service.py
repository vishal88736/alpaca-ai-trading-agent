"""
English Crypto News Service

Fetches real-time crypto headlines and market news in English language
from cryptocurrency.cv and top crypto media aggregators.
"""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from typing import Optional
import httpx

from model.news.news_strategy import NewsArticle

CRYPTOCURRENCY_CV_BASE_URL = "https://cryptocurrency.cv"
DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/122.0.0.0 Safari/537.36"
)


class NewsUnavailableError(Exception):
    """Raised when the news provider call fails or data is unavailable."""


def is_english(text: str) -> bool:
    """Verify text is primarily English (Latin characters/ASCII)."""
    if not text:
        return False
    # Check ASCII / Latin character ratio
    ascii_count = sum(1 for c in text if ord(c) < 128)
    return (ascii_count / len(text)) >= 0.85


async def fetch_news(symbols: list[str] | None = None, limit: int = 20) -> list[NewsArticle]:
    """
    Fetch 100% English cryptocurrency market news and trending headlines.
    """
    headers = {
        "User-Agent": DEFAULT_USER_AGENT,
        "Accept": "application/json, application/xml, text/xml, */*",
    }

    articles: list[NewsArticle] = []
    seen_headlines: set[str] = set()

    async with httpx.AsyncClient(timeout=8.0) as client:
        # 1. Fetch from cryptocurrency.cv English news endpoint
        try:
            resp = await client.get(f"{CRYPTOCURRENCY_CV_BASE_URL}/api/news", headers=headers)
            if resp.status_code == 200:
                data = resp.json()
                for item in data.get("articles", []):
                    title = (item.get("title") or item.get("headline") or "").strip()
                    if title and is_english(title) and title not in seen_headlines:
                        seen_headlines.add(title)
                        articles.append(
                            NewsArticle(
                                headline=title,
                                source=item.get("source") or "cryptocurrency.cv",
                                url=item.get("link") or item.get("url") or CRYPTOCURRENCY_CV_BASE_URL,
                                published_at=item.get("publishedAt") or datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                                related_symbol="CRYPTO",
                                body=item.get("description"),
                            )
                        )
        except Exception:
            pass

        # 2. Fetch trending English topics from cryptocurrency.cv
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
                        if cleaned and is_english(cleaned) and cleaned not in seen_headlines:
                            seen_headlines.add(cleaned)
                            articles.append(
                                NewsArticle(
                                    headline=cleaned,
                                    source="cryptocurrency.cv",
                                    url=CRYPTOCURRENCY_CV_BASE_URL,
                                    published_at=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                                    related_symbol=topic.upper(),
                                    body=f"Trending Topic: {topic} (Sentiment: {sentiment}, Mentions: {count})",
                                )
                            )
        except Exception:
            pass

        # 3. Augment with verified English Crypto media feed
        try:
            resp = await client.get("https://cointelegraph.com/rss", headers=headers)
            if resp.status_code == 200:
                root = ET.fromstring(resp.content)
                for item in root.findall(".//item"):
                    title_elem = item.find("title")
                    link_elem = item.find("link")
                    pub_elem = item.find("pubDate")
                    desc_elem = item.find("description")

                    title = (title_elem.text if title_elem is not None and title_elem.text else "").strip()
                    link = (link_elem.text if link_elem is not None and link_elem.text else "").strip()
                    pub = (pub_elem.text if pub_elem is not None and pub_elem.text else "").strip()
                    desc = (desc_elem.text if desc_elem is not None and desc_elem.text else "").strip()

                    # Strip HTML tags if present in description
                    desc_clean = re.sub(r"<[^>]+>", "", desc)

                    if title and is_english(title) and title not in seen_headlines:
                        seen_headlines.add(title)
                        articles.append(
                            NewsArticle(
                                headline=title,
                                source="CoinTelegraph",
                                url=link or CRYPTOCURRENCY_CV_BASE_URL,
                                published_at=pub or datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                                related_symbol="CRYPTO",
                                body=desc_clean[:200] if desc_clean else None,
                            )
                        )
        except Exception:
            pass

    if not articles:
        raise NewsUnavailableError("Unable to load English news feed")

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
