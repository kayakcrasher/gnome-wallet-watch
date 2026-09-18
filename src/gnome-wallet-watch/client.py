"""Solana RPC connection handling."""
from __future__ import annotations

import os

from dotenv import load_dotenv
from solana.rpc.api import Client

load_dotenv()

DEFAULT_RPC = "https://api.mainnet-beta.solana.com"


def get_client() -> Client:
    """Return a Solana RPC client using SOLANA_RPC_URL from .env if set."""
    url = os.getenv("SOLANA_RPC_URL", DEFAULT_RPC)
    return Client(url)
