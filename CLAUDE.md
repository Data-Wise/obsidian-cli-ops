# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Obsidian CLI Ops (obs)** is an intelligent command-line tool for managing multi-vault Obsidian systems with knowledge graph analysis and R development integration.

**Current Version**: 2.0.0-beta

### What It Does

- **v1.x Features**: Federated vault management, plugin installation, R-Dev integration
- **v2.0 Features**: Knowledge graph analysis, vault scanning, link resolution, graph metrics, AI-powered similarity detection (100% free, local, private)

### Technology Stack

- **ZSH**: Main CLI interface (`src/obs.zsh`)
- **Python**: Backend for v2.0 features (`src/python/`)
- **SQLite**: Knowledge graph database (`~/.config/obs/vault_db.sqlite`)
- **NetworkX**: Graph analysis library
- **HuggingFace/Ollama**: Free local AI (embeddings, similarity detection)
- **Node.js**: Testing harness (Jest)
- **MkDocs**: Documentation site

## Core Architecture

### Two-Layer Design

#### Layer 1: ZSH CLI (`src/obs.zsh`)
- Main user interface
- Configuration management
- Vault operations (sync, install, audit)
- R-Dev integration
- Routes v2.0 commands to Python backend

#### Layer 2: Python Backend (`src/python/`)
- Database management
- Vault scanning and parsing
- Graph analysis and metrics
- Knowledge extraction
- AI integration (HuggingFace, Ollama)
- Interactive setup wizard

### Main Script: `src/obs.zsh`

The script is designed as a ZSH function library that can be:
- Sourced and called as a function (`obs <command>`)
- Executed directly as a standalone script

**Key architectural components:**

1. **Configuration System**:
   - User config: `~/.config/obs/config` (defines `OBS_ROOT` and `VAULTS` array)
   - Project mapping: `~/.config/obs/project_map.json` (maps R project paths to Obsidian folders)
   - Database: `~/.config/obs/vault_db.sqlite` (knowledge graph storage)
   - AI config: `~/.config/obs/ai_config.json` (AI provider and model settings)

2. **Command Routing**:
   - Commands that don't need config: `help`, `version`, `check`, `discover`, `analyze`, `vaults`, `stats`, `ai`
   - Commands that need config: `list`, `sync`, `install`, `search`, `audit`, `r-dev`

3. **Helper Functions**:
   - `_get_r_root()`: Climbs directory tree to find R project root
   - `_get_mapped_path()`: Looks up Obsidian path for current R project
   - `_get_plugin_url()`: Searches Obsidian plugin registry
   - `_get_python_cli()`: Locates Python CLI for v2.0 commands

### Python Module: `src/python/`

**Module Structure:**

```
src/python/
├── __init__.py           # Package initialization
├── db_manager.py         # Database operations (469 lines)
├── vault_scanner.py      # Vault scanning & parsing (373 lines)
├── graph_builder.py      # Graph analysis (307 lines)
├── obs_cli.py            # CLI entry point (318 lines)
├── ai_client.py          # AI client base & factory (440 lines)
├── ai_client_ollama.py   # Ollama integration (450 lines)
├── ai_client_hf.py       # HuggingFace integration (340 lines)
├── setup_wizard.py       # Interactive AI setup (837 lines)
├── similarity_analyzer.py # Note similarity analysis (470 lines)
├── requirements.txt      # Python dependencies
└── README.md             # Python module documentation
```

**Key Classes:**

1. **DatabaseManager** (`db_manager.py`):
   - `get_connection()`: Context manager for DB connections
   - `add_vault()`, `get_vault()`, `list_vaults()`: Vault operations
   - `add_note()`, `get_note()`, `list_notes()`: Note operations
   - `add_link()`, `get_outgoing_links()`, `get_incoming_links()`: Link operations
   - `add_tag()`, `get_note_tags()`, `get_tag_stats()`: Tag operations
   - `get_orphaned_notes()`, `get_hub_notes()`, `get_broken_links()`: Graph queries

2. **VaultScanner** (`vault_scanner.py`):
   - `discover_vaults()`: Finds vaults by `.obsidian` directory
   - `scan_vault()`: Parses all markdown files and populates database
   - **MarkdownParser**: Extracts frontmatter, wikilinks, tags, metadata

