"""Tests for receipt_index.cli."""

from __future__ import annotations

import json
from datetime import UTC, date, datetime
from decimal import Decimal
from typing import Any
from unittest.mock import MagicMock, patch
from uuid import UUID

from click.testing import CliRunner

from receipt_index.cli import cli
from receipt_index.models import Receipt
from receipt_index.pipeline import IngestResult

_RECEIPT_ROW: dict[str, Any] = {
    "id": UUID("019572a0-0000-7000-8000-000000000001"),
    "source_id": "<msg-1@example.com>",
    "source_type": "imap",
    "vendor": "Amazon",
    "amount": Decimal("42.99"),
    "currency": "USD",
    "receipt_date": date(2025, 6, 15),
    "description": "Python Cookbook",
    "confidence": 0.95,
    "pdf_path": "2025/06/2025-06-15__amazon__42.99.pdf",
    "email_subject": "Your Amazon.com order",
    "email_sender": "no-reply@amazon.com",
    "email_date": datetime(2025, 6, 15, 10, 30, 0, tzinfo=UTC),
    "created_at": datetime(2025, 6, 15, 12, 0, 0, tzinfo=UTC),
    "updated_at": datetime(2025, 6, 15, 12, 0, 0, tzinfo=UTC),
}

_SAMPLE_RECEIPT = Receipt.model_validate(_RECEIPT_ROW)


class TestIngestCommand:
    """Tests for the ingest CLI command."""

    @patch("receipt_index.pipeline.run_ingest")
    @patch("receipt_index.db.get_connection")
    @patch("receipt_index.store.LocalFileStore")
    @patch("receipt_index.config.get_store_path")
    @patch("receipt_index.adapters.imap.ImapAdapter")
    @patch("receipt_index.config.get_imap_config")
    def test_ingest_success(
        self,
        mock_imap_config: MagicMock,
        mock_adapter_cls: MagicMock,
        mock_store_path: MagicMock,
        mock_store_cls: MagicMock,
        mock_get_conn: MagicMock,
        mock_run: MagicMock,
    ) -> None:
        mock_run.return_value = IngestResult(processed=3, skipped=0, failed=0)
        runner = CliRunner()
        result = runner.invoke(cli, ["ingest"])
        assert result.exit_code == 0
        assert "Processed: 3" in result.output

    @patch("receipt_index.pipeline.run_ingest")
    @patch("receipt_index.db.get_connection")
    @patch("receipt_index.store.LocalFileStore")
    @patch("receipt_index.config.get_store_path")
    @patch("receipt_index.adapters.imap.ImapAdapter")
    @patch("receipt_index.config.get_imap_config")
    def test_ingest_dry_run_passes_flag(
        self,
        mock_imap_config: MagicMock,
        mock_adapter_cls: MagicMock,
        mock_store_path: MagicMock,
        mock_store_cls: MagicMock,
        mock_get_conn: MagicMock,
        mock_run: MagicMock,
    ) -> None:
        mock_run.return_value = IngestResult(skipped=5)
        runner = CliRunner()
        result = runner.invoke(cli, ["ingest", "--dry-run"])
        assert result.exit_code == 0
        _, kwargs = mock_run.call_args
        assert kwargs["dry_run"] is True

    @patch("receipt_index.pipeline.run_ingest")
    @patch("receipt_index.db.get_connection")
    @patch("receipt_index.store.LocalFileStore")
    @patch("receipt_index.config.get_store_path")
    @patch("receipt_index.adapters.imap.ImapAdapter")
    @patch("receipt_index.config.get_imap_config")
    def test_ingest_limit_passes_value(
        self,
        mock_imap_config: MagicMock,
        mock_adapter_cls: MagicMock,
        mock_store_path: MagicMock,
        mock_store_cls: MagicMock,
        mock_get_conn: MagicMock,
        mock_run: MagicMock,
    ) -> None:
        mock_run.return_value = IngestResult(processed=3)
        runner = CliRunner()
        result = runner.invoke(cli, ["ingest", "--limit", "3"])
        assert result.exit_code == 0
        _, kwargs = mock_run.call_args
        assert kwargs["limit"] == 3

    @patch("receipt_index.pipeline.run_ingest")
    @patch("receipt_index.db.get_connection")
    @patch("receipt_index.store.LocalFileStore")
    @patch("receipt_index.config.get_store_path")
    @patch("receipt_index.adapters.imap.ImapAdapter")
    @patch("receipt_index.config.get_imap_config")
    def test_ingest_exits_1_on_failures(
        self,
        mock_imap_config: MagicMock,
        mock_adapter_cls: MagicMock,
        mock_store_path: MagicMock,
        mock_store_cls: MagicMock,
        mock_get_conn: MagicMock,
        mock_run: MagicMock,
    ) -> None:
        mock_run.return_value = IngestResult(processed=1, failed=2)
        runner = CliRunner()
        result = runner.invoke(cli, ["ingest"])
        assert result.exit_code != 0


