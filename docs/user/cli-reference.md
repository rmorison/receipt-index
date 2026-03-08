# CLI Reference

## Commands

- [`receipt-index ingest`](#ingest) — Fetch and process receipts from email
- [`receipt-index search`](#search) — Find receipts by metadata
- [`receipt-index show`](#show) — View full details for a receipt

All commands require a configured `.env` file (see [Getting Started](getting-started.md)).

---

## ingest

Fetch unprocessed receipts from the configured IMAP folder, extract metadata using an LLM, render PDFs, and store everything in the database and file store.

```bash
receipt-index ingest [OPTIONS]
```

### Options

| Option | Description |
|---|---|
| `--dry-run` | Preview what would be processed without making any changes |
| `--limit N` | Process at most N messages |

### Examples

```bash
# Preview what will be ingested
receipt-index ingest --dry-run

# Ingest the next 10 unprocessed messages
receipt-index ingest --limit 10

# Ingest all unprocessed messages
receipt-index ingest
```

### How It Works

1. Connects to your IMAP server and fetches messages from the configured folder
2. Skips messages already ingested (tracked by message ID for idempotency)
3. For each new message:
   - Sends the email content to Claude Haiku to extract vendor, amount, date, and description
   - If the LLM confidence is too low, the message is skipped (not a receipt)
   - Renders the email as a PDF (using Playwright headless Chromium, with weasyprint fallback)
   - Stores the metadata in PostgreSQL and the PDF in the file store
4. Reports processed/skipped/failed counts

Re-running `ingest` is safe — previously processed messages are automatically skipped.

---

## search

Query indexed receipts by vendor, amount, date, or any combination.

```bash
receipt-index search [OPTIONS]
```

### Options

| Option | Description |
|---|---|
| `--vendor TEXT` | Filter by vendor name (case-insensitive substring match) |
| `--amount DECIMAL` | Filter by exact amount |
| `--amount-min DECIMAL` | Filter by minimum amount (inclusive) |
| `--amount-max DECIMAL` | Filter by maximum amount (inclusive) |
| `--date-from YYYY-MM-DD` | Filter by start date (inclusive) |
| `--date-to YYYY-MM-DD` | Filter by end date (inclusive) |
| `--output text\|json` | Output format (default: `text`) |

Note: `--amount` cannot be combined with `--amount-min`/`--amount-max`.

### Examples

```bash
# Find all Amazon receipts
receipt-index search --vendor amazon

# Find receipts between $50 and $200
receipt-index search --amount-min 50 --amount-max 200

# Find receipts from January 2026
receipt-index search --date-from 2026-01-01 --date-to 2026-01-31

# Combine filters: vendor + date range
receipt-index search --vendor "whole foods" --date-from 2026-01-01

# Find an exact amount (useful for reconciliation)
receipt-index search --amount 47.99

# Output as JSON for scripting
receipt-index search --vendor amazon --output json
```

### Text Output

The default text output shows a table:

```
ID                                     Date         Vendor               Amount
----------------------------------------------------------------------------------
01942a3b-...                           2026-01-15   Amazon               47.99
01942a3c-...                           2026-01-22   Amazon Web Services  129.00

2 receipt(s) found.
```

### JSON Output

Use `--output json` for machine-readable output:

```json
[
  {
    "id": "01942a3b-...",
    "vendor": "Amazon",
    "amount": "47.99",
    "currency": "USD",
    "receipt_date": "2026-01-15",
    "pdf_path": "2026/01/2026-01-15__amazon__47.99.pdf",
    ...
  }
]
```

---

## show

Display full details for a specific receipt by its ID.

```bash
receipt-index show RECEIPT_ID [OPTIONS]
```

### Options

| Option | Description |
|---|---|
| `--output text\|json` | Output format (default: `text`) |

### Examples

```bash
# Show receipt details
receipt-index show 01942a3b-1234-7def-8abc-567890abcdef

# Show as JSON
receipt-index show 01942a3b-1234-7def-8abc-567890abcdef --output json
```

### Text Output

```
ID:           01942a3b-1234-7def-8abc-567890abcdef
Vendor:       Amazon
Amount:       47.99 USD
Date:         2026-01-15
Description:  Order #123-4567890 - Wireless keyboard
Confidence:   0.95
PDF:          2026/01/2026-01-15__amazon__47.99.pdf
Source:       imap (msg-id-12345@mail.example.com)
Subject:      Your Amazon.com order has shipped
Sender:       ship-confirm@amazon.com
Email Date:   2026-01-15T10:30:00
```

The `PDF` path is relative to your configured `RECEIPT_STORE_PATH`.

---

## Example Workflows

### Initial Bulk Ingest

When first setting up, ingest all existing receipts:

```bash
# Preview first
receipt-index ingest --dry-run

# Ingest in batches to monitor progress
receipt-index ingest --limit 50
receipt-index ingest --limit 50
# ... repeat until all processed

# Or ingest everything at once
receipt-index ingest
```

### Reconciling a Transaction

You have a $47.99 charge from January 2026 and need the receipt:

```bash
# Search by amount and date
receipt-index search --amount 47.99 --date-from 2026-01-01 --date-to 2026-01-31

# Get the full details including PDF location
receipt-index show 01942a3b-1234-7def-8abc-567890abcdef
```

The PDF is at `$RECEIPT_STORE_PATH/2026/01/2026-01-15__amazon__47.99.pdf`.

### Finding All Receipts from a Vendor

```bash
receipt-index search --vendor "whole foods" --date-from 2026-01-01 --date-to 2026-03-31
```

### Exporting Search Results

Pipe JSON output to other tools:

```bash
# Save search results to a file
receipt-index search --vendor amazon --output json > amazon-receipts.json

# Count receipts per vendor with jq
receipt-index search --date-from 2026-01-01 --output json | jq 'group_by(.vendor) | map({vendor: .[0].vendor, count: length})'

# Sum amounts with jq
receipt-index search --vendor amazon --output json | jq '[.[].amount | tonumber] | add'
```

### Weekly Ingestion

Run periodically to pick up new receipts:

```bash
receipt-index ingest
```

Previously ingested messages are skipped automatically, so this is safe to run on a schedule.
