"""
AlpacaService — the ONLY place in this codebase that talks to Alpaca.

Uses the current `alpaca-py` SDK (never the deprecated `alpaca-trade-api`).
Strategy code, the orchestrator, and the risk engine never import this
module directly with live credentials — the automation engine is the sole
caller, and only after a `RiskDecision.approved is True`.

All methods are paper-trading safe: `paper` is controlled by the session
the caller connects with (see app/services/session_store.py), defaulting to
True everywhere in this scaffold.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from alpaca.data.historical import CryptoHistoricalDataClient, StockHistoricalDataClient
from alpaca.data.requests import CryptoBarsRequest, StockBarsRequest
from alpaca.data.timeframe import TimeFrame
from alpaca.trading.client import TradingClient
from alpaca.trading.enums import AssetClass as AlpacaAssetClass
from alpaca.trading.enums import OrderSide, TimeInForce as AlpacaTimeInForce
from alpaca.trading.requests import GetAssetsRequest, MarketOrderRequest, LimitOrderRequest, StopOrderRequest, StopLimitOrderRequest

from model.schemas.market_data import AssetClass, AssetInfo, Bar, MarketData, Timeframe
from model.schemas.trade_signal import Action, OrderRequest


TIMEFRAME_MAP = {
    "1m": TimeFrame.Minute,
    "5m": TimeFrame(5, TimeFrame.Unit.Minute) if hasattr(TimeFrame, "Unit") else TimeFrame.Minute,
    "15m": TimeFrame(15, TimeFrame.Unit.Minute) if hasattr(TimeFrame, "Unit") else TimeFrame.Minute,
    "1h": TimeFrame.Hour,
    "1D": TimeFrame.Day,
}


class AlpacaCredentialsError(Exception):
    """Raised when Alpaca rejects the supplied API key/secret."""


class AlpacaService:
    """
    Thin, typed wrapper around alpaca-py's TradingClient + data clients.

    Instantiate one per authenticated session — do not share a single
    instance across users/sessions.
    """

    def __init__(self, api_key: str, secret_key: str, paper: bool = True) -> None:
        self.api_key = api_key
        self.secret_key = secret_key
        self.paper = paper
        self.trading_client = TradingClient(api_key, secret_key, paper=paper)
        self.stock_data_client = StockHistoricalDataClient(api_key, secret_key)
        self.crypto_data_client = CryptoHistoricalDataClient(api_key, secret_key)

    # ------------------------------------------------------------------ #
    # Connection / account
    # ------------------------------------------------------------------ #

    def validate_credentials(self) -> bool:
        """Raises AlpacaCredentialsError if the credentials are invalid."""
        try:
            self.trading_client.get_account()
            return True
        except Exception as exc:  # noqa: BLE001 - surface as a typed error
            raise AlpacaCredentialsError(str(exc)) from exc

    def get_account(self) -> dict:
        account = self.trading_client.get_account()
        return {
            "account_id": account.id,
            "status": account.status,
            "portfolio_value": float(account.portfolio_value),
            "cash": float(account.cash),
            "buying_power": float(account.buying_power),
            "equity": float(account.equity),
            "long_market_value": float(account.long_market_value),
            "short_market_value": float(account.short_market_value),
            "todays_pl": float(account.equity) - float(account.last_equity),
            "total_pl": float(account.equity) - float(account.cash) if account.cash else None,
        }

    # ------------------------------------------------------------------ #
    # Positions / orders
    # ------------------------------------------------------------------ #

    def get_positions(self) -> list[dict]:
        positions = self.trading_client.get_all_positions()
        result = []
        for p in positions:
            unrealized_pl = float(p.unrealized_pl) if p.unrealized_pl is not None else 0.0
            cost_basis = float(p.cost_basis) if p.cost_basis else 0.0
            result.append(
                {
                    "symbol": p.symbol,
                    "quantity": float(p.qty),
                    "avg_entry_price": float(p.avg_entry_price),
                    "current_price": float(p.current_price) if p.current_price else None,
                    "market_value": float(p.market_value) if p.market_value else None,
                    "unrealized_pl": unrealized_pl,
                    "unrealized_pl_pct": (unrealized_pl / cost_basis * 100) if cost_basis else 0.0,
                    "side": p.side,
                }
            )
        return result

    def get_orders(self, status: str = "all", limit: int = 50) -> list[dict]:
        orders = self.trading_client.get_orders()
        normalized: list[dict] = []
        for o in orders:
            st = o.status.value if hasattr(o.status, "value") else str(o.status)
            side = o.side.value if hasattr(o.side, "value") else str(o.side)
            otype = o.order_type.value if hasattr(o.order_type, "value") else str(o.order_type)
            tif = o.time_in_force.value if hasattr(o.time_in_force, "value") else str(o.time_in_force)
            normalized.append(
                {
                    "id": str(o.id),
                    "symbol": o.symbol,
                    "side": side.lower(),
                    "qty": float(o.qty) if o.qty else None,
                    "filled_qty": float(o.filled_qty) if getattr(o, "filled_qty", None) is not None else None,
                    "filled_avg_price": float(o.filled_avg_price) if getattr(o, "filled_avg_price", None) else None,
                    "status": st,
                    "order_type": otype.lower(),
                    "time_in_force": tif.lower(),
                    "submitted_at": o.submitted_at.isoformat() if getattr(o, "submitted_at", None) else None,
                    "filled_at": o.filled_at.isoformat() if getattr(o, "filled_at", None) else None,
                    "client_order_id": getattr(o, "client_order_id", None),
                }
            )
        if status != "all":
            wanted = status.lower()
            normalized = [o for o in normalized if o["status"] == wanted]
        return normalized[:limit]

    def get_order_by_id(self, order_id: str) -> dict | None:
        """Fetch a single order by its Alpaca id. Returns None if not found."""
        try:
            o = self.trading_client.get_order_by_id(order_id)
        except Exception:
            return None
        st = o.status.value if hasattr(o.status, "value") else str(o.status)
        side = o.side.value if hasattr(o.side, "value") else str(o.side)
        return {
            "id": str(o.id),
            "symbol": o.symbol,
            "side": side.lower(),
            "qty": float(o.qty) if o.qty else None,
            "filled_qty": float(o.filled_qty) if getattr(o, "filled_qty", None) is not None else None,
            "filled_avg_price": float(o.filled_avg_price) if getattr(o, "filled_avg_price", None) else None,
            "status": st,
            "submitted_at": o.submitted_at.isoformat() if getattr(o, "submitted_at", None) else None,
            "filled_at": o.filled_at.isoformat() if getattr(o, "filled_at", None) else None,
        }

    def is_market_open(self) -> bool:
        """Whether the currently configured market is open for trading."""
        try:
            clock = self.trading_client.get_clock()
            return bool(clock.is_open)
        except Exception:
            # When the venue cannot be queried (e.g. crypto-only paper flow),
            # default to closed so execution is not attempted blindly.
            return False

    # ------------------------------------------------------------------ #
    # Assets / market data
    # ------------------------------------------------------------------ #

    def get_assets(self, tradable_only: bool = True, asset_class: Optional[str] = None) -> list[AssetInfo]:
        request_params = {}
        if asset_class:
            if asset_class.lower() == "crypto":
                request_params["asset_class"] = AlpacaAssetClass.CRYPTO
            elif asset_class.lower() in ("us_equity", "equity"):
                request_params["asset_class"] = AlpacaAssetClass.US_EQUITY

        request = GetAssetsRequest(**request_params) if request_params else GetAssetsRequest()
        assets = self.trading_client.get_all_assets(request)
        
        results = []
        popular_first = {"BTC/USD", "ETH/USD", "SOL/USD", "DOGE/USD", "AVAX/USD", "LINK/USD", "AAPL", "NVDA", "TSLA", "SPY", "QQQ", "MSFT", "AMZN", "GOOGL", "META"}
        
        for a in assets:
            if tradable_only and not a.tradable:
                continue
            is_crypto = "crypto" in str(a.asset_class).lower() or "/" in str(a.symbol)
            is_options = "option" in str(a.asset_class).lower()
            cls_name = "crypto" if is_crypto else ("options" if is_options else "us_equity")
            
            results.append(
                AssetInfo(
                    symbol=a.symbol,
                    name=a.name or a.symbol,
                    asset_class=cls_name,
                    exchange=str(a.exchange),
                    tradable=a.tradable,
                    fractionable=getattr(a, "fractionable", False),
                )
            )
        
        # Sort so popular tickers and crypto appear first before 10,000 alphabetical equities
        results.sort(key=lambda x: (0 if x.symbol in popular_first else (1 if x.asset_class == "crypto" else 2), x.symbol))
        return results

    def get_market_data(self, symbol: str, timeframe: str = "15m", limit: int = 200) -> Optional[MarketData]:
        """Fetch recent bars for a symbol. Returns MarketData with fallback if Alpaca is unavailable."""
        tf = TIMEFRAME_MAP.get(timeframe, TimeFrame.Minute)
        is_crypto = "/" in symbol

        if is_crypto:
            request = CryptoBarsRequest(symbol_or_symbols=symbol, timeframe=tf, limit=limit)
            bars_resp = self.crypto_data_client.get_crypto_bars(request)
        else:
            request = StockBarsRequest(symbol_or_symbols=symbol, timeframe=tf, limit=limit)
            bars_resp = self.stock_data_client.get_stock_bars(request)
        
        raw_bars = bars_resp.data.get(symbol, []) if hasattr(bars_resp, "data") else []

        # Alpaca data client should be the single source of truth.
        # Fallbacks to un-rate-limited scraping are removed to prevent silent failures.

        if not raw_bars:
            return None

        bars = [
            Bar(
                timestamp=b.timestamp,
                open=float(b.open),
                high=float(b.high),
                low=float(b.low),
                close=float(b.close),
                volume=float(b.volume),
            )
            for b in raw_bars
        ]

        return MarketData(
            symbol=symbol,
            asset_class="crypto" if is_crypto else "us_equity",
            timeframe=timeframe,
            bars=bars,
        )

    # ------------------------------------------------------------------ #
    # Execution — only ever called with an approved OrderRequest
    # ------------------------------------------------------------------ #

    def submit_order(self, order: OrderRequest) -> dict:
        side = OrderSide.BUY if order.action == Action.BUY else OrderSide.SELL
        is_crypto = "/" in order.symbol
        # Alpaca requires GTC for crypto, DAY for equities
        time_in_force = AlpacaTimeInForce.GTC if is_crypto else AlpacaTimeInForce.DAY

        qty = round(order.quantity, 6) if is_crypto else round(order.quantity)

        if order.order_type == "MARKET":
            order_data = MarketOrderRequest(
            symbol=order.symbol,
                qty=qty,
            side=side,
            time_in_force=time_in_force,
            client_order_id=order.client_order_id,
        )
        elif order.order_type == "LIMIT":
            if order.limit_price is None:
                raise ValueError("Limit order requires a limit_price")
            order_data = LimitOrderRequest(
                symbol=order.symbol,
                qty=qty,
                side=side,
                time_in_force=time_in_force,
                limit_price=order.limit_price,
                client_order_id=order.client_order_id,
            )
        elif order.order_type == "STOP":
            if order.stop_price is None:
                raise ValueError("Stop order requires a stop_price")
            order_data = StopOrderRequest(
                symbol=order.symbol,
                qty=qty,
                side=side,
                time_in_force=time_in_force,
                stop_price=order.stop_price,
                client_order_id=order.client_order_id,
            )
        elif order.order_type == "STOP_LIMIT":
            if order.stop_price is None or order.limit_price is None:
                raise ValueError("Stop-Limit order requires both stop_price and limit_price")
            order_data = StopLimitOrderRequest(
                symbol=order.symbol,
                qty=qty,
                side=side,
                time_in_force=time_in_force,
                stop_price=order.stop_price,
                limit_price=order.limit_price,
                client_order_id=order.client_order_id,
            )
        else:
            raise ValueError(f"Unsupported order type: {order.order_type}")

        result = self.trading_client.submit_order(order_data=order_data)
        return {
            "id": str(result.id),
            "symbol": result.symbol,
            "side": str(result.side),
            "qty": float(result.qty) if result.qty else None,
            "status": str(result.status),
            "submitted_at": result.submitted_at.isoformat() if result.submitted_at else None,
        }

    def cancel_order(self, order_id: str) -> None:
        self.trading_client.cancel_order_by_id(order_id)
