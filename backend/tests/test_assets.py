import pytest
from httpx import AsyncClient
from app.main import app
from app.services.alpaca_service import AlpacaService
from alpaca.trading.enums import AssetClass as AlpacaAssetClass
from model.schemas.market_data import AssetInfo, AssetClass
import asyncio

@pytest.mark.asyncio
async def test_api_assets_crypto_filter():
    """Test the /api/assets endpoint with the crypto filter."""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        # Request all assets
        resp_all = await ac.get("/api/assets")
        assert resp_all.status_code == 200
        all_assets = resp_all.json()
        assert len(all_assets) > 0
        
        # Request crypto assets
        resp_crypto = await ac.get("/api/assets?asset_class=crypto")
        assert resp_crypto.status_code == 200
        crypto_assets = resp_crypto.json()
        assert len(crypto_assets) > 0
        
        # Ensure format and that all are crypto
        for asset in crypto_assets:
            assert asset["asset_class"] == "crypto"
            assert "/" in asset["symbol"] or "crypto" in asset["exchange"].lower()
            
@pytest.mark.asyncio
async def test_api_assets_equity_filter():
    """Test the /api/assets endpoint with the us_equity filter."""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        resp_equity = await ac.get("/api/assets?asset_class=us_equity")
        assert resp_equity.status_code == 200
        equity_assets = resp_equity.json()
        assert len(equity_assets) > 0
        
        for asset in equity_assets:
            assert asset["asset_class"] == "us_equity"
            assert "/" not in asset["symbol"]

def test_alpaca_service_fallback_crypto_failure(mocker):
    """Test that AlpacaService.get_assets continues if crypto fails."""
    # Mock trading client
    mock_tc = mocker.MagicMock()
    mock_asset = mocker.MagicMock(symbol="AAPL", asset_class=AlpacaAssetClass.US_EQUITY, exchange="NASDAQ", tradable=True)
    mock_asset.name = "Apple"
    mock_eq_resp = [mock_asset]
    
    # Setup mock to succeed on US_EQUITY and fail on CRYPTO
    def side_effect(request):
        if request.asset_class == AlpacaAssetClass.US_EQUITY:
            return mock_eq_resp
        else:
            raise Exception("Crypto API unavailable")
            
    mock_tc.get_all_assets.side_effect = side_effect
    
    # Inject mocked client
    service = AlpacaService("fake", "fake")
    service.trading_client = mock_tc
    
    # Call without specific asset class (triggers both calls)
    assets = service.get_assets()
    
    # Should contain Apple but no crypto
    assert len(assets) == 1
    assert assets[0].symbol == "AAPL"
    assert assets[0].asset_class == "us_equity"
