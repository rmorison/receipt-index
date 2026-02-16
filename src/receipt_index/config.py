"""Configuration via environment variables."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


def get_database_url() -> str:
    """Return the DATABASE_URL from the environment."""
    url = os.environ.get("DATABASE_URL")
    if not url:
        msg = "DATABASE_URL environment variable is required"
        raise ValueError(msg)
    return url


def get_store_path() -> Path:
    """Return the RECEIPT_STORE_PATH, defaulting to ./data/receipts."""
    return Path(os.environ.get("RECEIPT_STORE_PATH", "./data/receipts"))
