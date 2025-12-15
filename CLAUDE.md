# CLAUDE.md

This file provides guidance to Claude Code when working with code in this repository.

## Project Overview

**Obsidian CLI Ops (obs)** is an intelligent command-line tool for managing multi-vault Obsidian systems with knowledge graph analysis and R development integration.

**Current Version**: 2.0.0-beta
**Status**: Phase 4 TUI Complete (100%)

### What It Does

- **v1.x Features**: Federated vault management, plugin installation, R-Dev integration
- **v2.0 Features**: Knowledge graph analysis, vault scanning, link resolution, graph metrics, AI-powered similarity detection (100% free, local, private)

### Technology Stack

- **ZSH**: Main CLI interface (`src/obs.zsh`)
- **Python 3.9+**: Backend for v2.0 features (`src/python/`)
- **SQLite**: Knowledge graph database (`~/.config/obs/vault_db.sqlite`)
- **NetworkX**: Graph analysis library
- **Textual**: TUI framework for interactive interface
- **HuggingFace/Ollama**: Free local AI (embeddings, similarity detection)
- **Node.js**: Testing harness (Jest)
- **MkDocs**: Documentation site

## Quick Command Reference

### Vault Discovery and Scanning

```bash
# Discover vaults in directory
obs discover ~/Documents -v

# Discover and scan automatically
obs discover ~/Documents --scan -v

# Scan specific vault
python3 src/python/obs_cli.py scan /path/to/vault --analyze -v
```

### Graph Analysis

```bash
# List all vaults (get vault IDs)
obs vaults

# Analyze vault graph
obs analyze <vault_id> -v

# View statistics
obs stats                    # Global stats
obs stats <vault_id>         # Vault-specific stats
```

### TUI Interface

```bash
# Launch interactive TUI
obs tui

# Open specific vault
obs tui --vault-id <id>

# Open specific screen
obs tui --screen vaults|notes|graph|stats
```

### Database Management

```bash
# Initialize/rebuild database
python3 src/python/obs_cli.py db init

# View database stats
python3 src/python/obs_cli.py db stats
```

## Development Commands

### Python Dependencies

```bash
# Install required packages (Phase 1)
pip3 install python-frontmatter mistune PyYAML networkx

# Install TUI packages
pip3 install textual rich

# Install AI packages (Phase 2)
pip3 install sentence-transformers numpy scikit-learn
```

### Testing

```bash
# Run Node.js test harness (Jest)
npm test

# Run shell integration tests for R-Dev module
bash tests/test_r_dev.sh

# Test Python CLI directly
python3 src/python/obs_cli.py --help
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

## Database Schema

**Location:** `schema/vault_db.sql`

**Tables:**
- `vaults`: Vault metadata
- `notes`: Note content, metadata, hashes
- `links`: Wikilink relationships (source → target)
- `tags`: Tag definitions
- `note_tags`: Many-to-many tag-note relationships
- `graph_metrics`: PageRank, centrality, clustering
- `scan_history`: Scan tracking and analytics

**Views:**
- `orphaned_notes`: Notes with no incoming/outgoing links
- `hub_notes`: Highly connected notes (>10 links)
- `broken_links`: Unresolved wikilinks

## Important Files

- `PROJECT_HUB.md`: ADHD-friendly control center
- `PROJECT_PLAN_v2.0.md`: Complete 12-week roadmap
- `.STATUS`: Comprehensive project status and metrics
- `V2_QUICKSTART.md`: Quick start guide for v2.0
- `PHASE_1_COMPLETE.md`: Phase 1 summary and usage
- `PHASE_2_COMPLETE.md`: Phase 2 AI integration summary
- `PHASE_4_TUI_PLAN.md`: Phase 3 TUI implementation plan (452 lines)
- `TEST_SUITE_SUMMARY.md`: Test suite documentation (162+ tests)
- `src/python/README.md`: Python module documentation

## Project Roadmap

### Phase 1: Foundation ✅ COMPLETE
- Database schema and manager
- Vault scanner with markdown parsing
- Graph builder with NetworkX
- CLI integration

### Phase 2: AI Integration ✅ COMPLETE
- FREE local AI providers (HuggingFace + Ollama)
- Interactive setup wizard with auto-detection
- Embedding generation (384-1024 dimensions)
- Note comparison using cosine similarity

### Phase 3: TUI/Visualization ✅ COMPLETE
- Interactive vault browser (Textual framework)
- Note explorer with search/preview
- Graph visualization (ASCII art)
- Statistics dashboard
- Keyboard navigation (arrows, vim keys, mouse)

### Phase 4: AI-Powered Features (Next)
- Find similar notes
- Detect duplicates
- Topic analysis and clustering
- Merge suggestions with reasoning

## Architecture

**Three-Layer Design:**
- **Presentation Layer**: CLI (`obs_cli.py`), TUI (`tui/`), ZSH wrapper (`obs.zsh`)
- **Application Layer**: Core business logic (`core/vault_manager.py`, `core/graph_analyzer.py`)
- **Data Layer**: Database, file scanning, graph building

**See `.claude/rules/architecture.md` for detailed architecture documentation.**

## Additional Documentation

Detailed documentation has been split into focused rule files in `.claude/rules/`:

- **architecture.md** - Three-layer design, module structure, implementation details
- **workflows.md** - Common workflows, adding new commands
- **skills.md** - Claude Code skills documentation
- **troubleshooting.md** - Troubleshooting guide and performance tips

These files are automatically loaded by Claude Code when working in relevant paths.

## Version History

- **2.0.0-beta** (2025-12-15):
  - Phase 1: Foundation, scanning, graph analysis (COMPLETE)
  - Phase 2: Free AI integration (HuggingFace + Ollama) (COMPLETE)
  - Phase 3: TUI/Visualization (COMPLETE)
  - Claude Code Skills for docs/knowledge/wrap-up workflow
  - Interactive setup wizard with auto-detection
  - Complete test suite (122 tests, 70% coverage)
- **1.1.0** (2025-12-11): Quick wins - list, stats, unlink, completion
- **1.0.0** (2025-12-10): Initial release - vault management, R-Dev integration
