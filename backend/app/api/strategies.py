from __future__ import annotations

from fastapi import APIRouter

from model.strategies.registry import STRATEGIES, STRATEGY_METADATA

router = APIRouter(prefix="/api/strategies", tags=["strategies"])


@router.get("")
def list_strategies():
    return [
        {"key": key, **STRATEGY_METADATA.get(key, {})}
        for key in STRATEGIES
    ]
