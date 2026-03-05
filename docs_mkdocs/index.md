# Obsidian CLI Ops

**An Intelligent Command-Line Tool for Obsidian Vault Management with AI-Powered Graph Analysis.**

`obs` is a laser-focused CLI tool for managing Obsidian vaults with knowledge graph analysis and multi-provider AI features.

**Current Version**: 3.0.0

## Key Features

### Vault Management
*   **🔍 Vault Discovery**: Automatically find and scan Obsidian vaults (iCloud auto-detect)
*   **📊 Graph Analysis**: PageRank, centrality, clustering coefficients
*   **🔗 Link Resolution**: Resolve wikilinks and detect broken links
*   **🏝️ Orphan Detection**: Find notes with no connections
*   **🌟 Hub Detection**: Identify highly connected notes
*   **📈 Analytics**: Comprehensive vault statistics and insights

### AI-Powered Features
*   **🤖 Multi-Provider AI**: Gemini API, Anthropic API, Gemini CLI, Claude CLI, Ollama
*   **🔍 Find Similar Notes**: `obs ai similar` — semantic similarity using embeddings
*   **🔬 Analyze Notes**: `obs ai analyze` — deep analysis with topics, themes, suggestions
*   **📋 Detect Duplicates**: `obs ai duplicates` — find potential duplicate notes
*   **🔗 Suggest Links**: `obs ai suggest-links` — find unlinked related notes
*   **🕳️ Knowledge Gaps**: `obs ai gaps` — detect stub notes and orphans
*   **📊 Vault Summary**: `obs ai summarize` — theme analysis across vault
*   **🔄 Vault Refactor**: `obs ai refactor` — AI-powered reorganization suggestions
*   **🔧 Provider Management**: `obs ai status`, `obs ai setup`, `obs ai test`
*   **⚡ Smart Routing**: Auto-selects best provider for each operation

### Developer Experience
*   **🎯 Zero-Friction**: Just type `obs` — lists your vaults immediately
*   **🌥️ iCloud-First**: Auto-detects standard Obsidian iCloud location
*   **🎨 ADHD-Friendly**: 15 focused commands, smart defaults, progressive disclosure
*   **🏷️ Flexible Lookup**: Use vault names or ID prefixes (`obs analyze Knowledge_Base`)

## Quick Start

### Install Dependencies
```bash
# Required CLI tools
brew install jq curl

# Python dependencies
pip3 install -r src/python/requirements.txt
```

### Initialize Database
```bash
# Create knowledge graph database
python3 src/python/obs_cli.py db init
```

### Start Using
```bash
# List your vaults
obs

# Discover vaults in a directory
obs discover ~/Documents --scan

# Analyze a vault by name or ID
obs analyze Knowledge_Base
obs stats --vault Knowledge_Base
```

### Setup AI Features (Optional)
```bash
# Check available providers
obs ai status

# Interactive setup wizard
obs ai setup

# Find similar notes
obs ai similar <note_id>

# Analyze a note
obs ai analyze <note_id>

# Find duplicates in vault
obs ai duplicates <vault>

# Get reorganization suggestions
obs ai refactor <vault>
```

[Full Installation Guide](installation.md){ .md-button .md-button--primary }
[AI Setup Guide](ai-setup.md){ .md-button }
[v3.0 Features](v3.0.md){ .md-button }

## Use Cases

### Knowledge Management
- Analyze vault structure and connections
- Find orphaned notes that need linking
- Identify hub notes (highly connected)
- Detect broken wikilinks

### AI-Powered Insights
- Find semantically similar notes across your vault
- Detect potential duplicate content
- Get AI analysis of note quality and connections
- Get actionable vault reorganization suggestions

### Vault Maintenance
- Discover and scan vaults automatically
- Track vault statistics over time
- Monitor graph health (orphans, broken links)
- AI-powered refactor plans for vault cleanup

## Architecture

**Three-Layer Design (Zero Duplication):**

1. **ZSH Layer** (`src/obs.zsh`): CLI interface (386 lines)
2. **Python Core** (`src/python/core/`): Business logic (859 lines)
3. **Python Data** (`src/python/`): Database, scanning, graph building

**Database:** SQLite (`~/.config/obs/vault_db.sqlite`)

**Graph Engine:** NetworkX for centrality and PageRank calculations

## Documentation

- [Installation](installation.md) - Get obs installed and configured
- [Usage](usage.md) - Core commands and workflows
- [v3.0 Features](v3.0.md) - Current version features
- [AI Setup Guide](ai-setup.md) - Set up AI features (Gemini, Claude, Ollama)
- [Migration Guide](migration.md) - Upgrading from v2.x
- [Configuration](configuration.md) - Advanced setup

## Project Status

- ✅ **Phase 1-5 Complete**: Database, scanner, graph, AI features
- ✅ **Phase 7.1 Complete**: v3.0.0 simplification (TUI removed, CLI consolidated)
- ✅ **Async & Lookup Fix**: Vault name/prefix lookup, async operations (PR #2)
- ✅ **Phase 7.2 Complete**: AI Enhancement (modern SDKs, 3 new commands, 125 tests)
- ✅ **Phase 7.3 Complete**: Vault Health & Polish (--json export, health dashboard, CLI polish, 183 tests)
- ✅ **Phase 7.4 Complete**: Testing & Release Prep (version sync, CI hardening, 202 tests, v3.0.0 stable)

**Current Status:** v3.0.0 Stable (202 tests)

See [TODOS.md](https://github.com/Data-Wise/obsidian-cli-ops/blob/main/TODOS.md) for current work items.

## Community

- **Repository**: [github.com/Data-Wise/obsidian-cli-ops](https://github.com/Data-Wise/obsidian-cli-ops)
- **Issues**: [Report bugs or request features](https://github.com/Data-Wise/obsidian-cli-ops/issues)
- **License**: ISC

---

**Built with ❤️ for the Obsidian and R communities**
