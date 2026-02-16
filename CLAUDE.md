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
