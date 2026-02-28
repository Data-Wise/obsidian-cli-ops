# SPEC: Fix Async Vault Operations in obs CLI

**Date:** 2026-02-28
**Branch:** `feature/fix-async-vault-ops` (from `dev`)
**Scope:** `src/python/obs_cli.py`, `src/python/graph_analyzer.py`, `src/python/db_manager.py`

## Problem

Three bugs prevent `scan` and `analyze` from working in v3.0.0-dev:

### Bug 1: Missing `await` on async `scan_vault()` (Critical)

**Files:** `obs_cli.py:69`, `obs_cli.py:88`

`VaultManager.scan_vault()` is `async def` (vault_manager.py:126) but called synchronously:

```python
# obs_cli.py:88 — scan() method
result = self.vault_manager.scan_vault(vault_path, vault_name)
#        ^^^^^ returns a coroutine object, not a ScanResult
```

**Result:** `AttributeError: 'coroutine' object has no attribute 'vault_name'`

Same issue at line 69 inside `discover()`.

### Bug 2: Vault ID lookup fails with displayed IDs (Critical)

**Files:** `obs_cli.py:332,397`, `graph_analyzer.py:63-65`, `db_manager.py:120-126`

`analyze` takes a `vault_id` argument, but `vaults` displays 8-char IDs while the DB stores 16-char SHA256 prefixes. `get_vault()` does exact match, so the displayed IDs can't be used.

```python
# graph_analyzer.py:63
vault = self.db.get_vault(vault_id)  # exact match only
```

**Result:** `Vault not found: a812d844` (even though `vaults` lists it)

### Bug 3: `discover()` loop has same async issue as Bug 1

**File:** `obs_cli.py:69`

Same missing `await` pattern inside the discover scan loop.

## Fix

### Bug 1 & 3: Wrap async calls with `asyncio.run()`

The CLI is synchronous. Don't make the CLI methods async — wrap the async calls instead:

```python
import asyncio

# obs_cli.py — scan() method (line 88)
result = asyncio.run(self.vault_manager.scan_vault(vault_path, vault_name))

# obs_cli.py — discover() method (line 69)
result = asyncio.run(self.vault_manager.scan_vault(vault_path, vault_name))
```

**Why `asyncio.run()` not `async`/`await`:** The CLI entry point (`main()`) is sync, argparse is sync, and there's no event loop to reuse. `asyncio.run()` is the standard pattern for calling async code from a sync CLI.

**Check for other calls:** Grep for all `self.vault_manager.` calls in `obs_cli.py` — any method that's `async def` in `vault_manager.py` needs the same treatment.

### Bug 2: Support vault lookup by name or ID prefix

Add name-based and prefix-based vault lookup in `db_manager.py`:

```python
def get_vault_by_name_or_id(self, identifier: str) -> Optional[Dict]:
    """Look up vault by name (exact), then ID prefix."""
    with self.get_connection() as conn:
        # Try name first (most intuitive for users)
        cursor = conn.execute(
            "SELECT * FROM vaults WHERE name = ?", (identifier,)
        )
        row = cursor.fetchone()
        if row:
            return dict(row)

        # Fall back to ID prefix
        cursor = conn.execute(
            "SELECT * FROM vaults WHERE id LIKE ?", (identifier + "%",)
        )
        row = cursor.fetchone()
        return dict(row) if row else None
```

Update `graph_analyzer.py:63` to use it:

```python
vault = self.db.get_vault_by_name_or_id(vault_id)
```

This lets users write `obs analyze Knowledge_Base` (by name) or `obs analyze a812` (by ID prefix).

## Testing

```bash
# After fix, these should all work:
python3 src/python/obs_cli.py scan "/Users/dt/Library/Mobile Documents/iCloud~md~obsidian/Documents/Knowledge_Base"
python3 src/python/obs_cli.py analyze Knowledge_Base
python3 src/python/obs_cli.py analyze a812d844
python3 src/python/obs_cli.py discover "/Users/dt/Library/Mobile Documents/iCloud~md~obsidian/Documents"
```

## Verification Checklist

- [ ] `obs scan <path>` completes without coroutine errors
- [ ] `obs analyze <vault-name>` finds vault by name
- [ ] `obs analyze <partial-id>` finds vault by ID prefix
- [ ] `obs discover <path>` scans found vaults without errors
- [ ] `obs vaults` still lists vaults correctly
- [ ] `obs db stats` still works
- [ ] Existing tests pass (if any — `jest.config.js` and `pytest.ini` exist)
