"""Email-to-PDF rendering."""

from __future__ import annotations

import base64
import html
import logging
import os
import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from receipt_index.models import Attachment, RawReceipt

logger = logging.getLogger(__name__)


PLAIN_TEXT_TEMPLATE = """\
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  body {{ font-family: monospace; font-size: 12px; margin: 2em; }}
  .header {{ border-bottom: 1px solid #ccc; padding-bottom: 1em; margin-bottom: 1em; }}
  .header p {{ margin: 0.2em 0; }}
  pre {{ white-space: pre-wrap; word-wrap: break-word; }}
</style>
</head>
<body>
<div class="header">
  <p><strong>Subject:</strong> {subject}</p>
  <p><strong>From:</strong> {sender}</p>
  <p><strong>Date:</strong> {date}</p>
</div>
<pre>{body}</pre>
</body>
</html>
"""


def render_pdf(raw: RawReceipt) -> bytes:
    """Render a RawReceipt to PDF bytes.

    Strategy (in order of preference):
    1. If a PDF attachment exists, return it directly
    2. If HTML body exists, render via Playwright (fallback: weasyprint)
    3. If text body exists, wrap in HTML template and render via weasyprint
    4. Render a minimal page with just the email headers via weasyprint
    """
    # 1. PDF attachment pass-through
    pdf_data = _find_pdf_attachment(raw.attachments)
    if pdf_data is not None:
        return pdf_data

    # 2. HTML body rendering (Playwright for complex email CSS)
    if raw.html_body:
        return _render_html_to_pdf(raw.html_body, raw.attachments)

    # 3. Text body rendering (weasyprint is fine for simple templates)
    if raw.text_body:
        return _render_text_to_pdf(raw)

    # 4. Minimal fallback — headers only
    return _render_text_to_pdf(raw)


def _find_pdf_attachment(attachments: list[Attachment]) -> bytes | None:
    """Return the data of the first PDF attachment, or None."""
    for att in attachments:
        if att.content_type.lower() == "application/pdf":
            return att.data
    return None


def _render_html_to_pdf(html_content: str, attachments: list[Attachment]) -> bytes:
    """Render HTML to PDF, embedding any inline images."""
    html_with_images = _embed_inline_images(html_content, attachments)
    return _html_to_pdf_bytes(html_with_images)


def _embed_inline_images(html_content: str, attachments: list[Attachment]) -> str:
    """Replace cid: references with data: URIs from attachments."""
    attachment_map: dict[str, Attachment] = {}
    for att in attachments:
        if att.content_type.startswith("image/"):
            # Map by filename (which may be the Content-ID)
            attachment_map[att.filename] = att

    if not attachment_map:
        return html_content

    def replace_cid(match: re.Match[str]) -> str:
        cid = match.group(1)
        att = attachment_map.get(cid)
        if att is None:
            return match.group(0)
        b64 = base64.b64encode(att.data).decode("ascii")
        return f"data:{att.content_type};base64,{b64}"

    return re.sub(r"cid:([^\s\"'>]+)", replace_cid, html_content)


def _render_text_to_pdf(raw: RawReceipt) -> bytes:
    """Wrap text body in HTML template and render to PDF."""
    body = html.escape(raw.text_body or "(no body content)")
    rendered = PLAIN_TEXT_TEMPLATE.format(
        subject=html.escape(raw.subject),
        sender=html.escape(raw.sender),
        date=html.escape(raw.date.isoformat()),
        body=body,
    )
    return _html_to_pdf_weasyprint(rendered)


def _html_to_pdf_bytes(html_content: str) -> bytes:
    """Convert HTML string to PDF bytes.

    Tries Playwright (browser-quality rendering) first, falls back to
    weasyprint if Chromium is not installed.
    """
    try:
        return _html_to_pdf_playwright(html_content)
    except ImportError:
        logger.debug(
            "Playwright not installed, falling back to weasyprint", exc_info=True
        )
    except Exception:
        logger.warning(
            "Playwright rendering failed, falling back to weasyprint", exc_info=True
        )
    return _html_to_pdf_weasyprint(html_content)


def _html_to_pdf_playwright(html_content: str) -> bytes:
    """Convert HTML string to PDF bytes via Playwright headless Chromium."""
    from playwright.sync_api import sync_playwright

    # Ensure PLAYWRIGHT_BROWSERS_PATH is set for local installs
    if "PLAYWRIGHT_BROWSERS_PATH" not in os.environ:
        os.environ["PLAYWRIGHT_BROWSERS_PATH"] = ".playwright"

    with sync_playwright() as p:
        browser = p.chromium.launch()
        try:
            page = browser.new_page()
            page.set_content(html_content, wait_until="domcontentloaded")
            pdf_bytes: bytes = page.pdf(format="Letter")
            return pdf_bytes
        finally:
            browser.close()


def _html_to_pdf_weasyprint(html_content: str) -> bytes:
    """Convert HTML string to PDF bytes via weasyprint."""
    import weasyprint

    doc = weasyprint.HTML(string=html_content)
    return doc.write_pdf()  # type: ignore[no-any-return]
