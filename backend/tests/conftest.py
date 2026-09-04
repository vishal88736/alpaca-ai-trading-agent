"""
Test bootstrap.

- Adds repo root + backend to sys.path so `model` and `app` import cleanly.
- Clears any ambient credential env vars before `app` is imported, so tests can
  NEVER accidentally call real Alpaca or a real LLM provider.
"""

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
BACKEND = ROOT / "backend"

for p in (str(ROOT), str(BACKEND)):
    if p not in sys.path:
        sys.path.insert(0, p)

for var in ("ALPACA_API_KEY", "ALPACA_SECRET_KEY", "GROQ_API_KEY", "LLM_API_KEY"):
    os.environ.pop(var, None)

import tempfile  # noqa: E402

_TEST_DB_DIR = tempfile.mkdtemp(prefix="trader_test_")
os.environ["DATABASE_URL"] = f"sqlite:///{_TEST_DB_DIR}/test.db"

import pytest  # noqa: E402

from datetime import datetime, timedelta, timezone  # noqa: E402
from uuid import uuid4  # noqa: E402

from model.schemas.market_data import Bar, MarketData  # noqa: E402
from model.schemas.trade_signal import Action  # noqa: E402


def make_trend_bars(symbol: str, n: int = 60, start: float = 100.0, step: float = 0.015) -> list[Bar]:
    """Deterministic upward-trending bars that trigger trend-following signals."""
    bars = []
    t = datetime(2024, 1, 1, tzinfo=timezone.utc)
    price = start
    for i in range(n):
        o = price
        c = price * (1 + step)
        h = c * 1.004
        l = o * 0.996
        bars.append(
            Bar(timestamp=t + timedelta(hours=i), open=o, high=h, low=l, close=c, volume=1000000.0)
        )
        price = c
    return bars


def make_market_data(symbol: str, bars: list[Bar]) -> MarketData:
    return MarketData(
        symbol=symbol,
        asset_class="crypto" if "/" in symbol else "us_equity",
        timeframe="1h",
        bars=bars,
    )


class FakeAlpacaBroker:
    """Isolated test double reproducing the AlpacaService API contract.

    This is ONLY used in tests. It records submitted orders and returns a real
    order id + status, so the end-to-end test can prove that a signal actually
    becomes a submitted order (and fails if it stops short of submission).
    """

    def __init__(self, buying_power: float = 100000.0, market_open: bool = True):
        self.paper = True
        self.buying_power = buying_power
        self.portfolio_value = buying_power
        self.cash = buying_power
        self._market_open = market_open
        self.submitted: list[dict] = []
        self._orders: dict[str, dict] = {}

    def get_market_data(self, symbol: str, timeframe: str = "1h", limit: int = 200):
        return make_market_data(symbol, make_trend_bars(symbol))

    def get_account(self) -> dict:
        return {
            "account_id": "FAKE",
            "status": "ACTIVE",
            "portfolio_value": self.portfolio_value,
            "cash": self.cash,
            "buying_power": self.buying_power,
            "equity": self.portfolio_value,
            "long_market_value": 0.0,
            "short_market_value": 0.0,
            "last_equity": self.portfolio_value,
            "todays_pl": 0.0,
            "total_pl": 0.0,
        }

    def get_positions(self) -> list[dict]:
        return []

    def submit_order(self, order_request) -> dict:
        oid = f"fake-order-{uuid4().hex[:8]}"
        result = {
            "id": oid,
            "symbol": order_request.symbol,
            "side": order_request.action.value.lower() if isinstance(order_request.action, Action) else str(order_request.action).lower(),
            "qty": float(order_request.quantity),
            "status": "accepted",
            "order_type": "market",
            "time_in_force": "day",
            "filled_avg_price": None,
            "client_order_id": getattr(order_request, "client_order_id", None),
            "submitted_at": datetime.now(timezone.utc).isoformat(),
        }
        self.submitted.append(result)
        self._orders[oid] = result
        return result

    def get_order_by_id(self, order_id: str) -> dict | None:
        return self._orders.get(order_id)

    def get_orders(self, status: str = "all", limit: int = 50) -> list[dict]:
        return list(self._orders.values())[:limit]

    def is_market_open(self) -> bool:
        return self._market_open


@pytest.fixture
def fake_alpaca():
    return FakeAlpacaBroker()


@pytest.fixture
def trend_market_data():
    return make_market_data("TEST/USD", make_trend_bars("TEST/USD"))


# Initialize the SQLite schema once for the test session.
from app.db.session import init_db  # noqa: E402

init_db()