3. **GraphBuilder** (`graph_builder.py`):
   - **LinkResolver**: Resolves wikilinks to note IDs
   - `build_graph()`: Constructs NetworkX directed graph
   - `calculate_metrics()`: PageRank, centrality, clustering
   - `find_clusters()`: Community detection
   - `analyze_vault()`: Complete analysis pipeline

4. **ObsCLI** (`obs_cli.py`):
   - Argparse-based CLI interface
   - Commands: discover, scan, analyze, stats, vaults, db, ai
   - Verbose mode support

5. **AI Clients** (`ai_client.py`, `ai_client_ollama.py`, `ai_client_hf.py`):
   - **AIClient**: Abstract base class for AI providers
   - **OllamaClient**: Local Ollama integration (embeddings + reasoning)
   - **HuggingFaceClient**: sentence-transformers integration (embeddings)
   - **get_ai_client()**: Factory function for provider selection
   - Support for multiple models (qwen2.5:0.5b, llama3.1, all-mpnet-base-v2, etc.)

6. **AISetupWizard** (`setup_wizard.py`):
   - Interactive setup with two paths (Quick Start, Custom)
   - System auto-detection (OS, Python, RAM, Ollama)
   - Provider and model selection menus
   - Automatic installation and testing
   - Config persistence to `~/.config/obs/ai_config.json`
   - Progress bars with `rich` library

7. **SimilarityAnalyzer** (`similarity_analyzer.py`):
   - Find similar notes using embeddings
   - Duplicate detection with threshold
   - Topic analysis and clustering
   - Merge suggestions with reasoning

### Database Schema: `schema/vault_db.sql`

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

**Triggers:**
- Auto-update vault note counts
- Auto-update tag counts
- Auto-update graph in/out degrees

### R-Dev Integration Flow

The R-Dev module requires a two-step workflow:
1. **Link**: Establish mapping between R project and Obsidian folder (`obs r-dev link`)
2. **Operations**: Once linked, use `log`, `draft` commands which auto-detect context

This design allows users to work within their R project directory without specifying the Obsidian target repeatedly.

## Development Commands

### Python Dependencies

```bash
# Install required packages (Phase 1)
pip3 install python-frontmatter mistune PyYAML networkx

# Install AI packages (Phase 2)
# Option 1: HuggingFace (recommended, free forever)
pip3 install sentence-transformers numpy scikit-learn rich

# Option 2: Ollama (requires Ollama installed)
brew install ollama
pip3 install requests numpy rich

# Optional: Run interactive setup wizard
obs ai setup --quick

# Optional paid APIs (commented out in requirements.txt)
# pip3 install anthropic google-generativeai
```

### Testing

```bash
# Run Node.js test harness (Jest)
npm test

# Run shell integration tests for R-Dev module
bash tests/test_r_dev.sh

# Test Python CLI directly
python3 src/python/obs_cli.py --help
python3 src/python/obs_cli.py db init
python3 src/python/obs_cli.py stats

# Test individual Python modules
python3 src/python/db_manager.py
python3 src/python/vault_scanner.py /path/to/vault
python3 src/python/graph_builder.py <vault_id>
```

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

### `mkdocs.yml`
- Material theme with custom colors
- Code highlighting for multiple languages
- GitHub repository integration

## Key Implementation Details

### Plugin Installation (v1.x)
Uses GitHub API to fetch latest release assets from Obsidian community plugins. Downloads `main.js`, `manifest.json`, and `styles.css` to vault's `.obsidian/plugins/<id>/` directory.

### Vault Sync (v1.x)
Syncs `appearance.json`, `hotkeys.json`, `themes/`, and `snippets/` from root vault (`.obsidian/`) to all sub-vaults defined in `VAULTS` array.

### R-Dev Artifact Logging (v1.x)
Copies files to `06_Analysis` with timestamp prefix format: `YYYYMMDD_HHMMSS_<original_filename>`. This prevents overwrites and maintains chronological organization.

### Vault Scanning (v2.0)
1. Discovers vaults by searching for `.obsidian` directories
2. Parses markdown files with `python-frontmatter` library
3. Extracts wikilinks using regex: `\[\[([^\]|]+)(?:\|([^\]]+))?\]\]`
4. Extracts tags using regex: `#([a-zA-Z0-9_/-]+)`
5. Stores content hash (SHA256) for change detection
6. Populates database with notes, links, tags

