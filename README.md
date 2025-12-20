# Obsidian CLI Ops

[![Build Status](https://github.com/Data-Wise/obsidian-cli-ops/actions/workflows/pages/pages-build-deployment/badge.svg)](https://github.com/Data-Wise/obsidian-cli-ops/actions)
[![Version](https://img.shields.io/badge/version-2.2.0-blue.svg)](https://github.com/Data-Wise/obsidian-cli-ops/releases)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://www.python.org/)
[![Tests](https://img.shields.io/badge/tests-394%2B%20passing-brightgreen.svg)](https://github.com/Data-Wise/obsidian-cli-ops)

**An Intelligent Command-Line Tool for Multi-Vault Obsidian Knowledge Management.**

`obs` is a powerful CLI tool that combines federated vault management with intelligent knowledge graph analysis.

**Current Version**: 2.2.0

## 🚀 Quick Start

```bash
obs                    # Open last vault
obs switch             # Vault switcher
obs scan <vault>       # Scan vault
obs stats <vault>      # Show statistics
```

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

### 🖥️ v2.1: Obsidian App Clone
- **Zero-Friction Start**: Just type `obs` - opens last vault automatically
- **Obsidian-Style Commands**: Works exactly like the official Obsidian app
- **iCloud-First**: Auto-detects standard Obsidian iCloud location
- **Last-Vault Tracking**: Remembers where you were (like Obsidian app)
- **Rich CLI Output**: Beautiful terminal output with tables, colors, progress bars
- **ADHD-Friendly**: One command, smart defaults, progressive disclosure

### 🤖 v2.2: AI-Powered Features (NEW!)
- **Multi-Provider AI**: Choose from Gemini API, Gemini CLI, Claude CLI, or Ollama
- **Find Similar Notes**: `obs ai similar` - semantic similarity using embeddings
- **Analyze Notes**: `obs ai analyze` - deep analysis with topics, themes, suggestions
- **Detect Duplicates**: `obs ai duplicates` - find potential duplicate notes
- **Provider Management**: `obs ai status`, `obs ai setup`, `obs ai test`
- **Smart Routing**: Auto-selects best provider for each operation type
- **Easy Installation**: `pip install obs[gemini]` or `pip install obs[ollama]`

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

**Option D: Obsidian App Clone** - Just type `obs`!

```bash
# The one command you need (opens last vault or shows picker)
obs

# Switch vaults (like "Open another vault" in Obsidian)
obs switch

# Manage vaults (like "Manage Vaults" menu in Obsidian)
obs manage

# Open specific vault
obs open <vault_name>

# Show graph visualization
obs graph

# View statistics
obs stats

# AI features (optional)
obs ai status              # Check provider status
obs ai setup               # Interactive setup wizard
obs ai similar <note_id>   # Find similar notes
obs ai analyze <note_id>   # Analyze a note
obs ai duplicates <vault>  # Find duplicates

# R integration (shortened from obs r-dev)
obs r link
obs r log result.png
```

**Pro Tip:** The CLI works exactly like the Obsidian app - just type `obs` and it does the right thing!

## 📋 Planning & Development

**Current Status:** v2.2.0 - Phase 5 AI Complete (98% complete)

### Active Planning Files
- **[TODOS.md](TODOS.md)** - Current work items and immediate next steps ⭐ What to work on now
- **[IDEAS.md](IDEAS.md)** - Future features and brainstorming 💡 What could be built

### For Contributors
- **[CLAUDE.md](CLAUDE.md)** - Developer guide and architecture quick reference
- **[Project Hub](docs/planning/project-hub.md)** - ADHD-friendly control center with current status
- **[.STATUS](.STATUS)** - Project metrics and progress tracking

**Want to contribute?** Start with [TODOS.md](TODOS.md) to see what needs doing!

## 📖 Documentation

### Getting Started
- **[Documentation Index](docs/README.md)** - Complete documentation structure
- **[Quickstart Guide](docs/user/getting-started/quickstart.md)** - Get up and running with v2.0
- **[Full Documentation](https://data-wise.github.io/obsidian-cli-ops/)** - Published guides and API reference
- **[CLAUDE.md](CLAUDE.md)** - Developer guide for contributing

### User Guides
- **[Unified Command Guide](docs/user/guides/unified-command.md)** - Using the unified `obs` command
- **[AI Setup Guide](docs/user/guides/ai-setup.md)** - Setting up AI features (100% local)

### Developer Docs
- **[Architecture](docs/developer/architecture.md)** - Three-layer system design
- **[Testing Guide](docs/developer/testing/overview.md)** - Test suite overview
- **[Sandbox Testing](docs/developer/testing/sandbox.md)** - Comprehensive testing guide

### Planning & Releases
- **[Project Hub](docs/planning/project-hub.md)** - ADHD-friendly control center
- **[Project Plan](docs/planning/project-plan.md)** - Complete v2.0 roadmap
- **[Latest Release](docs/releases/v2.2.0.md)** - v2.2.0 release notes

## 🧪 Test Coverage

- **394+ tests** across all components
- **72% code coverage** (AI: 80%, Core: 85%)
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
- ✅ v2.1: Option D (Obsidian App Clone) - Complete
- ✅ v2.2: AI Features - Complete
  - Multi-provider AI (Gemini, Claude, Ollama)
  - Find similar notes, analyze, detect duplicates
  - 96 AI tests, smart routing
- 📋 Future: Learning System, Automation

---

**Repository**: https://github.com/Data-Wise/obsidian-cli-ops
**Documentation**: https://data-wise.github.io/obsidian-cli-ops/
