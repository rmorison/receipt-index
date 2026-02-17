"""Shared test fixtures."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from pathlib import Path


@pytest.fixture
def store_root(tmp_path: Path) -> Path:
    """Provide a temporary directory as the file store root."""
    root = tmp_path / "receipts"
    root.mkdir()
    return root
