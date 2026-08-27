from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from app.core.deps import get_automation_engine
from app.models.api_models import AutomationStartRequest
from app.services.automation_engine import AutomationEngine

router = APIRouter(prefix="/api/automation", tags=["automation"])


@router.post("/start")
async def start(body: AutomationStartRequest, engine: AutomationEngine = Depends(get_automation_engine)):
    if not body.confirmed:
        raise HTTPException(status_code=400, detail="Explicit confirmation is required to start automation")
    try:
        return engine.start(body.config)
    except RuntimeError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.post("/pause")
async def pause(engine: AutomationEngine = Depends(get_automation_engine)):
    try:
        return engine.pause()
    except RuntimeError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.post("/resume")
async def resume(engine: AutomationEngine = Depends(get_automation_engine)):
    try:
        return engine.resume()
    except RuntimeError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.post("/stop")
async def stop(engine: AutomationEngine = Depends(get_automation_engine)):
    return engine.stop()


@router.post("/emergency-stop")
async def emergency_stop(engine: AutomationEngine = Depends(get_automation_engine)):
    return engine.emergency_stop()


@router.get("/status")
async def status(engine: AutomationEngine = Depends(get_automation_engine)):
    return engine.status()


@router.post("/test-trade")
async def test_trade(symbol: str = "BTC/USD", engine: AutomationEngine = Depends(get_automation_engine)):
    res = engine.execute_test_trade(symbol=symbol)
    if res.get("status") == "error":
        raise HTTPException(status_code=400, detail=res.get("message", "Failed to execute test trade"))
    return res
