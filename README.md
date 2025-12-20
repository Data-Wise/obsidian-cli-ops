# Obsidian CLI Ops

[![Build Status](https://github.com/Data-Wise/obsidian-cli-ops/actions/workflows/pages/pages-build-deployment/badge.svg)](https://github.com/Data-Wise/obsidian-cli-ops/actions)
[![Version](https://img.shields.io/badge/version-3.0.0--dev-blue.svg)](https://github.com/Data-Wise/obsidian-cli-ops/releases)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://www.python.org/)
[![Tests](https://img.shields.io/badge/tests-35%2B%20passing-brightgreen.svg)](https://github.com/Data-Wise/obsidian-cli-ops)

**An Intelligent Command-Line Tool for Obsidian Vault Management with AI-Powered Graph Analysis.**

`obs` is a laser-focused CLI tool for managing Obsidian vaults with AI-powered knowledge graph analysis.

**Current Version**: 3.0.0-dev (Proposal A - Pure Obsidian Manager)

## 🚀 Quick Start

```bash
obs                    # List your vaults
obs stats <vault>      # Show vault statistics
obs discover <path>    # Find new vaults
obs analyze <vault>    # Analyze knowledge graph
```

## ✨ Features

### 📊 Core Features (v3.0.0-dev)

- **Vault Discovery**: Automatically find and scan Obsidian vaults
- **Graph Analysis**: PageRank, centrality, clustering coefficients
- **Link Resolution**: Resolve wikilinks and detect broken links
- **Orphan Detection**: Find notes with no connections
- **Hub Detection**: Identify highly connected notes
- **Analytics**: Comprehensive vault statistics and insights
- **Rich CLI Output**: Beautiful terminal output with tables, colors, progress bars

### 🤖 AI-Powered Features

- **Multi-Provider AI**: Choose from Gemini API, Gemini CLI, Claude CLI, or Ollama
- **Find Similar Notes**: `obs ai similar` - semantic similarity using embeddings
- **Analyze Notes**: `obs ai analyze` - deep analysis with topics, themes, suggestions
- **Detect Duplicates**: `obs ai duplicates` - find potential duplicate notes
- **Provider Management**: `obs ai status`, `obs ai setup`, `obs ai test`
- **Smart Routing**: Auto-selects best provider for each operation type
- **100% Local & Private**: Default providers run entirely on your machine

### 🎯 v3.0.0 Simplification (Proposal A)

**Philosophy:** "Do one thing exceptionally well - manage Obsidian vaults"

**What's New:**

- **Simplified CLI**: 20+ commands → 10 focused commands
- **ZSH-First**: Fast shell integration with Python core
- **Laser Focus**: Removed features unrelated to Obsidian vault management
- **Code Reduction**: 11,500 → ~7,400 lines (36% reduction so far, target: 61%)

**Removed (still in v2.2.0):**

- TUI interface (1,701 lines) - CLI-only for simplicity
- R-Dev integration (307 lines) - Belongs in R package ecosystem
- Legacy v1.x commands (126 lines) - Plugin install, sync, audit

**Coming Soon (Phase 7.2):**

- `obs refactor <vault>` - AI-powered vault reorganization
- `obs tag-suggest` - Intelligent tag suggestions
- `obs quality` - Note quality assessment
- `obs merge-suggest` - Find merge candidates

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

**v3.0.0 - Simplified CLI** - 10 focused commands!

```bash
# PRIMARY COMMANDS
obs                        # List your vaults
obs stats <vault_id>       # Show vault statistics
obs discover <path>        # Find vaults in directory

# GRAPH ANALYSIS
obs analyze <vault_id>     # Analyze vault graph metrics

# AI FEATURES (optional)
obs ai status              # Check provider status
obs ai setup               # Interactive setup wizard
obs ai test                # Test all providers
obs ai similar <note_id>   # Find similar notes
obs ai analyze <note_id>   # Analyze a note with AI
obs ai duplicates <vault>  # Find duplicate notes

# UTILITIES
obs help                   # Show simple help
obs help --all             # Show all commands
obs version                # Show version
```

**Pro Tip:** All commands have `--verbose` flag for detailed output!

## 📋 Planning & Development

**Current Status:** v3.0.0-dev - Phase 7.1 Simplification (In Progress)

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

- ✅ v2.0: Knowledge Graph - Complete
- ✅ v2.2: AI Features - Complete
  - Multi-provider AI (Gemini, Claude, Ollama)
  - Find similar notes, analyze, detect duplicates
  - 96 AI tests, smart routing
- 🚧 v3.0.0: Simplification (In Progress)
  - Phase 7.1: Simplification (75% complete)
    - ✅ TUI removed (1,701 lines)
    - ✅ R-Dev removed (307 lines)
    - ✅ CLI consolidated (323 lines)
    - 🚧 Documentation updates
  - Phase 7.2: AI-Powered Note Operations (Planned)
  - Phase 7.3: Vault Health & Polish (Planned)
  - Phase 7.4: Testing & Release (Planned)

---

**Repository**: https://github.com/Data-Wise/obsidian-cli-ops
**Documentation**: https://data-wise.github.io/obsidian-cli-ops/