### Link Resolution (v2.0)
1. Builds cache of note paths, titles, and aliases
2. Resolves wikilinks by trying multiple strategies:
   - Exact path match
   - Path without `.md` extension
   - Relative path from source note
   - Filename only match
3. Updates links table with resolved `target_note_id`
4. Marks unresolved links as `broken`

### Graph Analysis (v2.0)
1. Constructs NetworkX `DiGraph` from database links
2. Calculates metrics:
   - **PageRank**: Importance score based on link structure
   - **In/Out Degree**: Number of incoming/outgoing links
   - **Betweenness Centrality**: How often note is on path between others
   - **Closeness Centrality**: Average distance to all other notes
   - **Clustering Coefficient**: How connected note's neighbors are
3. Updates `graph_metrics` table
4. Identifies special notes (orphans, hubs)

## v2.0 Command Reference

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

### Database Management

```bash
# Initialize/rebuild database
python3 src/python/obs_cli.py db init

# View database stats
python3 src/python/obs_cli.py db stats
```

### AI Setup and Configuration

```bash
# Interactive setup wizard (recommended)
obs ai setup

# Quick start (auto-detect and install)
obs ai setup --quick

# View current configuration
obs ai config

# Test AI clients directly (Python)
python3 src/python/ai_client_ollama.py
python3 src/python/ai_client_hf.py

# Run setup wizard directly
python3 src/python/setup_wizard.py --quick
```

## Testing Strategy

### Node.js Tests (Jest)
- Help command output validation
- Error handling for missing config
- Verbose mode functionality
- Config file validation
- Script structure verification

### Shell Tests (Bash)
- Project linking creates proper JSON mapping entries
- Artifact logging copies files with timestamps
- Context search finds Knowledge Base content
- Draft sync copies files to correct Obsidian folders

### Python Module Tests (Future)
- Database operations
- Markdown parsing accuracy
- Link resolution correctness
- Graph metric calculations

## Project Roadmap

### Phase 1: Foundation ✅ COMPLETE
- Database schema and manager
- Vault scanner with markdown parsing
- Graph builder with NetworkX
- CLI integration

### Phase 2: AI Integration ✅ COMPLETE
- **FREE local AI providers** (HuggingFace + Ollama)
- Interactive setup wizard with auto-detection
- Embedding generation (384-1024 dimensions)
- Note comparison using cosine similarity
- **Privacy-first**: 100% free, 100% local, 100% private
- Multi-provider architecture (easy to add more)
- **Documentation**: Complete setup guide with troubleshooting

### Phase 3: TUI/Visualization 🚧 IN PROGRESS
**Priority:** HIGH (moved ahead of Phase 4)
**Started:** 2025-12-13
**Plan:** See PHASE_4_TUI_PLAN.md

**Features:**
- Interactive vault browser (using Textual framework)
- Note explorer with search/preview
- Graph visualization (ASCII art)
- Statistics dashboard
- Keyboard navigation (arrows, vim keys, mouse)
- ADHD-friendly design (colors, emojis, clear hierarchy)

**Commands:**
- `obs tui` - Launch TUI application
- `obs tui --vault-id <id>` - Open specific vault
- `obs tui --screen <name>` - Open specific screen

**Rationale:**
- Can visualize existing Phase 1 data immediately
- Better UX for vault exploration
- Foundation ready when Phase 4 features arrive
- Standalone utility value

### Phase 4: AI-Powered Features (Deferred)
**Status:** Deferred (Phase 3 prioritized)
**Will integrate with:** Phase 3 TUI when complete

**Features:**
- Find similar notes (`obs ai similar`)
- Detect duplicates (`obs ai duplicates`)
- Topic analysis and clustering (`obs ai topics`)
- Merge suggestions with reasoning
- Single note analysis
- TUI review interface for suggestions

### Phase 5: Learning System (Planned)
- User feedback collection
- Rule generation
- Accuracy improvement
- Personalized suggestions

### Phase 6: Automation (Planned)
- Automated vault watching
- Scheduled scans
- Automatic AI-powered suggestions
- Background processing

## Important Files

