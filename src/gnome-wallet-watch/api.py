"""FastAPI app: serves the wallet inspector page + a JSON API."""
from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

from .client import get_client
from .wallet import snapshot

BASE_DIR = Path(__file__).parent
app = FastAPI(title="Gnome Wallet Watch")
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


class TokenOut(BaseModel):
    mint: str
    amount: float
    decimals: int


class SnapshotOut(BaseModel):
    address: str
    sol_balance: float
    tokens: list[TokenOut]
    recent_signatures: list[dict]


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/api/wallet/{address}", response_model=SnapshotOut)
async def wallet_api(address: str, tx_limit: int = 10):
    client = get_client()
    try:
        snap = snapshot(client, address, tx_limit=tx_limit)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"RPC error: {exc}")

    return SnapshotOut(
        address=snap.address,
        sol_balance=snap.sol_balance,
        tokens=[
            TokenOut(mint=t.mint, amount=t.amount, decimals=t.decimals)
            for t in sorted(snap.tokens, key=lambda x: x.amount, reverse=True)
        ],
        recent_signatures=[
            {"signature": sig, "block_time": dt.isoformat() if dt else None}
            for sig, dt in snap.recent_signatures
        ],
    )
