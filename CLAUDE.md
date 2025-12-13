# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a ZSH-based CLI tool (`obs`) for managing a federated Obsidian vault system. The tool enables syncing themes/hotkeys across multiple sub-vaults and provides special integration with R development workflows.

## Core Architecture

### Main Script: `src/obs.zsh`

The script is designed as a ZSH function library that can be:
- Sourced and called as a function (`obs <command>`)
- Executed directly as a standalone script

**Key architectural components:**

1. **Configuration System**:
   - User config: `~/.config/obs/config` (defines `OBS_ROOT` and `VAULTS` array)
   - Project mapping: `~/.config/obs/project_map.json` (maps R project paths to Obsidian folders)

2. **Module Design**:
   - Core vault operations (sync, install, audit)
   - R-Dev integration module (link, log, context, draft)
   - All commands route through the main `obs()` dispatcher function

3. **Helper Functions**:
   - `_get_r_root()`: Climbs directory tree to find R project root (DESCRIPTION or .Rproj file)
   - `_get_mapped_path()`: Looks up Obsidian path for current R project in project_map.json
   - `_get_plugin_url()`: Searches Obsidian plugin registry cache for plugin repos

### R-Dev Integration Flow

The R-Dev module requires a two-step workflow:
1. **Link**: Establish mapping between R project and Obsidian folder (`obs r-dev link`)
2. **Operations**: Once linked, use `log`, `draft` commands which auto-detect context

This design allows users to work within their R project directory without specifying the Obsidian target repeatedly.

## Development Commands

### Testing

```bash
# Run Node.js test harness (Jest)
npm test

# Run shell integration tests for R-Dev module
bash tests/test_r_dev.sh
```

The shell tests create mock environments and verify the R-Dev workflow end-to-end.

### Linting and Formatting

```bash
# Lint
npm run lint

# Format all files
npm run format

# Check formatting without modifying
npx prettier --check .
```

### Documentation

```bash
# Serve docs locally
mkdocs serve

# Build docs
mkdocs build

# Deploy to GitHub Pages (automatic on push to main)
mkdocs gh-deploy --force
```

Docs are in `docs_mkdocs/` and deployed via GitHub Actions to GitHub Pages.

## Configuration Files

### `.eslintrc.js`
- Configured for Node.js and Jest environment
- Prettier integration for consistent style
- `no-console` rule disabled (CLI tool needs console output)

### `.prettierrc`
- Semicolons enabled
- Single quotes
- 2-space indentation
- ES5 trailing commas

### `jest.config.js`
- Node environment
- Matches test files: `**/*.test.js`, `**/*.spec.js`
- Currently configured but no JS test files exist yet (tests are in Bash)

## Key Implementation Details

### Plugin Installation
Uses GitHub API to fetch latest release assets from Obsidian community plugins. Downloads `main.js`, `manifest.json`, and `styles.css` to vault's `.obsidian/plugins/<id>/` directory.

### Vault Sync
Syncs `appearance.json`, `hotkeys.json`, `themes/`, and `snippets/` from root vault (`.obsidian/`) to all sub-vaults defined in `VAULTS` array.

### R-Dev Artifact Logging
Copies files to `06_Analysis` with timestamp prefix format: `YYYYMMDD_HHMMSS_<original_filename>`. This prevents overwrites and maintains chronological organization.

## Testing Strategy

Integration tests (Bash) verify:
- Project linking creates proper JSON mapping entries
- Artifact logging copies files with timestamps
- Context search finds Knowledge Base content
- Draft sync copies files to correct Obsidian folders

Tests use temporary directories and mock Obsidian vault structure.
