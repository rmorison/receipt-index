# Project Context

## Engineering Standards

This project follows the engineering standards at:
https://github.com/rmorison/engineering-standards

Key standards applied:

- **[Python Standards](https://github.com/rmorison/engineering-standards/blob/main/code/python-standards.md)** — src-layout, uv, ruff, mypy, pytest, pre-commit
- **[Database Standards](https://github.com/rmorison/engineering-standards/blob/main/code/database-standards.md)** — PostgreSQL 18+, per-domain schemas, UUID v7, direct SQL with psycopg 3, golang-migrate, named constraints, database roles
- **[Documentation Standards](https://github.com/rmorison/engineering-standards/blob/main/process/documentation-standards.md)** — Product specs, technical designs, ADRs
- **[Feature Development Workflow](https://github.com/rmorison/engineering-standards/blob/main/process/feature-development-workflow.md)** — Spec-driven: Intent → Spec → Plan → Execute → Validate

## Project

**Receipt Search Index** — Pre-index receipts from email, extract metadata (vendor, amount, date), generate PDF renditions, provide CLI search for accounting reconciliation.

**Status**: Pre-development. Product spec and technical design complete.

**Tech Stack**: Python 3.11+, PostgreSQL 18+, Anthropic Claude Haiku via Pydantic-AI, Click CLI, weasyprint for PDF rendering.

**Key Docs**:
- Product spec: `docs/product/features/receipt-search-index-spec.md`
- Technical design: `docs/engineering/designs/receipt-search-index.md`
- ADRs: `docs/engineering/adr/`

## Local Devtest Setup

### Database
```bash
POSTGRES_HOST_PORT=15432 docker compose up -d
```
Migrations (requires [golang-migrate](https://github.com/golang-migrate/migrate)):
```bash
DB="postgresql://main:localpass@localhost:15432/receipt_index_dev?sslmode=disable"  # pragma: allowlist secret
migrate -path db/migrations/public -database "${DB}&x-migrations-table=schema_migrations_public" up
migrate -path db/migrations/receipt -database "${DB}&x-migrations-table=schema_migrations_receipt" up
```
Note: Postgres 18 requires volume mount at `/var/lib/postgresql` (not `/data` subdirectory). Separate migration tables (`schema_migrations_public`, `schema_migrations_receipt`) are needed because both migration dirs start at version 000001.

### Running the CLI
See `example.env` for required environment variables. IMAP and Anthropic credentials are stored in 1Password — see project memory for details.
