# Implementation Plan: Diagnostics and Installer Hardening (Issue #85)

## Overview
Implement fixes and enhancements to resolve iCloud offload warning specificity, fragile shell-wrapped MCP commands, duplicate indexing from nested vaults, and vague per-note diagnostic summaries.

## Architecture Decisions
* **Direct Path MCP Setup:** Write a Python script (`scripts/configure_mcp.py`) invoked by `install.sh` that checks for both standard Claude configuration paths and updates the `obsidian-ops` entry directly with the fully expanded absolute Python interpreter path from the virtual environment and the absolute script path of `mcp_server.py`. (Do NOT write unexpanded tilde `~` paths).
* **Robust Nesting Detection:** Implement overlap check in `DatabaseManager.add_vault` by verifying if the absolute resolved path of the new vault matches, is a parent of, or is a child of any already registered vault path:
  ```python
  if (vault_path_obj == ev_path 
          or vault_path_obj in ev_path.parents 
          or ev_path in vault_path_obj.parents):
      raise ValueError(f"Vault nesting detected: ...")
  ```
* **Per-Note Error Persistence:** Add `failed_paths TEXT` column dynamically to the `scan_history` table in `DatabaseManager._ensure_scan_history_columns`. Also update the initial schema `schema/vault_db.sql`. Update the `complete_scan` method signature to accept `failed_paths: Optional[List[str]] = None` and save it serialized as a JSON string (with safety fallbacks for parsing/decoding null/empty values).
* **Warning Before writing to Documents folder:** As an agent rule/boundary, if any task requires writing files directly to `/Users/dt/Library/Mobile Documents/iCloud~md~obsidian/Documents` or its subfolders, we must explicitly warn the user, prompt for confirmation, and suggest an alternative folder.

## Task List

### Phase 1: Database Migration and Nesting Guard
* **Task 1:** Add `failed_paths` column to `scan_history` (via `_ensure_scan_history_columns` in `db_manager.py` and in `schema/vault_db.sql`).
* **Task 2:** Implement nesting overlap validation check in `add_vault` in `db_manager.py` (checking exact matches, parent-of, and child-of). Update `complete_scan` signature to accept and serialize `failed_paths`.
* **Task 3:** Update `vault_scanner.py` to capture and pass `failed_paths` list to `db.complete_scan` at scan completion.

### Checkpoint: Database
* **Database Verification:** Verify that registering a nested vault folder fails with a `ValueError`. Run existing db tests.

### Phase 2: Diagnostics and Warnings
* **Task 4:** Implement nesting/overlap checks in `core/doctor.py` (`vault-nesting` check).
* **Task 5:** Update `_sync_errors_result` in `core/doctor.py` to retrieve `failed_paths` from the database, safely parse it, and inline up to the first 5 paths.
* **Task 6:** Update `_check_icloud` in `core/doctor.py` to perform per-vault check and recommend specific `brctl download` commands for each vault with offloaded files.

### Checkpoint: Diagnostics
* **Diagnostics Verification:** Run `pytest src/python/tests/test_doctor.py` and run `obs doctor` to inspect outputs.

### Phase 3: Installer Hardening
* **Task 7:** Create `scripts/configure_mcp.py` to safely expand paths and write direct commands to both standard Claude Desktop config locations. Update `install.sh` to run this script.

### Checkpoint: Full Verification
* **Final Verification:** Run `./install.sh`, run `obs doctor`, and ensure all pytest unit tests pass cleanly.

## Risks and Mitigations
| Risk | Impact | Mitigation |
|---|---|---|
| Auto-migration of sqlite schema fails on legacy database | Medium | Use `ALTER TABLE ...` inside a safe, retry-handled `_ensure_scan_history_columns` dynamic helper. |
| Writing to `claude_desktop_config.json` corrupts user config | High | Implement a Python helper that parses JSON, modifies only the `obsidian-ops` sub-dictionary, and writes it back cleanly preserving the structure. Always write a backup first. |

## Open Questions
None.
