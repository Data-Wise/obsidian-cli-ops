# CLAUDE.md

Developer guide for Claude Code when working with this repository.

## Project Overview

**Obsidian CLI Ops (obs)** - Intelligent CLI tool for multi-vault Obsidian knowledge management with graph analysis and interactive TUI.

**Current Version**: 2.2.0-dev (Phase 5 Complete)
**Status**: Production ready (97% complete)
**Priority**: P2

### Core Features

- **Vault Management**: Discovery, scanning, synchronization across multiple vaults
- **Graph Analysis**: PageRank, centrality, clustering, orphan/hub detection
- **Interactive TUI**: Full-screen terminal UI with vim-style navigation
- **AI Features**: Multi-provider AI (Gemini API, Gemini CLI, Claude CLI, Ollama)
- **R-Dev Integration**: Seamless R Project ↔ Obsidian workflow

### Technology Stack

- **ZSH**: CLI interface (`src/obs.zsh`)
- **Python 3.9+**: Core logic (`src/python/`)
- **SQLite**: Knowledge graph database
- **NetworkX**: Graph analysis
- **Textual**: TUI framework
- **Gemini/Claude/Ollama**: Multi-provider AI (optional)
- **Jest**: Testing harness

## Architecture

**Three-Layer Design** (zero duplication principle):

```
Presentation → Application → Data
   (CLI/TUI)     (Core Logic)   (DB/Files)
```

- **Presentation**: `obs.zsh` (CLI), `tui/` (TUI)
- **Application**: `core/vault_manager.py`, `core/graph_analyzer.py`
- **Data**: `db_manager.py`, `vault_scanner.py`, `graph_builder.py`

**Key Principle**: Business logic lives in Core layer only. CLI and TUI are thin presentation layers that share 100% of business logic.

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

**Option D: Obsidian App Clone** - Just type `obs`!

```bash
# Primary commands (90% of usage)
obs                             # Open last vault (or show picker)
obs switch                      # Vault switcher
obs manage                      # Manage vaults

# Quick actions
obs open <name>                 # Open specific vault
obs graph [vault]               # Show graph visualization
obs stats [vault]               # View statistics

# R integration (shortened)
obs r link                      # Link R project (was: obs r-dev link)
obs r log <file>                # Copy artifact (was: obs r-dev log)

# Development
npm test                        # Run test suite (394+ tests)
python3 src/python/obs_cli.py --help  # Python CLI help
mkdocs serve                    # Serve docs locally
```

### Testing

```bash
npm test                          # Full test suite (394+ tests)
pytest src/python/tests/          # Python tests only (197 tests)
bash tests/test_r_dev.sh          # R-Dev integration tests
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
- `src/obs.zsh` - ZSH CLI interface (917 lines, Option D)
- `src/python/` - Python backend (~11,500 lines)
  - `core/` - Business logic (859 lines)
  - `tui/` - TUI screens (1,701 lines)
  - `obs_cli.py` - CLI interface (318 lines)
- `schema/vault_db.sql` - Database schema
- `tests/` - Test suite (394+ tests)

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

1. **Core Layer** (`src/python/core/vault_manager.py`):
   - Add business logic method (interface-agnostic)
   - Return domain model objects

2. **CLI Interface** (`src/python/obs_cli.py`):
   - Add argparse subcommand
   - Call core method
   - Format output for terminal

3. **TUI Interface** (`src/python/tui/screens/`):
   - Add key binding or button
   - Call same core method
   - Update widgets with results

4. **ZSH Wrapper** (`src/obs.zsh`):
   - Add wrapper function (optional)
   - Use full Python path: `/opt/homebrew/bin/python3`

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
- TUI screen tests for major workflows
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

## Option D: Obsidian App Clone

**Version 2.1.0** implements Option D - a complete redesign that mimics the official Obsidian app.

### Key Features

1. **Zero-Friction Start**: `obs` opens last vault automatically
2. **iCloud-First**: Auto-detects `~/Library/Mobile Documents/iCloud~md~obsidian/Documents`
3. **Last-Vault Tracking**: Saved to `~/.config/obs/last_vault`
4. **Obsidian-Style Commands**:
   - `obs` - Open last vault (like launching Obsidian)
   - `obs switch` - Vault switcher (like "Open another vault")
   - `obs manage` - Vault management (like "Manage Vaults" menu)
5. **Shortened Namespaces**: `obs r` (was `obs r-dev`)
6. **Progressive Help**: `obs help` (simple) vs `obs help --all` (detailed)

### Command Structure

```
Primary: obs, obs switch, obs manage
Actions: obs open, obs graph, obs stats
AI: obs ai similar, obs ai analyze, obs ai duplicates, obs ai status
R: obs r link, obs r log, obs r context
Legacy: obs discover, obs tui, obs vaults (still work)
```

### ADHD-Friendly Design

- **One command**: Just type `obs`
- **Smart defaults**: iCloud auto-detect, last-vault memory
- **Progressive disclosure**: Simple help by default
- **Visual hierarchy**: Emojis, clear categories
- **Reduced cognitive load**: 15 → 12 commands (-20%)

**See `OPTION_D_IMPLEMENTATION.md` for complete details.**

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