class TestSearchCommand:
    """Tests for the search CLI command."""

    @patch("receipt_index.repository.search_receipts", return_value=[_SAMPLE_RECEIPT])
    @patch("receipt_index.db.get_connection")
    def test_search_vendor_filter(
        self,
        mock_conn: MagicMock,
        mock_search: MagicMock,
    ) -> None:
        runner = CliRunner()
        result = runner.invoke(cli, ["search", "--vendor", "amazon"])
        assert result.exit_code == 0
        _, kwargs = mock_search.call_args
        assert kwargs["vendor"] == "amazon"

    @patch("receipt_index.repository.search_receipts", return_value=[_SAMPLE_RECEIPT])
    @patch("receipt_index.db.get_connection")
    def test_search_json_output(
        self,
        mock_conn: MagicMock,
        mock_search: MagicMock,
    ) -> None:
        runner = CliRunner()
        result = runner.invoke(cli, ["search", "--output", "json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]["vendor"] == "Amazon"

    @patch("receipt_index.repository.search_receipts", return_value=[_SAMPLE_RECEIPT])
    @patch("receipt_index.db.get_connection")
    def test_search_text_has_table_headers(
        self,
        mock_conn: MagicMock,
        mock_search: MagicMock,
    ) -> None:
        runner = CliRunner()
        result = runner.invoke(cli, ["search"])
        assert result.exit_code == 0
        assert "ID" in result.output
        assert "Date" in result.output
        assert "Vendor" in result.output
        assert "Amount" in result.output
        assert "Amazon" in result.output

    @patch("receipt_index.repository.search_receipts", return_value=[])
    @patch("receipt_index.db.get_connection")
    def test_search_no_results(
        self,
        mock_conn: MagicMock,
        mock_search: MagicMock,
    ) -> None:
        runner = CliRunner()
        result = runner.invoke(cli, ["search"])
        assert result.exit_code == 0
        assert "No receipts found" in result.output

    @patch("receipt_index.repository.search_receipts", return_value=[_SAMPLE_RECEIPT])
    @patch("receipt_index.db.get_connection")
    def test_search_amount_range(
        self,
        mock_conn: MagicMock,
        mock_search: MagicMock,
    ) -> None:
        runner = CliRunner()
        result = runner.invoke(
            cli, ["search", "--amount-min", "10", "--amount-max", "100"]
        )
        assert result.exit_code == 0
        _, kwargs = mock_search.call_args
        assert kwargs["amount_min"] == Decimal("10")
        assert kwargs["amount_max"] == Decimal("100")


class TestShowCommand:
    """Tests for the show CLI command."""

    @patch("receipt_index.repository.get_receipt_by_id", return_value=_SAMPLE_RECEIPT)
    @patch("receipt_index.db.get_connection")
    def test_show_text_output(
        self,
        mock_conn: MagicMock,
        mock_get: MagicMock,
    ) -> None:
        runner = CliRunner()
        result = runner.invoke(cli, ["show", "019572a0-0000-7000-8000-000000000001"])
        assert result.exit_code == 0
        assert "Amazon" in result.output
        assert "42.99" in result.output

    @patch("receipt_index.repository.get_receipt_by_id", return_value=_SAMPLE_RECEIPT)
    @patch("receipt_index.db.get_connection")
    def test_show_json_output(
        self,
        mock_conn: MagicMock,
        mock_get: MagicMock,
    ) -> None:
        runner = CliRunner()
        result = runner.invoke(
            cli,
            ["show", "019572a0-0000-7000-8000-000000000001", "--output", "json"],
        )
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert data["vendor"] == "Amazon"

    def test_show_invalid_uuid(self) -> None:
        runner = CliRunner()
        result = runner.invoke(cli, ["show", "not-a-uuid"])
        assert result.exit_code != 0

    @patch("receipt_index.repository.get_receipt_by_id", return_value=None)
    @patch("receipt_index.db.get_connection")
    def test_show_not_found(
        self,
        mock_conn: MagicMock,
        mock_get: MagicMock,
    ) -> None:
        runner = CliRunner()
        result = runner.invoke(cli, ["show", "019572a0-0000-7000-8000-000000000099"])
        assert result.exit_code != 0
        assert "not found" in result.output
