-- Grant ingest_log table privileges to application roles.

-- _all: full DDL access (runs migrations)
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA receipt TO receipt_index_dev_all;

-- _write: insert + select on ingest_log
GRANT SELECT, INSERT ON receipt.ingest_log TO receipt_index_dev_write;

-- _read: SELECT only
GRANT SELECT ON receipt.ingest_log TO receipt_index_dev_read;
