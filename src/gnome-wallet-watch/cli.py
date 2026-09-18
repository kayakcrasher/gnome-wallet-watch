"""CLI entrypoint. `gnome-watch <address>`"""
from __future__ import annotations

import typer
from rich.console import Console
from rich.table import Table

from .client import get_client
from .wallet import snapshot

app = typer.Typer(add_completion=False, help="Inspect any Solana wallet.")
console = Console()


@app.command()
def main(
    address: str = typer.Argument(..., help="Solana wallet address (base58)."),
    tx_limit: int = typer.Option(10, "--txs", "-t", help="How many recent txs to show."),
) -> None:
    client = get_client()

    with console.status("[bold green]Fetching wallet data..."):
        try:
            snap = snapshot(client, address, tx_limit=tx_limit)
        except ValueError as exc:
            console.print(f"[red]{exc}[/red]")
            raise typer.Exit(code=1)

    console.print(f"\n[bold cyan]Wallet:[/bold cyan] {snap.address}")
    console.print(f"[bold cyan]SOL:[/bold cyan]    {snap.sol_balance:.4f}\n")

    if snap.tokens:
        table = Table(title="SPL Tokens", show_lines=False)
        table.add_column("Mint", style="magenta", no_wrap=True)
        table.add_column("Amount", justify="right", style="green")
        for t in sorted(snap.tokens, key=lambda x: x.amount, reverse=True):
            table.add_row(t.mint, f"{t.amount:,.4f}")
        console.print(table)
    else:
        console.print("[dim]No SPL token holdings.[/dim]")

    if snap.recent_signatures:
        tx_table = Table(title=f"Recent Transactions (last {len(snap.recent_signatures)})")
        tx_table.add_column("Signature", style="yellow", no_wrap=True)
        tx_table.add_column("Time (UTC)", style="white")
        for sig, dt in snap.recent_signatures:
            short = f"{sig[:8]}...{sig[-8:]}"
            tx_table.add_row(short, dt.strftime("%Y-%m-%d %H:%M:%S") if dt else "unknown")
        console.print(tx_table)
    else:
        console.print("[dim]No recent transactions.[/dim]")


if __name__ == "__main__":
    app()