### Documentation
- `PROJECT_HUB.md`: ADHD-friendly control center
- `PROJECT_PLAN_v2.0.md`: Complete 12-week roadmap (phase reordering: TUI before AI features)
- `.STATUS`: Comprehensive project status and metrics
- `V2_QUICKSTART.md`: Quick start guide for v2.0
- `PHASE_1_COMPLETE.md`: Phase 1 summary and usage
- `PHASE_2_COMPLETE.md`: Phase 2 AI integration summary
- `PHASE_4_TUI_PLAN.md`: Phase 3 TUI implementation plan (452 lines)
- `AI_SETUP_QUICKSTART.md`: One-page AI setup guide
- `docs_mkdocs/ai-setup.md`: Complete AI setup documentation (741 lines)
- `TEST_SUITE_SUMMARY.md`: Test suite documentation (162+ tests)
- `src/python/README.md`: Python module documentation

### Examples
- `config/example.project_map.json`: R project mapping template

### Schema
- `schema/vault_db.sql`: Complete database schema with comments

## Common Workflows

### Adding a New v2.0 Command

1. Add function to `src/python/obs_cli.py`:
   ```python
   def new_command(self, arg1, arg2):
       """Do something."""
       # Implementation
   ```

2. Add argument parser in `main()`:
   ```python
   new_parser = subparsers.add_parser('new', help='New command')
   new_parser.add_argument('arg1', help='Argument 1')
   ```

3. Add dispatch in `main()`:
   ```python
   elif args.command == 'new':
       cli.new_command(args.arg1, args.arg2)
   ```

4. Add ZSH wrapper to `src/obs.zsh`:
   ```zsh
   obs_new() {
       local python_cli=$(_get_python_cli) || return 1
       python3 "$python_cli" new "$@"
   }
   ```

5. Update help text in `obs_help()`

6. Add to dispatch in `obs()` function

### Extending the Database

1. Update `schema/vault_db.sql` with new table/column
2. Increment version in `schema_version` table
3. Add corresponding methods to `DatabaseManager`
4. Update views/triggers if needed
5. Test with `python3 src/python/db_manager.py`

### Adding New Graph Metrics

1. Add calculation in `GraphBuilder.calculate_metrics()`
2. Update `graph_metrics` table schema if needed
3. Add query method in `DatabaseManager`
4. Expose in CLI commands

## Dependencies and Requirements

### System Requirements
- macOS, Linux, or WSL2
- ZSH shell
- Python 3.9+
- Node.js 18+ (for testing)

### Required CLI Tools
- `curl`: API requests
- `jq`: JSON parsing
- `unzip`: Plugin extraction
- `git`: Version control

### Python Packages
- `python-frontmatter`: YAML frontmatter parsing
- `mistune`: Markdown rendering
- `PyYAML`: YAML parsing
- `networkx`: Graph analysis

### AI Packages (Phase 2)
- `sentence-transformers`: HuggingFace embeddings (recommended, free)
- `requests`: Ollama API client
- `numpy`: Numerical operations
- `scikit-learn`: Clustering and similarity
- `rich`: Terminal UI for setup wizard

### Optional Python Packages
- `anthropic`: Claude API (paid, commented out)
- `google-generativeai`: Gemini API (paid, commented out)
- `textual`: TUI framework (Phase 4)

## Claude Code Skills

Custom skills for streamlined documentation, knowledge management, and session workflows. These are markdown instruction files in `.claude/skills/` that provide one-command workflows for common tasks.

### Available Skills

#### docs-update
**Purpose:** Automatically update all project documentation

**Usage:**
```bash
/docs-update
```
Or say: "Update the docs" or "Run docs update"

**What it does:**
- Updates `.STATUS` with latest progress
- Marks completed tasks in phase plans
- Recalculates metrics (LOC, tests, coverage)
- Checks for documentation inconsistencies
- Updates version numbers

#### session-wrap
**Purpose:** Generate brief, ADHD-friendly session summaries

**Usage:**
```bash
/session-wrap
```
Or say: "Wrap up" or "Summarize session"

**What it does:**
- Lists completed tasks
- Shows files created/modified
- Highlights key decisions
- Notes next steps
- Saves to `.claude/sessions/YYYY-MM-DD_HHMM.md`

