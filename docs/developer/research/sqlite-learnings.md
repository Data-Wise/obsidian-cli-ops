# Learnings & Technical Debrief

## SQLite Limitations Encountered (2025-12-19)

During the TUI polish phase, we encountered specific behaviors in SQLite that required workarounds.

### 1. Pagination Syntax
**Issue:** `sqlite3.OperationalError: near "OFFSET": syntax error`
**Cause:** SQLite does not support `OFFSET` without a `LIMIT` clause.
**Fix:** When `offset` is provided but `limit` is not, inject `LIMIT -1`.
**Code:**
```python
if limit is not None:
    query += " LIMIT ?"
elif offset is not None:
    query += " LIMIT -1" # Required for OFFSET
```

### 2. In-Memory Database Persistence
**Issue:** `sqlite3.OperationalError: no such table: vaults` during tests.
**Cause:** Using `sqlite3.connect(":memory:")` creates a *new, isolated* database for every connection. Since `DatabaseManager` uses a context manager that opens/closes connections per operation, the schema created in `initialize_database` was lost immediately.
**Fix:** Use a temporary file (e.g., `/tmp/test.db`) for integration tests involving multiple DB operations, or refactor `DatabaseManager` to hold a persistent connection for in-memory mode.

### 3. Missing JOINs in Models
**Issue:** `KeyError: 'vault_id'` when converting `GraphMetrics` row to object.
**Cause:** The `graph_metrics` table only stores `note_id`. The model required `vault_id`, but the simple `SELECT *` query didn't provide it.
**Fix:** Updated `get_graph_metrics` to perform a `JOIN` with the `notes` table to retrieve the missing context.

---
**Action Item:** Consider strict typing for DB row returns or lighter models that don't require full context if not available.
