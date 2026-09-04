import pytest
import asyncio
from datetime import datetime, timezone
from app.services.automation_engine import AutomationEngine
from app.services.alpaca_service import AlpacaService
from model.schemas.agent_state import AutomationConfig, RiskConfig
from model.schemas.trade_signal import Action, OrderRequest, OrderType, TimeInForce, TradeIntent, TradeSignal

@pytest.fixture
def mock_alpaca(mocker):
    alpaca = mocker.MagicMock(spec=AlpacaService)
    alpaca.paper = True
    alpaca.submit_order.return_value = {
        "id": "mock_order_123",
        "symbol": "BTC/USD",
        "side": "buy",
        "qty": 1.0,
        "status": "accepted",
        "submitted_at": datetime.now(timezone.utc).isoformat()
    }
    alpaca.get_account.return_value = {"buying_power": 100000.0, "portfolio_value": 100000.0, "cash": 100000.0, "equity": 100000.0}
    alpaca.get_positions.return_value = []
    
    mock_bars = mocker.MagicMock()
    mock_bars.bars = [mocker.MagicMock(close=50000.0)]
    alpaca.get_market_data.return_value = mock_bars
    
    return alpaca

@pytest.fixture
def engine(mock_alpaca):
    return AutomationEngine(mock_alpaca)

@pytest.mark.asyncio
async def test_automation_positive_flow(engine, mock_alpaca):
    """Trace positive flow: Signal -> Risk -> Order -> Alpaca -> Log"""
    config = AutomationConfig(
        strategy="momentum",
        assets=["BTC/USD"],
        risk=RiskConfig(max_position_size=10000.0, max_daily_trades=10),
        paper_trading=True
    )
    
    engine.start(config)
    
    result = await engine.execute_test_trade("BTC/USD")
    
    assert result["status"] == "success", f"Failed: {result.get('message')}"
    mock_alpaca.submit_order.assert_called_once()
    assert result["order"]["id"] == "mock_order_123"

@pytest.mark.asyncio
async def test_automation_negative_not_in_allowlist(engine, mock_alpaca, mocker):
    """Test asset outside allowlist submitting zero orders using process_symbol."""
    config = AutomationConfig(
        strategy="momentum",
        assets=["ETH/USD"], # Allowlist is ETH only
        risk=RiskConfig(max_position_size=10000.0),
        paper_trading=True
    )
    engine.start(config)
    
    # Manually trigger process_symbol for an unallowed asset (simulate orchestrator error)
    strategy = mocker.MagicMock()
    strategy.generate_signal.return_value = TradeSignal(
        strategy="momentum",
        action=Action.BUY,
        symbol="BTC/USD",
        quantity=1.0,
        order_type=OrderType.MARKET,
        confidence=0.9,
        reasoning="Test"
    )
    
    # Mock LLM Orchestrator to return an intent
    intent = TradeIntent(
        action=Action.BUY,
        symbol="BTC/USD",
        quantity=1.0,
        order_type=OrderType.MARKET,
        time_in_force=TimeInForce.DAY,
        confidence=0.9,
        reasoning="Test",
        source_strategy="test",
        news_sentiment="NEUTRAL"
    )
    engine.orchestrator.process = mocker.AsyncMock(return_value=intent)
    
    await engine._process_symbol(strategy, "BTC/USD")
    
    assert len(engine.decisions) > 0
    decision = engine.decisions[-1]
    assert "REJECTED" in decision.execution_result
    assert "asset_not_in_user_selection" in decision.execution_result
    mock_alpaca.submit_order.assert_not_called()

@pytest.mark.asyncio
async def test_automation_negative_kill_switch(engine, mock_alpaca):
    """Test kill switch submitting zero orders."""
    config = AutomationConfig(
        strategy="funding_arbitrage",
        assets=["BTC/USD"],
        risk=RiskConfig(max_position_size=10000.0),
        paper_trading=True
    )
    engine.start(config)
    
    engine.emergency_stop() # Engage kill switch
    
    result = await engine.execute_test_trade("BTC/USD")
    
    assert result["status"] == "error"
    assert "Kill switch engaged" in result["message"]
    mock_alpaca.submit_order.assert_not_called()

@pytest.mark.asyncio
async def test_automation_negative_disabled(engine, mock_alpaca):
    """Test disabled automation submitting zero orders."""
    # Engine defaults to IDLE
    result = await engine.execute_test_trade("BTC/USD")
    assert result["status"] == "error"
    assert "Automation is not running" in result["message"]
    mock_alpaca.submit_order.assert_not_called()

@pytest.mark.asyncio
async def test_automation_negative_research_only_strategy(mocker, engine, mock_alpaca):
    """Test research-only strategy submitting zero orders."""
    mocker.patch("app.services.automation_engine.is_live_executable", return_value=False)
    mocker.patch("app.services.automation_engine._registry_keys", return_value=["research_strategy"])
    
    config = AutomationConfig(
        strategy="research_strategy",
        assets=["BTC/USD"],
        risk=RiskConfig(),
        paper_trading=True
    )
    
    engine.start(config)
    
    result = await engine.execute_test_trade("BTC/USD")
    
    assert result["status"] == "error"
    assert "research-only" in result["message"]
    mock_alpaca.submit_order.assert_not_called()
