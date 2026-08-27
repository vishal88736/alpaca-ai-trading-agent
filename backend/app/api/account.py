from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from app.core.deps import get_alpaca_service
from app.services.alpaca_service import AlpacaService

router = APIRouter(prefix="/api", tags=["account"])


@router.get("/account")
def get_account(alpaca: AlpacaService = Depends(get_alpaca_service)):
    try:
        return alpaca.get_account()
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=502, detail=f"Alpaca error: {exc}") from exc


@router.get("/positions")
def get_positions(alpaca: AlpacaService = Depends(get_alpaca_service)):
    try:
        return alpaca.get_positions()
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=502, detail=f"Alpaca error: {exc}") from exc


@router.get("/orders")
def get_orders(alpaca: AlpacaService = Depends(get_alpaca_service)):
    try:
        return alpaca.get_orders()
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=502, detail=f"Alpaca error: {exc}") from exc