**Output format:**
```markdown
# Session: 2025-12-13 14:30

## Completed
- ✅ Task 1
- ✅ Task 2

## Files
- Created: file1.py (100 lines)
- Modified: file2.md

## Next
→ Next task
```

#### checkpoint
**Purpose:** Complete checkpoint (docs + wrap + commit)

**Usage:**
```bash
/checkpoint
```
Or say: "Checkpoint" or "Save my work"

**What it does:**
1. Runs `docs-update` skill
2. Runs `session-wrap` skill
3. Stages all changes with `git add`
4. Creates commit with smart message
5. Optionally creates git tag

**Options:**
- `"Checkpoint: Custom message"` - Use custom commit message
- `"Checkpoint and tag as v2.1.0"` - Create tag
- `"Quick checkpoint"` - Skip docs update (WIP commits)

### Typical Workflow

```bash
# During development
# ... implement feature ...

# Save progress (WIP)
"Quick checkpoint"

# ... continue work ...

# Feature complete
"Checkpoint"

# Review summary
cat .claude/sessions/2025-12-13_1700.md

# Push if ready
git push origin main
```

### ADHD-Friendly Design

All skills follow these principles:
- ✅ One command does everything (no multi-step processes)
- ✅ Clear visual feedback (emojis, progress indicators)
- ✅ Automatic tracking (no manual note-taking required)
- ✅ Smart defaults (minimal decisions needed)
- ✅ Brief summaries (scannable, actionable output)
- ✅ Always show next steps (never wonder "what now?")

### Documentation

See `.claude/skills/README.md` for complete usage guide and examples.

## Troubleshooting

### Python CLI Not Found
- Check that `src/python/obs_cli.py` exists
- Verify file is executable: `chmod +x src/python/obs_cli.py`
- Run from project root directory

### Database Errors
- Initialize database: `python3 src/python/obs_cli.py db init`
- Check permissions on `~/.config/obs/`
- Verify SQLite3 is installed

### Import Errors
- Install dependencies: `pip3 install -r src/python/requirements.txt`
- Check Python version: `python3 --version` (must be 3.9+)

### Link Resolution Issues
- Verify wikilinks are in standard format: `[[target]]` or `[[target|display]]`
- Check for relative path issues
- Review broken links: `obs stats <vault_id>`

## Performance Considerations

### Database Optimization
- Indexes are created automatically via schema
- Use `VACUUM` periodically to reclaim space
- Consider `ANALYZE` for query optimization

### Scanning Large Vaults
- Use `--verbose` to monitor progress
- Scanner processes ~100 notes/second
- Graph metrics calculation is O(n²) for centrality

### Memory Usage
- NetworkX graphs held in memory during analysis
- Large vaults (>10k notes) may need 1-2GB RAM
- Consider batch processing for very large vaults

## Security and Privacy

### Local-First Design
- All data stored locally in SQLite
- No data sent to cloud by default
- AI features use local models (100% private)

### AI Privacy (Phase 2)
- **Default providers are 100% local** (HuggingFace, Ollama)
- No API keys required for default setup
- No data sent to external servers
- Models run on your machine
- Complete privacy and offline capability

### API Key Management (Optional)
- Paid APIs (Claude, Gemini) are **optional** and commented out
- If using paid APIs, store keys in environment variables
- Never commit API keys to git
- Use `.env` file for local development

## Version History

- **2.0.0-beta** (2025-12-13):
  - Phase 1: Foundation, scanning, graph analysis (COMPLETE)
  - Phase 2: Free AI integration (HuggingFace + Ollama) (COMPLETE)
  - Phase 4: TUI/Visualization (IN PROGRESS)
    - Phase 4.1: TUI Foundation with Textual framework (COMPLETE)
    - Phase 4.2: Vault Browser with real database integration (COMPLETE)
    - Phase 4.3: Note Explorer (NEXT)
  - Claude Code Skills for docs/knowledge/wrap-up workflow
  - Interactive setup wizard with auto-detection
  - Complete test suite (122 tests, 70% coverage)
  - Comprehensive documentation
- **1.1.0** (2025-12-11): Quick wins - list, stats, unlink, completion
- **1.0.0** (2025-12-10): Initial release - vault management, R-Dev integration
