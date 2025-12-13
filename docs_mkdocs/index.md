# Obsidian CLI Ops

**An Intelligent Command-Line Tool for Multi-Vault Obsidian Knowledge Management.**

`obs` is a powerful CLI tool that combines federated vault management with intelligent knowledge graph analysis. It bridges your Knowledge Base (Obsidian), your Computational Environment (R/Python), and your System Shell (ZSH).

**Current Version**: 2.0.0-beta

## Key Features

### v1.x: Federated Vault Management
*   **⚡️ Core Sync**: Keep themes, hotkeys, and settings consistent across multiple vaults
*   **📦 Plugin Manager**: Install community plugins directly from GitHub
*   **🔬 R-Dev Integration**: Seamlessly log plots, fetch theory, and sync drafts between R Projects and Obsidian
*   **🛡️ Audit**: Ensure your file structure stays organized

### v2.0: Knowledge Graph Analysis (NEW!)
*   **🔍 Vault Discovery**: Automatically find and scan all Obsidian vaults
*   **📊 Graph Metrics**: PageRank, centrality, clustering coefficients
*   **🔗 Link Resolution**: Resolve wikilinks and detect broken links
*   **🏝️ Orphan Detection**: Find notes with no connections
*   **🌟 Hub Detection**: Identify highly connected notes
*   **📈 Analytics**: Comprehensive vault statistics and insights

## Quick Start

### Install Dependencies
```bash
# Required CLI tools
brew install jq curl

# Python dependencies (for v2.0)
pip3 install python-frontmatter mistune PyYAML networkx
```

### Initialize Database
```bash
# Create knowledge graph database
obs stats  # Auto-initializes on first run
```

### Discover Vaults
```bash
# Find and scan Obsidian vaults
obs discover ~/Documents --scan -v
```

[Full Installation Guide](installation.md){ .md-button .md-button--primary }
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
- [R-Dev Integration](r-dev.md) - R development workflow
- [Configuration](configuration.md) - Advanced setup

## Project Status

- ✅ **Phase 1 Complete**: Database, scanner, graph analysis
- 🚧 **Phase 2 In Progress**: AI integration (Claude + Gemini)
- 📋 **Phase 3 Planned**: Intelligent suggestions
- 📋 **Phase 4 Planned**: TUI visualization
- 📋 **Phase 5 Planned**: Learning system
- 📋 **Phase 6 Planned**: Automation

See the [complete roadmap](https://github.com/Data-Wise/obsidian-cli-ops/blob/main/PROJECT_PLAN_v2.0.md).

## Community

- **Repository**: [github.com/Data-Wise/obsidian-cli-ops](https://github.com/Data-Wise/obsidian-cli-ops)
- **Issues**: [Report bugs or request features](https://github.com/Data-Wise/obsidian-cli-ops/issues)
- **License**: ISC

---

**Built with ❤️ for the Obsidian and R communities**
