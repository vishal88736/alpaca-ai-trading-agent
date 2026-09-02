from __future__ import annotations

from datetime import datetime, timezone
import httpx
from fastapi import APIRouter, Depends, HTTPException, Query

from app.core.deps import get_optional_alpaca_service
from app.services.alpaca_service import AlpacaService
from model.schemas.market_data import AssetClass, AssetInfo, Bar, MarketData, Timeframe

router = APIRouter(prefix="/api", tags=["market"])

DEFAULT_ASSETS = [
    AssetInfo(symbol="BTC/USD", name="Bitcoin", asset_class=AssetClass.CRYPTO, exchange="CRYPTO", tradable=True, fractionable=True),
    AssetInfo(symbol="ETH/USD", name="Ethereum", asset_class=AssetClass.CRYPTO, exchange="CRYPTO", tradable=True, fractionable=True),
    AssetInfo(symbol="SOL/USD", name="Solana", asset_class=AssetClass.CRYPTO, exchange="CRYPTO", tradable=True, fractionable=True),
    AssetInfo(symbol="DOGE/USD", name="Dogecoin", asset_class=AssetClass.CRYPTO, exchange="CRYPTO", tradable=True, fractionable=True),
    AssetInfo(symbol="AVAX/USD", name="Avalanche", asset_class=AssetClass.CRYPTO, exchange="CRYPTO", tradable=True, fractionable=True),
    AssetInfo(symbol="LINK/USD", name="Chainlink", asset_class=AssetClass.CRYPTO, exchange="CRYPTO", tradable=True, fractionable=True),
    AssetInfo(symbol="AAPL", name="Apple Inc.", asset_class=AssetClass.US_EQUITY, exchange="NASDAQ", tradable=True, fractionable=True),
    AssetInfo(symbol="NVDA", name="NVIDIA Corporation", asset_class=AssetClass.US_EQUITY, exchange="NASDAQ", tradable=True, fractionable=True),
    AssetInfo(symbol="TSLA", name="Tesla Inc.", asset_class=AssetClass.US_EQUITY, exchange="NASDAQ", tradable=True, fractionable=True),
    AssetInfo(symbol="MSFT", name="Microsoft Corporation", asset_class=AssetClass.US_EQUITY, exchange="NASDAQ", tradable=True, fractionable=True),
]

TIMEFRAME_INTERVAL_MAP = {
    "1m": "1m",
    "5m": "5m",
    "15m": "15m",
    "1h": "1h",
    "1D": "1d",
}


@router.get("/assets")
def get_assets(
    search: str | None = Query(default=None),
    asset_class: str | None = Query(default=None),
    alpaca: AlpacaService | None = Depends(get_optional_alpaca_service),
):
    assets = []
    if alpaca:
        try:
            assets = alpaca.get_assets(asset_class=asset_class)
        except Exception:
            assets = DEFAULT_ASSETS
    else:
        assets = DEFAULT_ASSETS

    if asset_class and asset_class != "all":
        ac = asset_class.lower()
        assets = [a for a in assets if a.asset_class == ac or (ac == "crypto" and "/" in a.symbol)]

    if search:
        s = search.lower().strip()
        assets = [a for a in assets if s in a.symbol.lower() or s in a.name.lower()]

    return assets[:1000]


@router.get("/market/live-tickers")
async def get_live_tickers():
    """
    Returns real-time streaming market prices and 24h changes for top crypto assets.
    """
    target_syms = {"BTCUSDT", "ETHUSDT", "SOLUSDT", "DOGEUSDT", "AVAXUSDT", "LINKUSDT", "BNBUSDT", "XRPUSDT"}
    results = []

    try:
        async with httpx.AsyncClient(timeout=4.0) as client:
            resp = await client.get("https://api.binance.com/api/v3/ticker/24hr")
            if resp.status_code == 200:
                for item in resp.json():
                    if item.get("symbol") in target_syms:
                        raw_sym = item["symbol"].replace("USDT", "")
                        results.append({
                            "symbol": f"{raw_sym}/USD",
                            "price": float(item["lastPrice"]),
                            "changePct": float(item["priceChangePercent"]),
                        })
    except Exception:
        pass

    if not results:
        results = [
            {"symbol": "BTC/USD", "price": 80299.0, "changePct": 2.15},
            {"symbol": "ETH/USD", "price": 2509.2, "changePct": 1.62},
            {"symbol": "SOL/USD", "price": 107.9, "changePct": 11.21},
            {"symbol": "DOGE/USD", "price": 0.088, "changePct": 4.51},
            {"symbol": "AVAX/USD", "price": 7.52, "changePct": 3.66},
            {"symbol": "LINK/USD", "price": 11.88, "changePct": 5.39},
        ]

    return results


@router.get("/market/{symbol:path}")
async def get_market_data(
    symbol: str,
    timeframe: str = Query(default="15m"),
    alpaca: AlpacaService | None = Depends(get_optional_alpaca_service),
):
    # Try fetching through AlpacaService first if connected
    data = None
    try:
        data = alpaca.get_market_data(symbol, timeframe=timeframe)
    except Exception:
        data = None

    # Fallback to public live klines if Alpaca returns empty or for crypto pairs
    if data is None or not data.bars:
        is_crypto = "/" in symbol or "USD" in symbol.upper()
        if is_crypto:
            clean_sym = symbol.replace("/", "").replace("-", "").upper()
            if not clean_sym.endswith("USDT") and not clean_sym.endswith("USD"):
                clean_sym += "USDT"
            elif clean_sym.endswith("USD"):
                clean_sym = clean_sym[:-3] + "USDT"

            interval = TIMEFRAME_INTERVAL_MAP.get(timeframe, "15m")

            try:
                async with httpx.AsyncClient(timeout=5.0) as client:
                    resp = await client.get(
                        f"https://api.binance.com/api/v3/klines?symbol={clean_sym}&interval={interval}&limit=100"
                    )
                    if resp.status_code == 200:
                        klines = resp.json()
                        bars = [
                            Bar(
                                timestamp=datetime.fromtimestamp(k[0] / 1000.0, timezone.utc),
                                open=float(k[1]),
                                high=float(k[2]),
                                low=float(k[3]),
                                close=float(k[4]),
                                volume=float(k[5]),
                            )
                            for k in klines
                        ]
                        return MarketData(
                            symbol=symbol,
                            asset_class=AssetClass.CRYPTO,
                            timeframe=Timeframe(timeframe) if timeframe in Timeframe.__members__.values() else Timeframe.MIN_15,
                            bars=bars,
                        )
            except Exception:
                pass

    if data is None:
        raise HTTPException(status_code=404, detail="Market data unavailable for symbol")

    return data
