# Production Setup

Run Receipt Search Index against a native PostgreSQL 18 server instead of Docker. This is suitable for a host-based deployment where you want to ingest and search your full set of receipts.

## 1. Install PostgreSQL 18

On Ubuntu (with the [PGDG apt repository](https://wiki.postgresql.org/wiki/Apt) configured):

```bash
sudo apt install postgresql-18
```

This creates a default cluster (`18/main`), starts it, and enables autostart on reboot. Verify:

```bash
pg_lsclusters
```

You should see something like:

```
Ver Cluster Port Status Owner    Data directory
18  main    5432 online postgres /var/lib/postgresql/18/main
```

Note the port — if other PostgreSQL versions are installed, 18 may get assigned `5433` or higher.

## 2. Create Database and Roles

Connect as the `postgres` superuser and set up the database and application roles:

```bash
sudo -u postgres psql
```

```sql
-- Create the database
CREATE DATABASE receipt_index;

-- Create application roles
CREATE ROLE receipt_index_write WITH LOGIN PASSWORD 'your-secure-password';  -- pragma: allowlist secret
CREATE ROLE receipt_index_read WITH LOGIN PASSWORD 'your-secure-password';  -- pragma: allowlist secret

-- Grant database-level connect
GRANT CONNECT ON DATABASE receipt_index TO receipt_index_write;
GRANT CONNECT ON DATABASE receipt_index TO receipt_index_read;

\q
```

Note: In production you don't need the `_all` role — the `postgres` superuser runs migrations directly.

## 3. Run Migrations

Set the migration URL to use the `postgres` superuser (or another superuser role) and point it at your native cluster:

```bash
export MIGRATION_DATABASE_URL="postgresql://postgres@localhost:5432/receipt_index?sslmode=disable"

migrate -path db/migrations/public \
  -database "${MIGRATION_DATABASE_URL}&x-migrations-table=schema_migrations_public" up

migrate -path db/migrations/receipt \
  -database "${MIGRATION_DATABASE_URL}&x-migrations-table=schema_migrations_receipt" up
```

The migrations create the `receipt` schema, tables, indexes, and grant permissions. The grant migration (`000002_grant_receipts_access.up.sql`) references `receipt_index_dev_write` and `receipt_index_dev_read` roles — for production, either:

- **Option A**: Create the dev-named roles as aliases (simplest, no migration changes):
  ```sql
  CREATE ROLE receipt_index_dev_write WITH LOGIN PASSWORD 'your-secure-password';  -- pragma: allowlist secret
  CREATE ROLE receipt_index_dev_read WITH LOGIN PASSWORD 'your-secure-password';  -- pragma: allowlist secret
  ```
- **Option B**: Add production-specific grant migrations (cleaner long-term)

Option A is recommended to get started — the role names are just labels.

## 4. Configure `.env`

Update your `.env` to point at the native PostgreSQL instance instead of Docker:

```bash
# Database — application connection (write role, used by the CLI)
DATABASE_URL=postgresql://receipt_index_dev_write:your-secure-password@localhost:5432/receipt_index  # pragma: allowlist secret

# Database — migrations (superuser, used by make migrate-up)
MIGRATION_DATABASE_URL=postgresql://postgres@localhost:5432/receipt_index
```

Key differences from the Docker dev setup:

| Setting | Docker (dev) | Native (production) |
|---|---|---|
| Port | `15432` (mapped) | `5432` (default) or check `pg_lsclusters` |
| Database name | `receipt_index_dev` | `receipt_index` |
| Migration user | `main` (Docker superuser) | `postgres` (system superuser) |
| Passwords | `localpass` | Use secure passwords |
| SSL | `sslmode=disable` | Consider `sslmode=require` for remote connections |

All other `.env` variables (`IMAP_*`, `ANTHROPIC_API_KEY`, `RECEIPT_STORE_PATH`, etc.) remain the same.

## 5. Verify

Test the connection:

```bash
psql "$DATABASE_URL"
```

Run a dry-run ingest:

```bash
uv run receipt-index ingest --dry-run
```

Then ingest your full receipt set:

```bash
uv run receipt-index ingest
```

## 6. PostgreSQL Maintenance

### Check cluster status

```bash
pg_lsclusters
sudo systemctl status postgresql@18-main
```

### Start / stop / restart

```bash
sudo systemctl start postgresql@18-main
sudo systemctl stop postgresql@18-main
sudo systemctl restart postgresql@18-main
```

### Logs

```bash
sudo journalctl -u postgresql@18-main -f
```

### pg_hba.conf

If connecting from a different host, edit `/etc/postgresql/18/main/pg_hba.conf` to allow remote connections, and set `listen_addresses` in `postgresql.conf`. Restart after changes.
