"""Shared test fixtures."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

import pytest

from receipt_index.config import ImapConfig
from receipt_index.models import RawReceipt

if TYPE_CHECKING:
    from pathlib import Path


@pytest.fixture
def store_root(tmp_path: Path) -> Path:
    """Provide a temporary directory as the file store root."""
    root = tmp_path / "receipts"
    root.mkdir()
    return root


@pytest.fixture
def imap_config() -> ImapConfig:
    """Provide a test IMAP configuration."""
    return ImapConfig(
        host="imap.example.com",
        username="test@example.com",
        password="secret",  # pragma: allowlist secret
        port=993,
        folder="INBOX",
    )


@pytest.fixture
def sample_raw_receipt() -> RawReceipt:
    """Provide a minimal RawReceipt for extraction and renderer tests."""
    return RawReceipt(
        source_id="<test-123@example.com>",
        subject="Your Amazon.com order",
        sender="no-reply@amazon.com",
        date=datetime(2025, 6, 15, 10, 30, 0, tzinfo=UTC),
        text_body="Order Total: $42.99\nItem: Python Cookbook",
    )
