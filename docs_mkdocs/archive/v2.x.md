# v2.x Documentation Archive

This directory contains documentation for features that were removed in v3.0.0 as part of Proposal A (Pure Obsidian Manager).

## What's Archived Here

### TUI Guides (`tui-guides/`)

Documentation for the Terminal User Interface (TUI) that was removed in v3.0.0:

- **README.md** - TUI overview and navigation guide
- **quick-reference.md** - Keyboard shortcuts reference
- **vim-tutorial.md** - Vim-style navigation tutorial for beginners
- **cheat-sheet.txt** - Printable keyboard shortcuts cheat sheet

**Why Removed:**
- 1,701 lines of code
- Duplicated CLI functionality
- Required Textual dependency (~500KB)
- Maintenance burden without unique value

**Alternatives:** All TUI functionality is available via CLI commands. See `MIGRATION.md` for command mappings.

### Removed Features (`removed-features/`)

Documentation for other features removed in v3.0.0:

- R-Dev integration (307 lines)
- Legacy v1.x commands (126 lines)

## Accessing v2.x

If you need the full v2.x version with TUI and R-Dev integration:

```bash
# Checkout v2.2.0 (stable release)
git checkout v2.2.0

# Or browse on GitHub
https://github.com/Data-Wise/obsidian-cli-ops/tree/v2.2.0
```

## Migration Guide

For migrating from v2.x to v3.0.0, see:
- **MIGRATION.md** in the repository root
- https://data-wise.github.io/obsidian-cli-ops/

## Questions?

- **GitHub Issues**: https://github.com/Data-Wise/obsidian-cli-ops/issues
- **Documentation**: https://data-wise.github.io/obsidian-cli-ops/

---

**Archive Date:** 2025-12-20
**Last v2.x Release:** v2.2.0
**Archived By:** Phase 7.1 Part 4 (Documentation cleanup)
