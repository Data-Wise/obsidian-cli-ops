# Fix Async Vault Operations — Orchestration Plan

> **Branch:** `feature/fix-async-vault-ops`
> **Base:** `dev`
> **Worktree:** `~/.git-worktrees/obsidian-cli-ops/feature-fix-async-vault-ops`
> **Spec:** `SPEC-fix-async-vault-ops.md`

## Objective

Fix three bugs that prevent `scan`, `analyze`, and `discover` from working in obs CLI v3.0.0-dev. Two root causes: missing `asyncio.run()` wrappers and vault lookup by exact ID only.

## Phase Overview

| Phase | Task | Files | Priority | Status |
|-------|------|-------|----------|--------|
| 1 | Audit all async calls in CLI layer | `obs_cli.py`, `vault_manager.py` | High | |
| 2 | Fix async/await mismatch (Bugs 1 & 3) | `obs_cli.py` | High | |
| 3 | Add vault name/prefix lookup (Bug 2) | `db_manager.py`, `graph_analyzer.py` | High | |
| 4 | Update `analyze` arg from `vault_id` to `vault` | `obs_cli.py` | Medium | |
| 5 | Test all fixed commands | — | High | |
| 6 | Clean up and commit | — | Medium | |

## Phase Details

### Phase 1: Audit async calls

Before fixing, identify ALL async methods in `vault_manager.py` and ALL call sites in `obs_cli.py`. Don't just fix the two known lines — grep for every `self.vault_manager.` call and cross-reference with `async def` in the manager.

```bash
# In vault_manager.py — find all async methods
grep "async def" src/python/vault_manager.py

# In obs_cli.py — find all vault_manager calls
grep "self.vault_manager\." src/python/obs_cli.py
```

**Output:** A list of which calls need `asyncio.run()` and which are already sync-safe.

### Phase 2: Fix async/await mismatch

1. Add `import asyncio` to `obs_cli.py` (if not already present)
2. Wrap every async `self.vault_manager.*()` call with `asyncio.run()`
3. Known locations: lines 69 and 88, but Phase 1 may find more

**Pattern:**
```python
# Before
result = self.vault_manager.scan_vault(path, name)

# After
result = asyncio.run(self.vault_manager.scan_vault(path, name))
```

**Commit:** `fix: wrap async vault_manager calls with asyncio.run()`

### Phase 3: Add vault name/prefix lookup

1. Add `get_vault_by_name_or_id()` method to `db_manager.py`
   - Try exact name match first (most intuitive)
   - Fall back to ID prefix match (`LIKE ? || '%'`)
   - Return `None` if neither matches
2. Update `graph_analyzer.py:63` to use the new method instead of `get_vault()`

**Commit:** `fix: support vault lookup by name or ID prefix`

### Phase 4: Update CLI argument naming

1. In `obs_cli.py` argument parser (line 332), rename `vault_id` to `vault`
2. Update help text: `"Vault name or ID"` instead of `"Vault ID"`
3. This makes `obs analyze Knowledge_Base` the documented UX

**Commit:** `refactor: rename analyze argument from vault_id to vault`

### Phase 5: Test all fixed commands

Run each command and verify output:

```bash
# Bug 1 fix — scan should complete without coroutine error
python3 src/python/obs_cli.py scan "/Users/dt/Library/Mobile Documents/iCloud~md~obsidian/Documents/Knowledge_Base"

# Bug 2 fix — analyze should find vault by name
python3 src/python/obs_cli.py analyze Knowledge_Base

# Bug 2 fix — analyze should find vault by ID prefix
python3 src/python/obs_cli.py analyze a812d844

# Bug 3 fix — discover should scan without errors
python3 src/python/obs_cli.py discover "/Users/dt/Library/Mobile Documents/iCloud~md~obsidian/Documents"

# Regression — existing commands should still work
python3 src/python/obs_cli.py vaults
python3 src/python/obs_cli.py db stats
```

Also run existing test suites if present:
```bash
pytest tests/ -v 2>/dev/null
npm test 2>/dev/null
```

### Phase 6: Clean up and commit

1. Verify all checklist items in spec pass
2. Remove `ORCHESTRATE-fix-async-vault-ops.md` (working artifact)
3. Final commit if any cleanup needed

## Acceptance Criteria

- [ ] `obs scan <path>` completes without coroutine errors
- [ ] `obs analyze Knowledge_Base` finds vault by name
- [ ] `obs analyze a812` finds vault by ID prefix
- [ ] `obs discover <path>` scans found vaults without errors
- [ ] `obs vaults` still lists vaults correctly
- [ ] `obs db stats` still works
- [ ] Existing tests pass
- [ ] No regressions in other commands

## How to Start

```bash
cd ~/.git-worktrees/obsidian-cli-ops/feature-fix-async-vault-ops
claude
```

Then follow phases 1-6 in order. Phase 1 (audit) informs Phase 2, so don't skip it.
