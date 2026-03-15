"""Ingest pipeline orchestration."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from receipt_index.extraction import extract_metadata
from receipt_index.renderer import render_pdf
from receipt_index.repository import (
    get_processed_source_ids,
    insert_ingest_log,
    insert_receipt,
)

if TYPE_CHECKING:
    import psycopg
    from pydantic_ai import Agent

    from receipt_index.adapters.base import SourceAdapter
    from receipt_index.models import Receipt, ReceiptMetadata
    from receipt_index.store import FileStore

logger = logging.getLogger(__name__)


@dataclass
class IngestResult:
    """Summary of an ingest run."""

    processed: int = 0
    skipped: int = 0
    failed: int = 0
    receipts: list[Receipt] = field(default_factory=list)


def run_ingest(
    *,
    conn: psycopg.Connection[dict[str, Any]],
    adapter: SourceAdapter,
    store: FileStore,
    agent: Agent[None, ReceiptMetadata] | None = None,
    dry_run: bool = False,
    limit: int | None = None,
) -> IngestResult:
    """Orchestrate the receipt ingestion pipeline.

    Fetches unprocessed messages from the adapter, extracts metadata,
    renders PDFs, saves to the file store, and inserts into the database.
    """
    result = IngestResult()
    processed_ids = get_processed_source_ids(conn)

    count = 0
    for raw in adapter.fetch_unprocessed(processed_ids):
        if limit is not None and count >= limit:
            break
        count += 1

        if dry_run:
            logger.info("Dry run: would process %s", raw.source_id)
            result.skipped += 1
            continue

        try:
            metadata = extract_metadata(raw, agent=agent)
            pdf_data = render_pdf(raw)
            pdf_path = store.save(
                metadata.date, metadata.vendor, metadata.amount, pdf_data
            )
            receipt = insert_receipt(
                conn,
                source_id=raw.source_id,
                source_type="imap",
                vendor=metadata.vendor,
                amount=metadata.amount,
                currency=metadata.currency,
                receipt_date=metadata.date,
                description=metadata.description,
                confidence=metadata.confidence,
                pdf_path=pdf_path,
                email_subject=raw.subject,
                email_sender=raw.sender,
                email_date=raw.date,
            )
            result.processed += 1
            result.receipts.append(receipt)
            insert_ingest_log(
                conn,
                source_id=raw.source_id,
                source_type="imap",
                status="success",
                receipt_id=receipt.id,
                vendor=metadata.vendor,
                amount=metadata.amount,
                email_subject=raw.subject,
                email_sender=raw.sender,
                email_date=raw.date,
            )
            logger.info(
                "Processed receipt: %s (%s) confidence=%.2f",
                metadata.vendor,
                receipt.id,
                metadata.confidence,
            )
        except Exception as exc:
            try:
                insert_ingest_log(
                    conn,
                    source_id=raw.source_id,
                    source_type="imap",
                    status="failed",
                    email_subject=raw.subject,
                    email_sender=raw.sender,
                    email_date=raw.date,
                    error_message=str(exc),
                )
            except Exception:
                logger.warning(
                    "Failed to write ingest log for %s",
                    raw.source_id,
                    exc_info=True,
                )
            logger.warning(
                "Failed to process message %s (subject=%s, sender=%s)",
                raw.source_id,
                raw.subject,
                raw.sender,
                exc_info=True,
            )
            result.failed += 1

    return result
