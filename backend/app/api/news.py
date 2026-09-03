from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from app.services.news_service import NewsUnavailableError, fetch_news

router = APIRouter(prefix="/api", tags=["news"])


@router.get("/news")
async def get_news(symbols: str | None = Query(default=None)):
    symbol_list = symbols.split(",") if symbols else None
    try:
        articles = await fetch_news(symbols=symbol_list)
        return {"available": True, "articles": articles}
    except NewsUnavailableError:
        return {"available": False, "articles": [], "message": "Data unavailable"}
