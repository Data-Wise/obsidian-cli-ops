# CLAUDE.md

Developer guide for Claude Code when working with this repository.

## Project Overview

**Obsidian CLI Ops (obs)** - Laser-focused CLI tool for Obsidian vault management with AI-powered graph analysis.

**Current Version**: 3.0.0-dev (Phase 7.1 Simplification - In Progress)
**Status**: Active development (Proposal A implementation)
**Priority**: P1

### Core Features (v3.0.0)

- **Vault Management**: Discovery, scanning across multiple vaults
- **Graph Analysis**: PageRank, centrality, clustering, orphan/hub detection
- **AI Features**: Multi-provider AI (Gemini API, Gemini CLI, Claude CLI, Ollama)
- **Rich CLI Output**: Beautiful terminal output with tables, colors, progress bars
- **ZSH-First Architecture**: Fast shell integration with Python core

### Technology Stack

- **ZSH**: CLI interface (`src/obs.zsh`) - 386 lines
- **Python 3.9+**: Core logic (`src/python/`) - ~3,500 lines
- **SQLite**: Knowledge graph database
- **NetworkX**: Graph analysis
- **Rich**: CLI output formatting
- **Gemini/Claude/Ollama**: Multi-provider AI (optional)
- **Pytest**: Testing harness

## Architecture

**Three-Layer Design** (zero duplication principle):

```
Presentation → Application → Data
    (CLI)        (Core Logic)   (DB/Files)
```

- **Presentation**: `obs.zsh` (ZSH CLI wrapper)
- **Application**: `core/vault_manager.py`, `core/graph_analyzer.py`
- **Data**: `db_manager.py`, `vault_scanner.py`, `graph_builder.py`

**Key Principle**: Business logic lives in Core layer only. CLI is a thin presentation layer.

**v3.0.0 Changes**: Removed TUI (1,701 lines) and R-Dev integration (307 lines) to focus on core Obsidian management.

**See `.claude/rules/architecture.md` for detailed documentation.**

## Quick Development Reference

### Installation & Setup

```bash
# Install dependencies
pip3 install -r src/python/requirements.txt

# Initialize database
python3 src/python/obs_cli.py db init

# Symlink for CLI usage
ln -s "$(pwd)/src/obs.zsh" ~/.config/zsh/functions/obs.zsh
```

### Essential Commands

**v3.0.0 Simplified CLI** - 10 focused commands!

```bash
# PRIMARY COMMANDS
obs                             # List vaults
obs stats <vault_id>            # Show vault statistics
obs discover <path>             # Find vaults in directory

# GRAPH ANALYSIS
obs analyze <vault_id>          # Analyze vault graph metrics

# AI FEATURES
obs ai status                   # Show AI provider status
obs ai setup                    # Interactive AI setup wizard
obs ai test                     # Test all providers
obs ai similar <note_id>        # Find similar notes
obs ai analyze <note_id>        # Analyze note with AI
obs ai duplicates <vault_id>    # Find duplicate notes

# UTILITIES
obs help [--all]                # Show help
obs version                     # Show version

# Development
pytest src/python/tests/        # Run Python tests (35+ core tests)
python3 src/python/obs_cli.py --help  # Python CLI help
mkdocs serve                    # Serve docs locally
```

### Testing

```bash
pytest src/python/tests/        # Python tests (35+ core tests passing)
obs --verbose <command>         # Run any command with verbose output
```

### Python Path Note

⚠️ **Important**: Shell scripts use full Python path `/opt/homebrew/bin/python3` to avoid PATH issues when called from unified dispatcher. Update all Python calls to use full path.

## Key Locations

### Root Files
- `.STATUS` - Project status and metrics
- `README.md` - User-facing documentation
- `IDEAS.md` - Feature ideas and enhancements
- `CLAUDE.md` - This file

### Code Structure

- `src/obs.zsh` - ZSH CLI interface (386 lines, v3.0.0)
- `src/python/` - Python backend (~3,500 lines)
  - `core/` - Business logic (859 lines)
  - `obs_cli.py` - CLI interface (318 lines)
  - AI clients - Multi-provider AI (440+ lines)
- `schema/vault_db.sql` - Database schema
- `tests/` - Test suite (35+ core tests passing)

### Documentation
- `docs/` - All documentation (organized by user/developer/planning)
- `docs/developer/architecture.md` - Detailed architecture
- `docs/developer/testing/` - Testing guides
- `.claude/rules/` - Auto-loaded rules (architecture, workflows, troubleshooting)
- `.claude/skills/` - Custom Claude Code skills

## Database Schema

**Location**: `schema/vault_db.sql`

**Core Tables**: vaults, notes, links, tags, graph_metrics, scan_history
**Views**: orphaned_notes, hub_notes, broken_links

Details in schema file and `docs/developer/architecture.md`.

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
- Keep core tests passing (35+ tests)
- Update test count in documentation

### Documentation
- Update `.STATUS` for progress tracking
- Add entries to `IDEAS.md` for future features
- Document new commands in appropriate docs
- Update version history for releases

### Git Workflow
- Work on feature branches
- Keep commits focused and atomic
- Update relevant docs before committing
- Run tests before pushing

## v3.0.0 Simplification (Proposal A)

**Version 3.0.0-dev** implements Proposal A - "Do one thing exceptionally well - manage Obsidian vaults"

### Key Changes

1. **Simplified CLI**: 20+ commands → 10 focused commands
2. **Removed Features**:
   - TUI interface (1,701 lines) - CLI-only for simplicity
   - R-Dev integration (307 lines) - Belongs in R package ecosystem
   - Legacy v1.x commands (126 lines) - Plugin install, sync, audit
3. **Code Reduction**: 11,500 → ~7,400 lines (36% so far, target 61%)
4. **ZSH-First**: Fast shell integration with Python core

### Command Structure (v3.0.0)

```
PRIMARY: obs, obs stats, obs discover
GRAPH: obs analyze
AI: obs ai status/setup/test/similar/analyze/duplicates
UTILITIES: obs help, obs version
```

### ADHD-Friendly Design (Retained)

- **One command**: Just type `obs`
- **Smart defaults**: iCloud auto-detect, last-vault memory
- **Progressive disclosure**: Simple help by default
- **Visual hierarchy**: Emojis, clear categories
- **Reduced cognitive load**: 20+ → 10 commands (50% reduction)

**See `PROPOSAL-REFOCUS-2025-12-20.md` and `REFOCUS-SUMMARY.md` for complete details.**

## Additional Resources

### Detailed Documentation
- **Architecture**: `.claude/rules/architecture.md` (890 lines)
- **Workflows**: `.claude/rules/workflows.md`
- **Troubleshooting**: `.claude/rules/troubleshooting.md`
- **Skills**: `.claude/rules/skills.md`

### Planning & Status
- **Project Hub**: `docs/planning/project-hub.md` (ADHD-friendly)
- **Project Plan**: `docs/planning/project-plan.md` (complete roadmap)
- **Phase Summaries**: `docs/planning/phases/`
- **Test Overview**: `docs/developer/testing/overview.md`

### External Links
- **Published Docs**: https://data-wise.github.io/obsidian-cli-ops/
- **Repository**: https://github.com/Data-Wise/obsidian-cli-ops

---

**Note**: This file focuses on quick developer reference. For comprehensive documentation, see `docs/` directory and `.claude/rules/`.
