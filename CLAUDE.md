# CLAUDE.md

Developer guide for Claude Code when working with this repository.

## Project Overview

**Obsidian CLI Ops (obs)** - Laser-focused CLI tool for Obsidian vault management with AI-powered graph analysis.

**Current Version**: 4.0.1
**Status**: Stable release
**Priority**: P1

> [!important] nexus-cli absorption — Phase 1 shipped in v4.0.0
> `obs` is the **survivor** of a merge with `nexus-cli` (RFC v2: `SPEC-merge-nexus-cli-v2-2026-06-21.md`, full Option-A absorption). **Phase 1 shipped in v4.0.0** (PR #37, `80cb505`): `obs config` (5 subcommands, `config_loader.py`) + `obs research` (11 subcommands — `research/` package: bibliography, courses, manuscript, pdf, zotero) + 27 new tests, all behind a **layered-AI** model (deterministic core default; AI opt-in). The MCP `nexus` client key is retired in favor of `obsidian-ops`. Non-vault domains stay scoped per RFC.

### Core Features

- **Vault Management**: Discovery, scanning across multiple vaults
- **Graph Analysis**: PageRank, centrality, clustering, orphan/hub detection
- **AI Features**: Multi-provider AI (Gemini API, Anthropic API, Gemini CLI, Claude CLI, Ollama)
- **Vault Health**: 4-dimension scoring (connectivity, link integrity, structure, freshness)
- **AI Refactor**: 3-phase vault reorganization pipeline (graph-only → AI-enhanced → prioritization)
- **Rich CLI Output**: Beautiful terminal output with tables, colors, progress bars
- **ZSH-First Architecture**: Fast shell integration with Python core

### Technology Stack

- **ZSH**: CLI interface (`src/obs.zsh`) - 501 lines
- **Python 3.9+**: Core logic (`src/python/`) - ~5,300 lines
- **SQLite**: Knowledge graph database
- **NetworkX**: Graph analysis
- **Rich**: CLI output formatting
- **Gemini/Anthropic/Claude/Ollama**: Multi-provider AI (optional)
- **Pytest**: Testing harness (360+ unit + 113 MCP unit + 32 E2E pytest)

## Architecture

**Three-Layer Design** (zero duplication principle):

```
Presentation → Application → Data
    (CLI)        (Core Logic)   (DB/Files)
```

- **Presentation**: `obs.zsh` (ZSH CLI wrapper)
- **Application**: `core/vault_manager.py`, `core/graph_analyzer.py`
- **Data**: `db_manager.py`, `vault_scanner.py`, `graph_builder.py`
- **AI Layer**: `ai/features.py`, `ai/features_vault.py`, `ai/features_refactor.py`, `ai/providers/`, `ai/models.py`

**Key Principle**: Business logic lives in Core layer only. CLI is a thin presentation layer.

**See `.claude/rules/architecture.md` for detailed documentation.**

## Quick Development Reference

### Installation & Setup

```bash
# Option 1: Homebrew (recommended)
brew install data-wise/tap/obsidian-cli-ops

# Option 2: Manual (isolated venv + symlink, no manual pip)
./install.sh
python3 src/python/obs_cli.py db init
```

### Essential Commands

**v3.4.0** - 25 commands (24 obs + 1 MCP-only):

```bash
# PRIMARY COMMANDS
obs                             # List vaults
obs search <query>              # Search notes by title (--vault, --limit, --json)
obs stats <vault>               # Show vault statistics (shows "Links: N (M broken)")
obs discover <path>             # Find vaults in directory

# GRAPH ANALYSIS
obs analyze <vault>             # Analyze vault graph metrics
obs health <vault>              # Vault health dashboard (scores + recommendations)

# AI FEATURES
obs ai status                   # Show AI provider status
obs ai setup                    # Interactive AI setup wizard
obs ai test                     # Test all providers
obs ai similar <note_id>        # Find similar notes
obs ai analyze <note_id>        # Analyze note with AI
obs ai duplicates <vault>       # Find duplicate notes
obs ai suggest-links <note_id>  # Suggest new links
obs ai gaps <vault>             # Find knowledge gaps
obs ai summarize <vault>        # Summarize vault themes
obs ai refactor <vault>         # AI-powered vault reorganization
obs ai merge-suggest <vault>    # Find merge candidates (v3.2.0)
obs ai tag-suggest <target>     # Suggest tags for untagged notes (v3.2.0)
obs ai quality <target>         # Score notes on quality dimensions (v3.2.0)

# UTILITIES
obs help [--all]                # Show help
obs version                     # Show version

# UTILITIES
obs help [--all]                # Show help
obs version                     # Show version

# Development
pytest src/python/tests/        # Run Python unit tests (360+ unit + 113 MCP)
pytest src/python/tests/test_mcp_server.py # Run MCP unit tests (113 tests)
E2E=1 pytest src/python/tests/e2e/ -v  # Run E2E tests (32 tests, gated)
python3 src/python/obs_cli.py --help  # Python CLI help
mkdocs serve                    # Serve docs locally
```

### Testing

```bash
pytest src/python/tests/        # 360+ unit tests passing
pytest src/python/tests/test_mcp_server.py # 113 MCP unit tests
E2E=1 pytest src/python/tests/e2e/ -v  # 32 E2E tests (requires real env)
npx jest                        # 69 Jest tests passing
obs --verbose <command>         # Run any command with verbose output
```

### Python Path Note

Shell scripts use full Python path `/opt/homebrew/bin/python3` to avoid PATH issues when called from unified dispatcher. As of v3.2.1, `obs.zsh` resolves the interpreter via `_obs_resolve_python` — priority: explicit `$OBS_PYTHON` → install.sh user venv (`~/.local/share/obs/venv`) → Homebrew formula venv (`libexec/venv`) → ambient `python3` (with a warning). It no longer silently trusts a bare `command -v python3` (that was the v3.2.0 clean-install crash). Core deps are pinned in `requirements.lock`.

## Key Locations

### Root Files

- `.STATUS` - Project status and metrics
- `README.md` - User-facing documentation
- `IDEAS.md` - Feature ideas and enhancements
- `CLAUDE.md` - This file

### Code Structure

- `src/obs.zsh` - ZSH CLI interface (501 lines)
- `src/python/` - Python backend
  - `core/` - Business logic (1,128 lines)
  - `obs_cli.py` - CLI interface (985 lines)
  - `ai/` - Multi-provider AI package (5 providers, 3,241 lines)
  - `tests/` - Test suite (360+ unit + 113 MCP unit + 32 E2E pytest tests)
- `schema/vault_db.sql` - Database schema (+ note_embeddings table)

### Documentation

- `docs_mkdocs/` - MkDocs Material site content (deployed to GitHub Pages)
- `docs/` - Legacy docs (organized by user/developer/planning)
- `.claude/rules/` - Auto-loaded rules (architecture, workflows, troubleshooting)

## Database Schema

**Location**: `schema/vault_db.sql`

**Core Tables**: vaults, notes, links, tags, graph_metrics, scan_history, note_embeddings
**Views**: orphaned_notes, hub_notes, broken_links

Details in schema file and `docs_mkdocs/developer/architecture.md`.

## Common Workflows

### Adding a New Command (Three-Layer Approach)

1. **Core Layer** (`src/python/core/vault_manager.py` or `graph_analyzer.py`):
   - Add business logic method (interface-agnostic)
   - Return domain model objects

2. **Python CLI** (`src/python/obs_cli.py`):
   - Add argparse subcommand
   - Call core method
   - Format output with Rich for terminal

3. **ZSH Wrapper** (`src/obs.zsh`):
   - Add wrapper function
   - Use full Python path: `/opt/homebrew/bin/python3`
   - Add to dispatcher case statement

**See `.claude/rules/workflows.md` for detailed examples.**

## Development Guidelines

### Code Quality

- Follow three-layer architecture strictly
- No business logic in presentation layers
- Use domain models for data transfer
- All Python calls use full path `/opt/homebrew/bin/python3`
- Keep test coverage above 70%

### Testing Requirements

- Unit tests for all core logic
- Integration tests for CLI commands
- Keep core tests passing (235+ tests)
- Update test count in documentation after adding tests

### Documentation

- Update `.STATUS` for progress tracking
- Add entries to `IDEAS.md` for future features
- Document new commands in appropriate docs
- Update version history for releases

### Git Workflow

- Work on feature branches in worktrees (`~/.git-worktrees/obsidian-cli-ops/`)
- Keep commits focused and atomic (conventional commits)
- Update relevant docs before committing
- Run tests before pushing

## Additional Resources

- **Architecture**: `.claude/rules/architecture.md`
- **Workflows**: `.claude/rules/workflows.md`
- **Troubleshooting**: `.claude/rules/troubleshooting.md`
- **Published Docs**: https://data-wise.github.io/obsidian-cli-ops/
- **Homebrew**: `data-wise/tap/obsidian-cli-ops`
