# Receipt Search Index

Pre-index receipts from email (and later, file stores), extract structured metadata, and provide fast CLI-based search — so that accounting reconciliation becomes confirmation rather than investigation.

## Prerequisites

- Python 3.11+
- [uv](https://docs.astral.sh/uv/) (Python package manager)
- [Docker](https://www.docker.com/) and Docker Compose (for PostgreSQL)
- [golang-migrate](https://github.com/golang-migrate/migrate) (for database migrations)

## Quick Start

```bash
make setup                    # Install deps + pre-commit hooks
docker compose up -d          # Start PostgreSQL 18
make migrate-up               # Run migrations (public → receipt)
cp example.env .env           # Configure credentials
```

## Development

```bash
make lint                     # Run linting (ruff check)
make format                   # Format code (ruff format + fix)
make format-check             # Check formatting without modifying
make typecheck                # Run type checking (mypy)
make test                     # Run all tests with coverage
make test-unit                # Run unit tests only
make test-integration         # Run integration tests only
```

## Database

```bash
make docker-db-up             # Start PostgreSQL
make docker-db-down           # Stop PostgreSQL
make migrate-up               # Apply all migrations
make migrate-down             # Roll back last migration per schema
```

## Documentation

See [`docs/`](docs/README.md) for:

- [Product Specification](docs/product/features/receipt-search-index-spec.md)
- [Technical Design](docs/engineering/designs/receipt-search-index.md)
- [Architecture Decision Records](docs/README.md#architecture-decision-records)

## Tech Stack

- Python 3.11+
- PostgreSQL 18+ (via Docker Compose)
- Anthropic Claude Haiku (via Pydantic-AI) for metadata extraction
- CLI interface (Click)

## License

MIT — see [LICENSE](LICENSE)
