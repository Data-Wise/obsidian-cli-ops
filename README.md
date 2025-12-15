# Obsidian CLI Ops

**An Intelligent Command-Line Tool for Multi-Vault Obsidian Knowledge Management.**

`obs` is a powerful CLI tool that combines federated vault management with intelligent knowledge graph analysis and an interactive TUI interface.

**Current Version**: 2.1.0-beta

## ✨ Features

### 🔧 v1.x: Federated Vault Management
- **Sync**: Keep themes, hotkeys, and settings consistent across multiple vaults
- **Plugin Manager**: Install community plugins directly from GitHub
- **R-Dev Integration**: Seamlessly integrate R Projects with Obsidian
- **Audit**: Ensure your file structure stays organized

### 📊 v2.0: Knowledge Graph Analysis
- **Vault Discovery**: Automatically find and scan all Obsidian vaults
- **Graph Metrics**: PageRank, centrality, clustering coefficients
- **Link Resolution**: Resolve wikilinks and detect broken links
- **Orphan Detection**: Find notes with no connections
- **Hub Detection**: Identify highly connected notes
- **Analytics**: Comprehensive vault statistics and insights
- **AI Features**: Note similarity, duplicate detection (100% free, local, private)

### 🖥️ v2.1: Interactive TUI (NEW!)
- **Full-Screen Interface**: Beautiful terminal UI with Textual framework
- **Vault Browser**: Interactive vault selection with real-time statistics
- **Note Explorer**: Search, filter, and preview notes with metadata
- **Graph Visualizer**: ASCII art graph with hub/orphan detection
- **Statistics Dashboard**: Tag analytics, link distribution, scan history
- **Keyboard Navigation**: Vim-style keys, arrow keys, and shortcuts
- **ADHD-Friendly Design**: Clear hierarchy, colors, emojis, and borders

## 🚀 Quick Start

### Installation
```bash
# 1. Symlink the script
ln -s "$(pwd)/src/obs.zsh" ~/.config/zsh/functions/obs.zsh

# 2. Autoload in .zshrc
echo "autoload -Uz obs" >> ~/.zshrc

# 3. Install Python dependencies
pip3 install -r src/python/requirements.txt
```

### Basic Usage
```bash
# Discover and scan vaults
obs discover ~/Documents --scan

# Launch interactive TUI
obs tui

# View statistics
obs stats

# Setup AI features (optional, 100% local)
obs ai setup --quick
```

## 📖 Documentation

- **[Full Documentation](https://data-wise.github.io/obsidian-cli-ops/)** - Complete guides and API reference
- **[Installation Guide](docs_mkdocs/installation.md)** - Detailed setup instructions
- **[v2.0 Features](docs_mkdocs/v2.0.md)** - Knowledge graph and AI features
- **[AI Setup Guide](docs_mkdocs/ai-setup.md)** - Complete AI configuration guide
- **[CLAUDE.md](CLAUDE.md)** - Developer guide for contributing

## 🧪 Test Coverage

- **298 tests** across all components
- **80% code coverage**
- All tests passing

## 📦 Requirements

- **ZSH**: Shell integration
- **Python 3.9+**: Core functionality
- **Dependencies**: See `src/python/requirements.txt`
- **Optional**: Ollama or HuggingFace for AI features

## 🤝 Contributing

See [CLAUDE.md](CLAUDE.md) for development guidelines and architecture details.

## 📄 License

MIT License - See LICENSE file for details.

## 🌟 Status

- ✅ v1.x: Production Ready
- ✅ v2.0: Knowledge Graph - Complete
- ✅ v2.1: Interactive TUI - Complete (Phases 4.1-4.5)
- 🚧 Future: AI Features, Learning System, Automation

---

**Repository**: https://github.com/Data-Wise/obsidian-cli-ops
**Documentation**: https://data-wise.github.io/obsidian-cli-ops/
