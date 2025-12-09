# Usage Guide

## Core Commands

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

### Audit Structure
Checks for "floating files" in the root directory that violate the organization rules.

```bash
obs audit
```
