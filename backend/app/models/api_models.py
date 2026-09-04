from __future__ import annotations

from pydantic import BaseModel

from model.schemas.agent_state import AutomationConfig


class ConnectRequest(BaseModel):
    api_key: str
    secret_key: str
    paper: bool = True


class ConnectResponse(BaseModel):
    connected: bool
    account_id: str | None = None


class StrategySelectRequest(BaseModel):
    strategy: str


class AutomationStartRequest(BaseModel):
    config: AutomationConfig
    confirmed: bool = False
