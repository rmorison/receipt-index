"""CLI entry point for receipt-index."""

from __future__ import annotations

import click


@click.group()
def cli() -> None:
    """Receipt Search Index — find receipts fast."""


@cli.command()
def ingest() -> None:
    """Ingest receipts from configured sources."""
    click.echo("Ingest not yet implemented.")


@cli.command()
def search() -> None:
    """Search indexed receipts."""
    click.echo("Search not yet implemented.")


@cli.command()
def show() -> None:
    """Show details for a specific receipt."""
    click.echo("Show not yet implemented.")
