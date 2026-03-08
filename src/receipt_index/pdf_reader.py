"""PDF text extraction with pdfplumber and Claude vision fallback."""

from __future__ import annotations

import logging
from typing import Any

from pydantic_ai import Agent, BinaryContent

from receipt_index.config import get_anthropic_api_key, get_llm_model

logger = logging.getLogger(__name__)

# Minimum non-whitespace characters to consider pdfplumber output valid.
# A minimal receipt must contain at least a vendor name and amount; 20 chars
# provides a buffer while catching truly empty extractions from image-only PDFs.
_MIN_TEXT_LENGTH = 20

_VISION_SYSTEM_PROMPT = """\
You are a document text extractor. Given a PDF document, extract ALL visible \
text content exactly as it appears. Include:
- All amounts, prices, and totals (preserve exact formatting)
- All dates
- Vendor/merchant names
- Line items and descriptions
- Any other readable text

Return the raw text content only. Do not add commentary or formatting.\
"""


def extract_text(
    pdf_bytes: bytes,
    *,
    vision_agent: Agent[None, str] | None = None,
) -> str:
    """Extract text from PDF bytes.

    Strategy:
    1. Try pdfplumber for text-based PDFs (fast, no API call)
    2. Fall back to Claude vision for scanned/image PDFs

    Args:
        pdf_bytes: Raw PDF file content.
        vision_agent: Optional pydantic-ai Agent for vision fallback
                      (injected in tests).

    Returns:
        Extracted text content, or empty string if extraction fails.
    """
    text = _extract_with_pdfplumber(pdf_bytes)
    if _is_sufficient_text(text):
        logger.debug("pdfplumber extracted %d chars from PDF", len(text))
        return text

    logger.info(
        "pdfplumber extracted insufficient text (%d chars), "
        "falling back to Claude vision",
        len(text.strip()),
    )
    return _extract_with_vision(pdf_bytes, agent=vision_agent)


def create_vision_agent() -> Agent[None, str]:
    """Create a pydantic-ai Agent configured for PDF text extraction."""
    get_anthropic_api_key()  # Fail fast if missing
    model_name = get_llm_model()
    return Agent(
        f"anthropic:{model_name}",
        output_type=str,
        system_prompt=_VISION_SYSTEM_PROMPT,
    )


def _extract_with_pdfplumber(pdf_bytes: bytes) -> str:
    """Extract text from PDF using pdfplumber."""
    import io

    import pdfplumber

    try:
        with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
            pages = [page.extract_text() or "" for page in pdf.pages]
        return "\n\n".join(pages).strip()
    except Exception:
        logger.warning("pdfplumber failed to process PDF", exc_info=True)
        return ""


def _is_sufficient_text(text: str) -> bool:
    """Check if extracted text meets the minimum quality threshold."""
    stripped = "".join(text.split())
    return len(stripped) >= _MIN_TEXT_LENGTH


def _extract_with_vision(
    pdf_bytes: bytes,
    *,
    agent: Agent[None, str] | None = None,
) -> str:
    """Extract text from PDF using Claude vision API."""
    if agent is None:
        agent = create_vision_agent()

    try:
        result: Any = agent.run_sync(
            [
                "Extract all text content from this PDF document.",
                BinaryContent(data=pdf_bytes, media_type="application/pdf"),
            ]
        )
        return result.output  # type: ignore[no-any-return]
    except Exception:
        logger.warning("Vision extraction failed for PDF", exc_info=True)
        return ""
