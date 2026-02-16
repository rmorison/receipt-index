"""Database connection helper."""

from __future__ import annotations

import psycopg
from psycopg.rows import dict_row

from receipt_index.config import get_database_url


def get_connection() -> psycopg.Connection[dict[str, object]]:
    """Create and return a new database connection."""
    return psycopg.connect(get_database_url(), row_factory=dict_row)
