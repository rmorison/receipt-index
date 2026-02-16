# Receipt Search Index

Pre-index receipts from email (and later, file stores), extract structured metadata, and provide fast CLI-based search — so that accounting reconciliation becomes confirmation rather than investigation.

## Status

**Pre-development** — Product spec and technical design complete. Implementation not yet started.

## Documentation

See [`docs/`](docs/README.md) for:

- [Product Specification](docs/product/features/receipt-search-index-spec.md)
- [Technical Design](docs/engineering/designs/receipt-search-index.md)
- [Architecture Decision Records](docs/README.md#architecture-decision-records)

## Planned Tech Stack

- Python 3.11+
- PostgreSQL 18+ (via Docker Compose)
- Anthropic Claude Haiku (via Pydantic-AI) for metadata extraction
- CLI interface (Click)

## License

MIT — see [LICENSE](LICENSE)
