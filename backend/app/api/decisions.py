from __future__ import annotations

from fastapi import APIRouter, Depends

from app.core.deps import get_alpaca_service, get_automation_engine
from app.services.alpaca_service import AlpacaService
from app.services.automation_engine import AutomationEngine

router = APIRouter(prefix="/api", tags=["decisions"])


@router.get("/decisions")
def get_decisions(engine: AutomationEngine = Depends(get_automation_engine)):
    return list(reversed(engine.decisions))


@router.get("/trades")
def get_trades(alpaca: AlpacaService = Depends(get_alpaca_service)):
    return alpaca.get_orders()
