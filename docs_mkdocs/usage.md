# Usage Guide

## Global Flags

All commands support the following global flags:

```bash
obs --verbose <command>  # Enable verbose debug logging
obs -v <command>         # Short form of --verbose
```

The verbose flag shows detailed information about:
- Directory traversal when finding R projects
- Configuration file loading
- Mapping lookups
- Internal operations

## Core Commands

### Check Dependencies
Verifies that required system dependencies are installed.

```bash
obs check
```

Required dependencies:
- `curl` - HTTP requests
- `jq` - JSON parsing
- `unzip` - Plugin extraction

### List Vaults
Shows configured vaults and R project mappings.

```bash
obs list
```

Output shows:
- Root vault location
- Sub-vaults with ✓ (exists) or ✗ (missing)
- Number of R project mappings
- Project name → Obsidian folder mappings

### Sync Configuration
Synchronizes `appearance.json`, `hotkeys.json`, `themes/`, and `snippets/` from the Root vault to all Sub-vaults.

```bash
obs sync          # Dry run (preview)
obs sync --force  # Execute sync
```

### Install Plugins
Installs a community plugin from GitHub to one or all vaults.

```bash
obs install dataview --all
obs install kanban --vault Research_Lab
```

### Search Plugins
Search the Obsidian community plugin registry.

```bash
obs search calendar
```

### Audit Structure
Checks for "floating files" in the root directory that violate the organization rules.

```bash
obs audit
```
