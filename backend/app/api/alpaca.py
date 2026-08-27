from __future__ import annotations

from fastapi import APIRouter, Cookie, Depends, HTTPException, Response

from app.core.deps import clear_session_services, get_or_create_session_id
from app.models.api_models import ConnectRequest, ConnectResponse
from app.services.alpaca_service import AlpacaCredentialsError, AlpacaService
from app.services.session_store import AlpacaSession, session_store

router = APIRouter(prefix="/api/alpaca", tags=["alpaca"])


@router.post("/connect", response_model=ConnectResponse)
def connect(
    body: ConnectRequest,
    response: Response,
    session_id: str = Depends(get_or_create_session_id),
):
    """
    Validates credentials against Alpaca and stores them server-side only.
    The API key/secret are never echoed back in the response or logged.
    """
    service = AlpacaService(body.api_key, body.secret_key, paper=body.paper)
    try:
        service.validate_credentials()
    except AlpacaCredentialsError as exc:
        raise HTTPException(status_code=401, detail="Invalid Alpaca credentials") from exc

    session_store.set(session_id, AlpacaSession(api_key=body.api_key, secret_key=body.secret_key, paper=body.paper))
    account = service.get_account()
    return ConnectResponse(connected=True, account_id=str(account.get("account_id")))


@router.post("/disconnect")
def disconnect(response: Response, session_id: str | None = Cookie(default=None)):
    if session_id:
        session_store.clear(session_id)
        clear_session_services(session_id)
    response.delete_cookie("session_id")
    return {"connected": False}


@router.get("/status")
def status(session_id: str | None = Cookie(default=None)):
    return {"connected": session_id is not None and session_store.is_connected(session_id)}
