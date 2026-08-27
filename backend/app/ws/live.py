"""
WebSocket endpoint for live dashboard updates (automation status, latest
decisions). The frontend connects to /ws/live?session_id=... after
connecting to Alpaca.

For a hackathon scaffold this polls the AutomationEngine in-process and
pushes snapshots; swap for a pub/sub model if you scale beyond one process.
"""

from __future__ import annotations

import asyncio

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.core.deps import peek_automation_engine

router = APIRouter()


@router.websocket("/ws/live")
async def live_updates(websocket: WebSocket, session_id: str | None = None):
    await websocket.accept()
    try:
        while True:
            engine = peek_automation_engine(session_id) if session_id else None
            if engine is not None:
                await websocket.send_json(engine.status().model_dump(mode="json"))
            else:
                await websocket.send_json({"state": "IDLE"})
            await asyncio.sleep(2)
    except WebSocketDisconnect:
        return
