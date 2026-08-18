# Spec: Diagnostic & Installer Hardening (Issue #85)

## Objective
Address the diagnostic audit findings to improve CLI robustness, prevent indexing bugs, and resolve fragile setup configurations:
1. **iCloud Offload Warning:** Update `obs diagnose` (`core/doctor.py`) to report specific `brctl download` commands for vaults containing offloaded files.
2. **Robust MCP Configuration:** Modify `install.sh` to write direct absolute paths for the `obsidian-ops` command and args in `claude_desktop_config.json`, replacing the zsh wrapper script.
3. **Vault Nesting Prevention:** Throw a `ValueError` during vault registration/addition when a parent-child directory overlap is detected. Add a `vault-overlap` layer check to `obs diagnose`.
4. **Per-Note Error Diagnostics:** Add a `failed_paths` column to `scan_history` to persist failing paths, and output these inline in the diagnose results.

## Tech Stack
* Language: ZSH (installer/hooking), Python 3.9+ (database migrations, CLI parser, doctor tests)
* Database: SQLite (migrations/schema additions)

## Commands
* Run tests: `pytest src/python/tests/test_doctor.py src/python/tests/test_db_manager.py`
* Run diagnose: `obs doctor`
* Run installer: `./install.sh`

## Project Structure
* `install.sh` &rarr; Installer script that provisions environment. We will add a Python script execution step to write direct MCP config paths.
* `src/python/db_manager.py` &rarr; SQLite manager. We will add overlap checks in `add_vault` and the `failed_paths` migration.
* `src/python/vault_scanner.py` &rarr; Scans markdown files. We will pass failed note paths to the `complete_scan` database call.
* `src/python/core/doctor.py` &rarr; Implements diagnostic checks. We will add the `vault-overlap` check and print inline failed note paths.

## Code Style
Standard PEP 8 Python style. Path resolution should use `pathlib.Path.resolve()` to ensure correct path comparison.

```python
# Path comparison example
if vault_path_obj in existing_path_obj.parents:
    raise ValueError("Vault nesting detected")
```

## Testing Strategy
1. **Unit Tests:** Add unit tests to check:
   * Vault nesting `ValueError` on path overlap.
   * `failed_paths` serialization and storage.
   * `vault-overlap` detection in `doctor.py`.
2. **Integration Test:** Execute `./install.sh` and inspect the updated `claude_desktop_config.json` to verify direct path writing.

## Boundaries
* **Always do:** Preserve compatibility with non-Darwin (Linux) systems (skip Darwin-specific checks cleanly).
* **Ask first:** Modifying other configuration files outside `claude_desktop_config.json`; writing any file to the `Documents` folder or its sub-directories (must warn the user, get confirmation, and suggest an alternative directory).
* **Never do:** Commit secrets, edit external virtual environments directly, or force database drops.

## Success Criteria
- [ ] `./install.sh` configures `obsidian-ops` command to use the absolute path of the virtual environment's python interpreter and the absolute path of `mcp_server.py`.
- [ ] Attempting to scan or add a nested/overlapping vault raises a `ValueError` explaining the overlap.
- [ ] `obs doctor` lists specific failing note paths if the last scan had per-note failures.
- [ ] `obs doctor` displays warnings for any overlapping/nested vaults on disk.
- [ ] All tests pass successfully.

## Open Questions
1. Do you have any preferred fallback command if python is not available during installation to update the JSON config? (Default: we use the bootstrapped python in the venv).
