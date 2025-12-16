# Obsidian CLI Ops

**An Intelligent Command-Line Tool for Multi-Vault Obsidian Knowledge Management.**

`obs` is a powerful CLI tool that combines federated vault management with intelligent knowledge graph analysis. It bridges your Knowledge Base (Obsidian), your Computational Environment (R/Python), and your System Shell (ZSH).

**Current Version**: 2.2.0

## Key Features

### v1.x: Federated Vault Management
*   **⚡️ Core Sync**: Keep themes, hotkeys, and settings consistent across multiple vaults
*   **📦 Plugin Manager**: Install community plugins directly from GitHub
*   **🔬 R-Dev Integration**: Seamlessly log plots, fetch theory, and sync drafts between R Projects and Obsidian
*   **🛡️ Audit**: Ensure your file structure stays organized

### v2.0: Knowledge Graph Analysis
*   **🔍 Vault Discovery**: Automatically find and scan all Obsidian vaults
*   **📊 Graph Metrics**: PageRank, centrality, clustering coefficients
*   **🔗 Link Resolution**: Resolve wikilinks and detect broken links
*   **🏝️ Orphan Detection**: Find notes with no connections
*   **🌟 Hub Detection**: Identify highly connected notes
*   **📈 Analytics**: Comprehensive vault statistics and insights
*   **🤖 AI-Powered Features**: Note similarity, duplicate detection, topic analysis (100% free, local, private)

### v2.1: Obsidian App Clone
*   **🎯 Zero-Friction Start**: Just type `obs` - opens last vault automatically (like Obsidian app)
*   **🌥️ iCloud-First**: Auto-detects standard Obsidian iCloud location
*   **🔄 Last-Vault Tracking**: Remembers where you were (like Obsidian app)
*   **🖥️ Full-Screen TUI**: Beautiful terminal UI with vault browser, note explorer, graph visualizer
*   **⌨️ Obsidian-Style Commands**: `obs switch`, `obs manage`, `obs open` - works like the official app
*   **🎨 ADHD-Friendly**: One command, smart defaults, progressive disclosure
*   **📦 Shortened R Integration**: `obs r` (from `obs r-dev`) for less typing
*   **✅ Backward Compatible**: All legacy commands still work

### v2.2: AI-Powered Features (NEW!)
*   **🤖 Multi-Provider AI**: Gemini API, Gemini CLI, Claude CLI, Ollama
*   **🔍 Find Similar Notes**: `obs ai similar` - semantic similarity using embeddings
*   **🔬 Analyze Notes**: `obs ai analyze` - deep analysis with topics, themes, suggestions
*   **📋 Detect Duplicates**: `obs ai duplicates` - find potential duplicate notes
*   **🔧 Provider Management**: `obs ai status`, `obs ai setup`, `obs ai test`
*   **⚡ Smart Routing**: Auto-selects best provider for each operation
*   **📦 Easy Setup**: `pip install obs[gemini]` or `pip install obs[ollama]`

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

### Start Using (Zero Configuration!)
```bash
# Just type obs - it auto-detects iCloud vaults!
obs

# If no vaults found, discover in specific directory
obs manage open ~/Documents

# Or use vault picker (press 'd' to discover iCloud vaults)
obs switch
```

**That's it!** Works exactly like launching the Obsidian app.

### Option D Commands (Obsidian-Style)
```bash
obs                     # Open last vault (or show picker)
obs switch              # Vault switcher (like "Open another vault")
obs manage              # Manage vaults (like "Manage Vaults" menu)
obs open <name>         # Open specific vault
obs graph               # Show graph visualization
obs stats               # View statistics
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
obs ai duplicates <vault_id>
```

[Full Installation Guide](installation.md){ .md-button .md-button--primary }
[AI Setup Guide](ai-setup.md){ .md-button }
[v2.0 Features](v2.0.md){ .md-button }

## Use Cases

### Knowledge Management
- Analyze vault structure and connections
- Find orphaned notes that need linking
- Identify hub notes (highly connected)
- Detect broken wikilinks

### R Development
- Link R projects to Obsidian folders
- Log analysis results automatically
- Fetch theory notes while coding
- Sync vignettes and drafts

### Vault Maintenance
- Sync themes and settings across vaults
- Install plugins to multiple vaults
- Audit file organization
- Track vault statistics over time

## Architecture

**Two-Layer Design:**

1. **ZSH Layer** (`src/obs.zsh`): Main CLI interface, configuration, vault operations
2. **Python Layer** (`src/python/`): Knowledge graph analysis, scanning, metrics

**Database:** SQLite (`~/.config/obs/vault_db.sqlite`)

**Graph Engine:** NetworkX for centrality and PageRank calculations

## Documentation

- [Installation](installation.md) - Get obs installed and configured
- [Usage](usage.md) - Core commands and workflows
- [v2.0 Features](v2.0.md) - Knowledge graph analysis
- [AI Setup Guide](ai-setup.md) - Set up free AI features (similarity, duplicates, topics)
- [R-Dev Integration](r-dev.md) - R development workflow
- [Configuration](configuration.md) - Advanced setup

## Project Status

- ✅ **Phase 1 Complete**: Database, scanner, graph analysis
- ✅ **Phase 2 Complete**: AI integration (HuggingFace + Ollama - free, local, private)
- ✅ **Phase 4 Complete**: TUI visualization, Option D (Obsidian App Clone)
- ✅ **Phase 5 Complete**: Multi-provider AI (Gemini, Claude, Ollama) + AI features
- 📋 **Phase 6 Planned**: Learning system

**Current Status:** v2.2.0 (98% complete) - Production Ready

See [TODOS.md](https://github.com/Data-Wise/obsidian-cli-ops/blob/main/TODOS.md) for current work items.

## Community

- **Repository**: [github.com/Data-Wise/obsidian-cli-ops](https://github.com/Data-Wise/obsidian-cli-ops)
- **Issues**: [Report bugs or request features](https://github.com/Data-Wise/obsidian-cli-ops/issues)
- **License**: ISC

---

**Built with ❤️ for the Obsidian and R communities**
