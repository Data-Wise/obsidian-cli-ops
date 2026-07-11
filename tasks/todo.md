# Task List: Diagnostics and Installer Hardening (Issue #85)

## Task 1: Database Nesting Guard and Column Migration
**Description:** Implement parent-child overlap validation in `db_manager.py`'s `add_vault` method, and dynamically add `failed_paths` column to `scan_history` in `_ensure_scan_history_columns`. Update `schema/vault_db.sql`. Update `complete_scan` method signature.

**Acceptance criteria:**
- [x] Attempting to add a vault path that overlaps with an existing vault path (either exact match, parent, or child) raises a `ValueError`.
- [x] Database dynamically adds `failed_paths TEXT` to `scan_history` if not present.
- [x] `schema/vault_db.sql` defines `failed_paths TEXT` in `scan_history`.
- [x] `complete_scan` accepts `failed_paths` list and saves it serialized to JSON.

**Verification:**
- [x] Run `pytest src/python/tests/test_db_manager.py`

**Dependencies:** None
**Files likely touched:** `src/python/db_manager.py`, `schema/vault_db.sql`
**Estimated scope:** S (2 files)

---

## Task 2: Persist Failed Paths in Scanner
**Description:** Modify `VaultScanner.scan_vault` to pass the collected `failed_paths` list to the `db.complete_scan` call.

**Acceptance criteria:**
- [x] Failing note paths are saved as a JSON string to the SQLite database during scanning.

**Verification:**
- [x] Python unit tests verify `failed_paths` is correctly supplied and serialized.

**Dependencies:** Task 1
**Files likely touched:** `src/python/vault_scanner.py`
**Estimated scope:** S (1 file)

---

## Task 3: Implement Nesting Overlap Check in Doctor
**Description:** Add a `vault-nesting` check to `_check_vaults` in `core/doctor.py` that warns when nested/overlapping vaults are indexed.

**Acceptance criteria:**
- [x] Overlapping vaults produce a `warn` diagnostic result showing which paths collide.

**Verification:**
- [x] Run `pytest src/python/tests/test_doctor.py`

**Dependencies:** Task 1
**Files likely touched:** `src/python/core/doctor.py`
**Estimated scope:** S (1 file)

---

## Task 4: Inline Failing Paths in Doctor
**Description:** Update `_sync_errors_result` in `core/doctor.py` to retrieve `failed_paths` from the database, safely handle NULLs, parse JSON, and inline the first 5 paths in the warning message.

**Acceptance criteria:**
- [x] `obs doctor` outputs the specific failed note paths when `notes_failed > 0`.

**Verification:**
- [x] Run `pytest src/python/tests/test_doctor.py`

**Dependencies:** Task 2
**Files likely touched:** `src/python/core/doctor.py`
**Estimated scope:** S (1 file)

---

## Task 5: Detailed Per-Vault iCloud Offload Warning
**Description:** Update `_check_icloud` in `core/doctor.py` to check each vault for offloaded files and recommend vault-specific `brctl download` commands.

**Acceptance criteria:**
- [x] Warning displays a targeted `brctl download` command referencing the specific vault paths for each vault containing offloaded files.

**Verification:**
- [x] Run `pytest src/python/tests/test_doctor.py`

**Dependencies:** None
**Files likely touched:** `src/python/core/doctor.py`
**Estimated scope:** S (1 file)

---

## Task 6: Rewrite Claude Desktop MCP Path Setup
**Description:** Create a Python helper script `scripts/configure_mcp.py` to safely expand path variables (handling tilde expansion) and update `claude_desktop_config.json` with absolute paths. Update `install.sh` to run it.

**Acceptance criteria:**
- [x] `claude_desktop_config.json` contains direct commands to the fully resolved absolute venv python path and `mcp_server.py` path.
- [x] Config is updated in both standard Claude Desktop directory paths if they exist.

**Verification:**
- [x] Inspect `claude_desktop_config.json` after running `./install.sh`.

**Dependencies:** None
**Files likely touched:** `install.sh`, `scripts/configure_mcp.py` (new)
**Estimated scope:** M (2 files)

---

## Checkpoint: Final Integration
- [x] All unit and integration tests pass cleanly: `pytest`
- [x] `obs doctor` executes with no unhandled exceptions.
