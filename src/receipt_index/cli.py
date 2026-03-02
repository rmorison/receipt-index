"""CLI entry point for receipt-index."""

from __future__ import annotations

import json
import logging
import sys
from typing import TYPE_CHECKING
from uuid import UUID

import click

if TYPE_CHECKING:
    from datetime import datetime
    from decimal import Decimal


@click.group()
def cli() -> None:
    """Receipt Search Index — find receipts fast."""
    from receipt_index.config import get_log_level

    logging.basicConfig(
        level=getattr(logging, get_log_level(), logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )


@cli.command()
@click.option("--dry-run", is_flag=True, help="Preview without processing.")
@click.option("--limit", type=int, default=None, help="Max messages to process.")
def ingest(dry_run: bool, limit: int | None) -> None:
    """Ingest receipts from configured sources."""
    from receipt_index.adapters.imap import ImapAdapter
    from receipt_index.config import get_imap_config, get_store_path
    from receipt_index.db import get_connection
    from receipt_index.pipeline import run_ingest
    from receipt_index.store import LocalFileStore

    adapter = ImapAdapter(get_imap_config())
    store = LocalFileStore(get_store_path())

    with get_connection() as conn:
        result = run_ingest(
            conn=conn,
            adapter=adapter,
            store=store,
            dry_run=dry_run,
            limit=limit,
        )

    click.echo(
        f"Processed: {result.processed}  "
        f"Skipped: {result.skipped}  "
        f"Failed: {result.failed}"
    )

    if result.failed > 0:
        sys.exit(1)


@cli.command()
@click.option("--vendor", default=None, help="Filter by vendor name (substring).")
@click.option("--amount", default=None, help="Filter by exact amount.")
@click.option("--amount-min", default=None, help="Filter by minimum amount.")
@click.option("--amount-max", default=None, help="Filter by maximum amount.")
@click.option(
    "--date-from",
    type=click.DateTime(formats=["%Y-%m-%d"]),
    default=None,
    help="Filter by start date (YYYY-MM-DD).",
)
@click.option(
    "--date-to",
    type=click.DateTime(formats=["%Y-%m-%d"]),
    default=None,
    help="Filter by end date (YYYY-MM-DD).",
)
@click.option(
    "--output",
    "output_format",
    type=click.Choice(["text", "json"]),
    default="text",
    help="Output format.",
)
def search(
    vendor: str | None,
    amount: str | None,
    amount_min: str | None,
    amount_max: str | None,
    date_from: datetime | None,
    date_to: datetime | None,
    output_format: str,
) -> None:
    """Search indexed receipts."""
    from decimal import Decimal, InvalidOperation

    from receipt_index.db import get_connection
    from receipt_index.repository import search_receipts

    def _to_decimal(value: str | None, name: str) -> Decimal | None:
        if value is None:
            return None
        try:
            return Decimal(value)
        except InvalidOperation:
            msg = f"Invalid decimal value for {name}: {value}"
            raise click.BadParameter(msg) from None

    amount_d = _to_decimal(amount, "--amount")
    amount_min_d = _to_decimal(amount_min, "--amount-min")
    amount_max_d = _to_decimal(amount_max, "--amount-max")

    with get_connection() as conn:
        results = search_receipts(
            conn,
            vendor=vendor,
            amount=amount_d,
            amount_min=amount_min_d,
            amount_max=amount_max_d,
            date_from=date_from.date() if date_from else None,
            date_to=date_to.date() if date_to else None,
        )

    if output_format == "json":
        data = [r.model_dump(mode="json") for r in results]
        click.echo(json.dumps(data, indent=2, default=str))
    else:
        if not results:
            click.echo("No receipts found.")
            return
        click.echo(f"{'ID':<38} {'Date':<12} {'Vendor':<20} {'Amount':>10}")
        click.echo("-" * 82)
        for r in results:
            click.echo(
                f"{r.id!s:<38} "
                f"{r.receipt_date.isoformat():<12} "
                f"{r.vendor:<20} "
                f"{r.amount!s:>10}"
            )
        click.echo(f"\n{len(results)} receipt(s) found.")


@cli.command()
@click.argument("receipt_id")
@click.option(
    "--output",
    "output_format",
    type=click.Choice(["text", "json"]),
    default="text",
    help="Output format.",
)
def show(receipt_id: str, output_format: str) -> None:
    """Show details for a specific receipt."""
    from receipt_index.db import get_connection
    from receipt_index.repository import get_receipt_by_id

    try:
        uid = UUID(receipt_id)
    except ValueError:
        click.echo(f"Error: invalid UUID: {receipt_id}", err=True)
        sys.exit(1)

    with get_connection() as conn:
        receipt = get_receipt_by_id(conn, uid)

    if receipt is None:
        click.echo(f"Receipt not found: {receipt_id}")
        sys.exit(1)

    if output_format == "json":
        click.echo(receipt.model_dump_json(indent=2))
    else:
        click.echo(f"ID:           {receipt.id}")
        click.echo(f"Vendor:       {receipt.vendor}")
        click.echo(f"Amount:       {receipt.amount} {receipt.currency}")
        click.echo(f"Date:         {receipt.receipt_date}")
        click.echo(f"Description:  {receipt.description or '—'}")
        click.echo(f"Confidence:   {receipt.confidence}")
        click.echo(f"PDF:          {receipt.pdf_path}")
        click.echo(f"Source:       {receipt.source_type} ({receipt.source_id})")
        if receipt.email_subject:
            click.echo(f"Subject:      {receipt.email_subject}")
        if receipt.email_sender:
            click.echo(f"Sender:       {receipt.email_sender}")
        if receipt.email_date:
            click.echo(f"Email Date:   {receipt.email_date.isoformat()}")
