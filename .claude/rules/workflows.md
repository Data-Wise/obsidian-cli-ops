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

## R-Dev Integration Flow

The R-Dev module requires a two-step workflow:
1. **Link**: Establish mapping between R project and Obsidian folder (`obs r-dev link`)
2. **Operations**: Once linked, use `log`, `draft` commands which auto-detect context

This design allows users to work within their R project directory without specifying the Obsidian target repeatedly.
