"""Core wallet inspection logic. Framework-agnostic — CLI just calls this."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from solana.rpc.api import Client
from solders.pubkey import Pubkey


@dataclass
class TokenHolding:
    mint: str
    amount: float
    decimals: int


@dataclass
class WalletSnapshot:
    address: str
    sol_balance: float
    tokens: list[TokenHolding]
    recent_signatures: list[tuple[str, datetime | None]]


def _parse_pubkey(address: str) -> Pubkey:
    try:
        return Pubkey.from_string(address)
    except Exception as exc:
        raise ValueError(f"Invalid Solana address: {address}") from exc


def get_sol_balance(client: Client, address: str) -> float:
    pubkey = _parse_pubkey(address)
    resp = client.get_balance(pubkey)
    lamports = resp.value
    return lamports / 1_000_000_000


def get_token_holdings(client: Client, address: str) -> list[TokenHolding]:
    pubkey = _parse_pubkey(address)
    resp = client.get_token_accounts_by_owner(
        pubkey,
        program_id=Pubkey.from_string("TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA"),
    )
    holdings: list[TokenHolding] = []
    for account in resp.value:
        parsed = account.account.data.parsed
        info = parsed["info"]
        token_amount = info["tokenAmount"]
        amount = float(token_amount["uiAmountString"])
        if amount == 0:
            continue
        holdings.append(
            TokenHolding(
                mint=info["mint"],
                amount=amount,
                decimals=int(token_amount["decimals"]),
            )
        )
    return holdings


def get_recent_signatures(
    client: Client, address: str, limit: int = 10
) -> list[tuple[str, datetime | None]]:
    pubkey = _parse_pubkey(address)
    resp = client.get_signatures_for_address(pubkey, limit=limit)
    out: list[tuple[str, datetime | None]] = []
    for sig_info in resp.value:
        ts = sig_info.block_time
        dt = datetime.fromtimestamp(ts, tz=timezone.utc) if ts else None
        out.append((str(sig_info.signature), dt))
    return out


def snapshot(client: Client, address: str, tx_limit: int = 10) -> WalletSnapshot:
    return WalletSnapshot(
        address=address,
        sol_balance=get_sol_balance(client, address),
        tokens=get_token_holdings(client, address),
        recent_signatures=get_recent_signatures(client, address, tx_limit),
    )
