"""Configuration via environment variables."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class ImapConfig:
    """IMAP connection configuration."""

    host: str
    username: str
    password: str
    port: int = 993
    folder: str = "INBOX"


def get_database_url() -> str:
    """Return the DATABASE_URL from the environment."""
    url = os.environ.get("DATABASE_URL")
    if not url:
        msg = "DATABASE_URL environment variable is required"
        raise ValueError(msg)
    return url


def get_store_path() -> Path:
    """Return the RECEIPT_STORE_PATH, defaulting to ./data/receipts.

    Always resolves to an absolute path to avoid issues if the
    working directory changes during execution.
    """
    return Path(os.environ.get("RECEIPT_STORE_PATH", "./data/receipts")).resolve()


def get_imap_config() -> ImapConfig:
    """Build IMAP configuration from environment variables.

    Required: IMAP_HOST, IMAP_USERNAME, IMAP_PASSWORD
    Optional: IMAP_PORT (default 993), IMAP_FOLDER (default INBOX)
    """
    host = os.environ.get("IMAP_HOST")
    username = os.environ.get("IMAP_USERNAME")
    password = os.environ.get("IMAP_PASSWORD")

    missing = []
    if not host:
        missing.append("IMAP_HOST")
    if not username:
        missing.append("IMAP_USERNAME")
    if not password:
        missing.append("IMAP_PASSWORD")

    if missing:
        msg = f"Required environment variables not set: {', '.join(missing)}"
        raise ValueError(msg)

    port_str = os.environ.get("IMAP_PORT", "993")
    port = int(port_str)

    folder = os.environ.get("IMAP_FOLDER", "INBOX")

    return ImapConfig(
        host=host,  # type: ignore[arg-type]
        username=username,  # type: ignore[arg-type]
        password=password,  # type: ignore[arg-type]
        port=port,
        folder=folder,
    )


def get_anthropic_api_key() -> str:
    """Return the ANTHROPIC_API_KEY from the environment."""
    key = os.environ.get("ANTHROPIC_API_KEY")
    if not key:
        msg = "ANTHROPIC_API_KEY environment variable is required"
        raise ValueError(msg)
    return key


def get_llm_model() -> str:
    """Return the LLM model identifier.

    Defaults to claude-haiku-4-5-20251001.
    """
    return os.environ.get("LLM_MODEL", "claude-haiku-4-5-20251001")
