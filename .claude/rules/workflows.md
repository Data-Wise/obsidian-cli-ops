---
paths:
  - "src/**"
  - "tests/**"
---

# Common Workflows

## Adding a New v2.0 Command (Three-Layer Approach)

### Step 1: Add business logic to core layer

```python
# src/python/core/vault_manager.py
def export_vault(self, vault_id: str, format: str) -> ExportResult:
    """Export vault to specific format."""
    vault = self.get_vault(vault_id)
    if not vault:
        raise VaultNotFoundError(f"Vault not found: {vault_id}")

    # Business logic here (interface-agnostic)
    notes = self.get_notes(vault_id)
    # ... export logic ...

    return ExportResult(
        vault_id=vault_id,
        format=format,
        notes_exported=len(notes),
        output_path=output_path
    )
```

### Step 2: Add CLI interface

```python
# src/python/obs_cli.py
def export(self, args):
    """Export vault command."""
    result = self.vault_manager.export_vault(args.vault_id, args.format)

    # CLI-specific formatting
    if args.json:
        print(result.to_json())
    else:
        print(f"✓ Exported {result.notes_exported} notes to {result.output_path}")
```

### Step 3: Add argument parser

```python
# src/python/obs_cli.py main()
export_parser = subparsers.add_parser('export', help='Export vault')
export_parser.add_argument('vault_id', help='Vault ID')
export_parser.add_argument('--format', choices=['json', 'csv', 'html'], default='json')
```

### Step 4: Add TUI interface (optional)

```python
# src/python/tui/screens/vaults.py
def on_export_clicked(self):
    """Handle export button click."""
    result = self.vault_manager.export_vault(self.selected_vault_id, "json")

    # TUI-specific display
    self.notify(f"Exported {result.notes_exported} notes")
    self.refresh()
```

### Step 5: Add ZSH wrapper

```zsh
# src/obs.zsh
obs_export() {
    local python_cli=$(_get_python_cli) || return 1
    python3 "$python_cli" export "$@"
}
```

**Key principles:**
- Business logic in core layer (step 1)
- Presentation logic in CLI/TUI (steps 2, 4)
- Both interfaces use same core method
- Zero duplication of business logic

## Extending the Database

1. Update `schema/vault_db.sql` with new table/column
2. Increment version in `schema_version` table
3. Add corresponding methods to `DatabaseManager`
4. Update views/triggers if needed
5. Test with `python3 src/python/db_manager.py`

## Adding New Graph Metrics

1. Add calculation in `GraphBuilder.calculate_metrics()`
2. Update `graph_metrics` table schema if needed
3. Add query method in `DatabaseManager`
4. Expose in CLI commands

## Releasing: Version-Bump Checklist

When bumping the version, update **every** file that carries the version string —
grep the old version across the whole repo first (`grep -rn "<old>" --include='*.json'
--include='*.toml' --include='*.zsh' --include='*.py' --include='*.1' --include='*.md'
. | grep -v node_modules`). The files that must move together:

- `package.json` / `package-lock.json`
- `pyproject.toml`
- `src/python/__init__.py`
- `src/obs.zsh` (header `# Version:` comment)
- **`man/man1/obs.1`** — the `.TH` line's `obsidian-cli-ops <version>` field.
  `__tests__/man-page-version-sync.test.js` asserts this equals `package.json`,
  so a forgotten man-page bump is a **hard CI failure**, not silent drift. (The
  `.TH` date field is ISO `YYYY-MM-DD`, mandoc-clean, and intentionally unguarded
  — it is decoupled from the version and may go stale without breaking anything.)
- `README.md` / `CLAUDE.md` (version badges and references)

### Release-check harness (gate order)

`scripts/` carries validators that prevent the drift classes v4.0.0 shipped
(25→38 MCP-tool undercount; stale Homebrew caveats). Run them in this order:

1. **Pre-tag** — `scripts/validate-counts.sh` (counts in docs == source of truth;
   `--fix` to auto-correct). Also enforced in CI by `tests/test_doc_counts.py` and
   surfaced anytime via `obs doctor --layer docs`, so count drift cannot merge.
2. Release → GitHub release → `homebrew-release.yml` auto-bumps the tap (url+sha256).
3. **After the formula bump** — `scripts/verify-caveats.sh` (the tap caveats name the
   current tool count + `obs config`/`obs research` + the `obsidian-ops` MCP key).
4. **After `brew install/upgrade`** — `scripts/post-install-check.sh [version]`
   (obs version, `obs doctor` clean = db-init worked, installed tool count == source).
   The canonical gate is `brew reinstall --build-from-source` (audit-green ≠ installs clean).
5. **Post-release** — `scripts/post-release-sweep.sh [--fix]` (Tier-2: counts, stray
   version strings, changelog currency).

Design: `core/doc_counts.py` is the single source of truth for counts; the shell
scripts + doctor check + pytest are thin consumers (no duplication). Spec:
`docs/specs/SPEC-release-check-harness-2026-06-22.md`.

### MCP server dep changes (separate from version bump)

If `mcp_server.py` deps change (new import, upgraded `mcp` lib, new transitive):
1. Update `requirements.lock` with pinned versions
2. Update `pyproject.toml` `dependencies` block
3. **Manually** regenerate Homebrew resource blocks:
   ```bash
   brew update-python-resources data-wise/tap/obsidian-cli-ops
   ```
   The release CI (`homebrew-release.yml`) only bumps `url` + main `sha256` — resource
   blocks are **static** and must be updated by hand before tagging the release.
4. Run `brew audit --strict data-wise/tap/obsidian-cli-ops` to verify clean.

## R-Dev Integration Flow

The R-Dev module requires a two-step workflow:
1. **Link**: Establish mapping between R project and Obsidian folder (`obs r-dev link`)
2. **Operations**: Once linked, use `log`, `draft` commands which auto-detect context

This design allows users to work within their R project directory without specifying the Obsidian target repeatedly.
