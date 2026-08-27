from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from app.core.deps import get_automation_engine
from app.models.api_models import AutomationStartRequest
from app.services.automation_engine import AutomationEngine

router = APIRouter(prefix="/api/automation", tags=["automation"])


@router.post("/start")
def start(body: AutomationStartRequest, engine: AutomationEngine = Depends(get_automation_engine)):
    if not body.confirmed:
        raise HTTPException(status_code=400, detail="Explicit confirmation is required to start automation")
    try:
        return engine.start(body.config)
    except RuntimeError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.post("/pause")
def pause(engine: AutomationEngine = Depends(get_automation_engine)):
    try:
        return engine.pause()
    except RuntimeError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.post("/resume")
def resume(engine: AutomationEngine = Depends(get_automation_engine)):
    try:
        return engine.resume()
    except RuntimeError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.post("/stop")
def stop(engine: AutomationEngine = Depends(get_automation_engine)):
    return engine.stop()


@router.post("/emergency-stop")
def emergency_stop(engine: AutomationEngine = Depends(get_automation_engine)):
    return engine.emergency_stop()


@router.get("/status")
def status(engine: AutomationEngine = Depends(get_automation_engine)):
    return engine.status()
