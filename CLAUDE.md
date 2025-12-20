# CLAUDE.md

Developer guide for Claude Code when working with this repository.

## Project Overview

**Obsidian CLI Ops (obs)** - Intelligent CLI tool for multi-vault Obsidian knowledge management with graph analysis and interactive TUI.

| Metric | Value |
|--------|-------|
| Version | 2.2.0 |
| Status | Production ready (98% complete) |
| Tests | 398/461 passing (86% pass rate) |
| Priority | P2 |

### Core Features

- **Vault Management**: Discovery, scanning, synchronization across multiple vaults
- **Graph Analysis**: PageRank, centrality, clustering, orphan/hub detection
- **Interactive TUI**: Full-screen terminal UI with vim-style navigation
- **AI Features**: Multi-provider AI (Gemini API, Gemini CLI, Claude CLI, Ollama)
- **R-Dev Integration**: Seamless R Project ↔ Obsidian workflow

### Technology Stack

- **ZSH/Python**: CLI interface (`src/obs.zsh`) + Core logic (`src/python/`)
- **SQLite + NetworkX**: Knowledge graph database and analysis
- **Textual**: TUI framework
- **Gemini/Claude/Ollama**: Multi-provider AI (optional)

## Architecture

**Three-Layer Design** (zero duplication principle):

```
Presentation → Application → Data
   (CLI/TUI)     (Core Logic)   (DB/Files)
```

- **Presentation**: `obs.zsh` (CLI), `tui/` (TUI)
- **Application**: `core/vault_manager.py`, `core/graph_analyzer.py`
- **Data**: `db_manager.py`, `vault_scanner.py`, `graph_builder.py`

**Key Principle**: Business logic lives in Core layer only. CLI and TUI share 100% of business logic.

**See `.claude/rules/architecture.md` for detailed documentation.**

## Quick Reference

### Setup

```bash
pip3 install -r src/python/requirements.txt
python3 src/python/obs_cli.py db init
```

### Essential Commands

```bash
# Primary (90% of usage)
obs                      # Open last vault (or show picker)
obs switch               # Vault switcher
obs manage               # Manage vaults

# Quick actions
obs open <name>          # Open specific vault
obs graph [vault]        # Graph visualization
obs stats [vault]        # View statistics

# Development
npm test                 # Full test suite
pytest src/python/tests/ # Python tests only
mkdocs serve             # Serve docs locally
```

### Testing

```bash
npm test                          # Full test suite (461 tests)
pytest src/python/tests/          # Python tests (398 passing)
bash tests/test_r_dev.sh          # R-Dev integration tests
```

## Key Locations

| Path | Description |
|------|-------------|
| `src/obs.zsh` | ZSH CLI interface (929 lines) |
| `src/python/` | Python backend (~17,000 lines) |
| `src/python/core/` | Business logic (932 lines) |
| `src/python/tui/` | TUI screens |
| `schema/vault_db.sql` | Database schema |
| `tests/` | Test suite |

### Documentation

| Path | Description |
|------|-------------|
| `.STATUS` | Project status and metrics |
| `docs/` | All documentation |
| `.claude/rules/` | Auto-loaded rules (architecture, workflows, troubleshooting) |

## Common Workflows

### Adding a New Command (Three-Layer Approach)

1. **Core Layer** (`src/python/core/vault_manager.py`): Add business logic method
2. **CLI Interface** (`src/python/obs_cli.py`): Add argparse subcommand
3. **TUI Interface** (`src/python/tui/screens/`): Add key binding or button
4. **ZSH Wrapper** (`src/obs.zsh`): Add wrapper function (optional)

**See `.claude/rules/workflows.md` for detailed examples.**

## Development Guidelines

### Code Quality
- Follow three-layer architecture strictly
- No business logic in presentation layers
- Use domain models for data transfer
- Keep test coverage above 70%

### Testing Requirements
- Unit tests for all core logic
- Integration tests for CLI commands
- TUI screen tests for major workflows

### Git Workflow
- Work on feature branches
- Run tests before pushing

## Database Schema

**Location**: `schema/vault_db.sql`

**Core Tables**: vaults, notes, links, tags, graph_metrics, scan_history

**Views**: orphaned_notes, hub_notes, broken_links

## Additional Resources

| Resource | Path |
|----------|------|
| Architecture | `.claude/rules/architecture.md` |
| Workflows | `.claude/rules/workflows.md` |
| Troubleshooting | `.claude/rules/troubleshooting.md` |
| Project Hub | `docs/planning/project-hub.md` |
| Published Docs | https://data-wise.github.io/obsidian-cli-ops/ |

---

**Note**: This file focuses on quick developer reference. For comprehensive documentation, see `docs/` and `.claude/rules/`.
