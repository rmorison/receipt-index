# Getting Started

Set up Receipt Search Index from scratch and run your first ingest.

## Prerequisites

- **Python 3.11+** — [python.org](https://www.python.org/downloads/)
- **uv** — [docs.astral.sh/uv](https://docs.astral.sh/uv/) (Python package manager)
- **Docker** and Docker Compose — [docker.com](https://www.docker.com/)
- **golang-migrate** — [github.com/golang-migrate/migrate](https://github.com/golang-migrate/migrate)
- **Anthropic API key** — [console.anthropic.com](https://console.anthropic.com/)
- An IMAP email account with receipts in a designated folder

## 1. Clone and Install

```bash
git clone https://github.com/rmorison/receipt-index.git
cd receipt-index
make setup        # Installs Python deps, Playwright browser, and pre-commit hooks
```

## 2. Start Database

```bash
docker compose up -d    # Starts PostgreSQL 18
make migrate-up         # Applies database schema migrations
```

To verify the database is running:

```bash
docker compose ps
```

## 3. Configure Environment

```bash
cp example.env .env
```

Edit `.env` with your settings. The key variables:

| Variable | Description | Example |
|---|---|---|
| `IMAP_HOST` | Your email server | `imap.gmail.com` |
| `IMAP_PORT` | IMAP port (usually 993 for SSL) | `993` |
| `IMAP_USERNAME` | Email address | `you@example.com` |
| `IMAP_PASSWORD` | App-specific password | (see below) |
| `IMAP_FOLDER` | Folder containing receipts | `INBOX.Receipts` |
| `IMAP_USE_SSL` | Use SSL connection | `true` |
| `ANTHROPIC_API_KEY` | Your Anthropic API key | `sk-ant-...` |
| `DATABASE_URL` | PostgreSQL connection string | (default works with Docker) |
| `RECEIPT_STORE_PATH` | Where PDFs are saved | `./data/receipts` |

The `DATABASE_URL`, `MIGRATION_DATABASE_URL`, `PLAYWRIGHT_BROWSERS_PATH`, and Docker port variables can generally be left at their defaults.

### Email App-Specific Passwords

Most email providers require an app-specific password rather than your main account password:

- **Gmail**: [Create an app password](https://support.google.com/accounts/answer/185833) (requires 2FA enabled)
- **Other providers**: Check your provider's documentation for IMAP access and app-specific passwords

## 4. Set Up Your Email Folder

Create a dedicated folder in your email client for receipts (e.g., `Receipts` or `INBOX.Receipts`). Move or copy receipt emails into this folder. The tool will ingest all messages from this folder.

Set the `IMAP_FOLDER` variable in your `.env` to match the folder path. Folder naming varies by provider:

- **Gmail**: `[Gmail]/Receipts` or a label name
- **Most IMAP servers**: `INBOX.Receipts` or `Receipts`

Check your email client's folder list if unsure of the exact path.

## 5. First Ingest

Preview what will be processed without making changes:

```bash
receipt-index ingest --dry-run
```

When you're satisfied, run a small batch first:

```bash
receipt-index ingest --limit 5
```

Then ingest everything:

```bash
receipt-index ingest
```

You'll see output like:

```
Processed: 12  Skipped: 3  Failed: 0
```

- **Processed**: Receipts successfully indexed with metadata extracted and PDFs generated
- **Skipped**: Messages that didn't look like receipts (low LLM confidence)
- **Failed**: Messages that encountered errors during processing

## 6. Search Your Receipts

```bash
receipt-index search --vendor amazon
```

See the [CLI Reference](cli-reference.md) for all search options and more examples.

## Next Steps

- [CLI Reference](cli-reference.md) — Full command documentation and example workflows
- [Troubleshooting](troubleshooting.md) — Common issues and solutions
