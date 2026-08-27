from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query

from app.core.deps import get_alpaca_service
from app.services.alpaca_service import AlpacaService

router = APIRouter(prefix="/api", tags=["market"])


@router.get("/assets")
def get_assets(search: str | None = Query(default=None), alpaca: AlpacaService = Depends(get_alpaca_service)):
    try:
        assets = alpaca.get_assets()
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=502, detail=f"Alpaca error: {exc}") from exc

    if search:
        s = search.lower()
        assets = [a for a in assets if s in a.symbol.lower() or s in a.name.lower()]
    return assets[:200]


@router.get("/market/{symbol}")
def get_market_data(
    symbol: str,
    timeframe: str = Query(default="15m"),
    alpaca: AlpacaService = Depends(get_alpaca_service),
):
    data = alpaca.get_market_data(symbol, timeframe=timeframe)
    if data is None:
        raise HTTPException(status_code=404, detail="Data unavailable")
    return data
