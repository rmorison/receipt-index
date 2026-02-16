# Receipt Search Index — Product Specification

**Version:** 0.3 — Draft
**Date:** 2026-02-16

---

## Intent

During accounting reconciliation, matching bank transactions to supporting receipts is slow and error-prone. Receipts arrive from multiple sources (forwarded emails, scanned documents, vendor order pages) and land in disconnected locations with no consistent metadata. The reconciler must mentally reverse-engineer vendor, amount, and date from a bank feed entry, then hunt through email folders and file stores to locate the matching receipt.

**This tool eliminates the search problem.** It pre-indexes receipts from all sources, extracts structured metadata, generates standardized PDF renditions, and provides fast lookup by vendor, amount, and date range — so that reconciliation becomes confirmation rather than investigation.

## Scope

### Phase 1 — Email Receipts

Ingest from a configured IMAP receipts folder. For each message: extract vendor, amount(s), and date; generate a PDF rendition; store metadata in a search index; store the PDF in a local file store.

### Phase 2 — File-Based Receipts

Ingest from a Google Drive folder containing scanned receipts and print-to-PDF captures. Extract metadata via OCR/AI, index and store alongside email-sourced receipts.

### Future

- Direct accounting software integration (attach receipts from index to transactions)
- Automated matching suggestions (fuzzy join unreconciled transactions against index)
- Cloud storage backend (S3/GCS) behind the same file store interface

## Functional Requirements

| ID | Requirement |
|----|-------------|
| FR-01 | Ingest emails from a configured IMAP folder via standard IMAP protocol |
| FR-02 | Extract vendor name, transaction amount(s), and date from email content |
| FR-03 | Generate a single, human-readable PDF rendition of each receipt (rendered HTML body + embedded attachments) suitable for review by bookkeeper or claims adjuster |
| FR-04 | Store extracted metadata in PostgreSQL for indexed search |
| FR-05 | Store PDF renditions in a local file store using metadata-structured naming (`{date}__{vendor}__{amount}.pdf`) for human readability; directory layout compatible with future cloud storage migration |
| FR-06 | Search receipts by any combination of: vendor (substring), amount (exact or range), date (range) |
| FR-07 | Search results return metadata and a path/reference to the PDF file |
| FR-08 | Support idempotent ingestion — track processed messages by unique identifier (e.g., IMAP message ID) to skip already-seen items on subsequent runs |
| FR-09 | Handle common email receipt formats: forwarded vendor confirmations, attached PDF/image receipts, inline HTML order summaries |

## Non-Functional Requirements

| ID | Requirement |
|----|-------------|
| NFR-01 | Runs locally — no cloud services required (PostgreSQL on localhost) |
| NFR-02 | Python 3.11+, project structure per engineering standards |
| NFR-03 | Docker Compose option for PostgreSQL and application |
| NFR-04 | CLI interface for ingestion and search operations |
| NFR-05 | File store abstraction layer to support local filesystem now, cloud storage later |
| NFR-06 | Credentials (IMAP, database, API keys) via environment variables |
| NFR-07 | LLM-powered extraction via Anthropic API (Haiku model for cost-effective parsing); agentic patterns via Pydantic-AI |
| NFR-08 | Structured output support (JSON/Pydantic models) via CLI flag for agent consumption; human-friendly text by default |

## Architecture Overview

```
┌─────────────┐     ┌─────────────┐
│ IMAP Folder  │     │ Google Drive │  (Phase 2)
└──────┬──────┘     └──────┬──────┘
       │                   │
       ▼                   ▼
┌──────────────────────────────────┐
│         Ingestion Pipeline       │
│  ┌───────────┐  ┌──────────────┐ │
│  │  Adapter   │  │  Metadata    │ │
│  │ (per src)  │  │  Extractor   │ │
│  └───────────┘  └──────────────┘ │
└──────────┬───────────────────────┘
           │
     ┌─────┴─────┐
     ▼           ▼
┌─────────┐ ┌──────────┐
│ Postgres │ │ File     │
│ (index)  │ │ Store    │
└─────────┘ │ (PDFs)   │
            └──────────┘
     ┌───────────┘
     ▼
┌──────────────┐
│  CLI Search  │
│  Interface   │
└──────────────┘
```

**Key design decisions:**

- **PostgreSQL over SQLite:** Richer full-text search, better concurrency if we later add a web UI, aligns with existing infrastructure.
- **File store abstraction:** Local filesystem with a defined directory/naming structure. Interface designed so a cloud backend (S3, GCS) can be swapped in without changing callers.
- **Adapter pattern for sources:** Each ingestion source (IMAP, Drive, future vendor APIs) implements a common interface, keeping the pipeline source-agnostic.

## Success Criteria

1. Reconciler can find the matching receipt for a bank transaction in under 30 seconds (vs. 5-10 minutes today)
2. Existing ~200 email receipts are indexed and searchable
3. PDF renditions are clean enough to attach directly to accounting transactions
4. Incremental runs complete in under 60 seconds for a typical week's receipts

## Resolved Decisions

| ID | Decision |
|----|----------|
| RD-01 | **LLM extraction:** Anthropic Haiku model via Pydantic-AI for metadata parsing. Cost-effective and proven in other projects. This project may also inform new engineering standards for agentic patterns. |
| RD-02 | **File naming:** Metadata-structured (`{date}__{vendor}__{amount}.pdf`) for human readability and manual review. |
| RD-03 | **CLI output:** Human-friendly text by default; structured output (JSON/Pydantic models) via `--output json` flag for agent consumption. |
| RD-04 | **PDF rendition:** Single human-readable PDF per receipt — rendered HTML with embedded images/attachments. Target audience is bookkeeper during reconciliation and claims adjuster during documentation review. |
| RD-05 | **Project scope:** Standalone project. |
| RD-06 | **Ingestion mode:** One-shot CLI command. Future expansion via workflow system (e.g., Dagster), not daemon mode. |
| RD-07 | **Idempotency:** Track processed items by unique ID (e.g., IMAP message ID) to skip on re-runs. Duplicate receipt detection is out of scope. |

## Open Questions

None — all questions resolved during technical design.

| ID | Resolution |
|----|------------|
| ~~OQ-01~~ | Resolved in [ADR-0003](../../engineering/adr/0003-local-file-store-with-abstraction.md): year/month subdirectory structure (`{YYYY}/{MM}/`). |
