# ADR-0004: Playwright for HTML-to-PDF Rendering

## Status

Accepted

## Context

The receipt ingestion pipeline renders email HTML bodies to PDF for archival storage. The current implementation uses weasyprint, a CSS-subset renderer that produces poor-quality output for complex HTML email layouts — text columns pushed off-page, missing prices and line items. For example, a Netflix Shop order confirmation that renders perfectly via a browser's print-to-PDF produces an unreadable weasyprint PDF with only images and no text or pricing.

This only affects emails without PDF attachments. Most receipts already include PDFs and bypass the HTML rendering path entirely. However, for the subset that relies on HTML rendering, the output quality is unacceptable for accounting reconciliation.

Key factors:

- **Root cause**: Weasyprint cannot execute JavaScript and lacks support for modern CSS layouts (flexbox, grid) that email clients use
- **Rendering quality**: A full browser engine produces output identical to what users see in their email client
- **Trade-offs**: Chromium binary adds ~300-400MB to the deployment; cold start is ~1-3 seconds vs ~100ms for weasyprint
- **Volume**: PDF rendering is infrequent (only HTML-only receipts) and not latency-sensitive

## Decision

Use **Playwright with headless Chromium** as the primary HTML-to-PDF renderer. Retain **weasyprint as an optional fallback** for environments where Chromium cannot be installed.

### Backend Selection

A `PDF_RENDERER` environment variable selects the backend:

- `playwright` (default): Use Playwright headless Chromium
- `weasyprint`: Use weasyprint (legacy fallback)
- `auto`: Try Playwright first, fall back to weasyprint on failure

### Architecture

The existing `_html_to_pdf_bytes()` function remains the single chokepoint for all HTML-to-PDF conversion. It dispatches to the selected backend internally, preserving the interface for all callers (`_render_html_to_pdf`, `_render_text_to_pdf`).

## Consequences

### Positive

- **Browser-identical rendering**: Complex HTML email layouts render correctly, preserving all text, pricing, and layout
- **No code changes to callers**: The dispatch is internal to `_html_to_pdf_bytes()`; `render_pdf()`, `_render_html_to_pdf()`, and `_render_text_to_pdf()` are unchanged
- **Configurable**: Teams or environments that cannot install Chromium can set `PDF_RENDERER=weasyprint`
- **Graceful degradation**: `auto` mode provides a safety net during migration

### Negative

- **Heavier dependency**: Chromium binary adds ~300-400MB to the Docker image
- **Slower cold start**: First PDF render launches the browser (~1-3 seconds); acceptable given low volume and batch processing
- **CI complexity**: Test matrix requires `playwright install --with-deps chromium` step
- **System dependencies**: Chromium requires system libraries (libnss3, libatk, etc.) in the Docker image

### Alternatives Considered

- **wkhtmltopdf**: Deprecated, based on an old WebKit fork. Not chosen.
- **Puppeteer (Node.js)**: Would require a Node.js runtime alongside Python. Not chosen.
- **Chrome CDP directly**: Lower-level, more complex API without Playwright's ergonomics. Not chosen.
- **Keep weasyprint only**: Does not solve the rendering quality problem. Not chosen.
