"""LLM-based metadata extraction using pydantic-ai."""

from __future__ import annotations

import logging
from html.parser import HTMLParser
from typing import Any

from pydantic_ai import Agent

from receipt_index.config import get_anthropic_api_key, get_llm_model
from receipt_index.models import RawReceipt, ReceiptMetadata

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = """\
You are a receipt metadata extractor. Given an email that contains or forwards \
a receipt, extract the following fields:

- vendor: The canonical business name (e.g. "Amazon", not "no-reply@amazon.com")
- amount: The total amount charged (numeric, e.g. 42.99)
- currency: ISO 4217 currency code (e.g. "USD", "CAD", "EUR")
- date: The purchase/transaction date (YYYY-MM-DD), NOT the email send date
- description: Brief summary of what was purchased (optional)
- confidence: Your confidence in the extraction from 0.0 to 1.0. \
Use below 0.5 if the email may not be a receipt or key fields are uncertain.

Handle forwarded receipts by looking at the original receipt content. \
For multi-item orders, use the total amount. If the currency is not stated, \
assume USD.\
"""


def create_extraction_agent() -> Agent[None, ReceiptMetadata]:
    """Create a pydantic-ai Agent configured for receipt extraction."""
    # Ensure API key is available (fail fast)
    get_anthropic_api_key()

    model_name = get_llm_model()
    return Agent(
        f"anthropic:{model_name}",
        output_type=ReceiptMetadata,
        system_prompt=_SYSTEM_PROMPT,
    )


def extract_metadata(
    raw: RawReceipt,
    *,
    agent: Agent[None, ReceiptMetadata] | None = None,
) -> ReceiptMetadata:
    """Extract structured metadata from a raw receipt email.

    Accepts an optional agent for dependency injection in tests.
    """
    if agent is None:
        agent = create_extraction_agent()

    prompt = _build_prompt(raw)
    result: Any = agent.run_sync(prompt)
    return result.output  # type: ignore[no-any-return]


def _build_prompt(raw: RawReceipt) -> str:
    """Build the user prompt from raw receipt data."""
    parts = [
        f"Subject: {raw.subject}",
        f"From: {raw.sender}",
        f"Date: {raw.date.isoformat()}",
        "",
        "--- Email Body ---",
    ]

    if raw.text_body:
        parts.append(raw.text_body)
    elif raw.html_body:
        parts.append(_strip_html_tags(raw.html_body))
    else:
        parts.append("(no body content)")

    return "\n".join(parts)


def _strip_html_tags(html: str) -> str:
    """Remove HTML tags, returning only text content."""
    stripper = _HTMLTagStripper()
    stripper.feed(html)
    return stripper.get_text()


class _HTMLTagStripper(HTMLParser):
    """HTMLParser subclass that strips tags and returns text."""

    def __init__(self) -> None:
        super().__init__()
        self._parts: list[str] = []

    def handle_data(self, data: str) -> None:
        self._parts.append(data)

    def handle_entityref(self, name: str) -> None:
        self._parts.append(f"&{name};")

    def handle_charref(self, name: str) -> None:
        self._parts.append(f"&#{name};")

    def get_text(self) -> str:
        return "".join(self._parts)
