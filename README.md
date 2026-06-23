# Obsidian CLI Ops

[![Build Status](https://github.com/Data-Wise/obsidian-cli-ops/actions/workflows/pages/pages-build-deployment/badge.svg)](https://github.com/Data-Wise/obsidian-cli-ops/actions)
[![Version](https://img.shields.io/badge/version-4.0.0-blue.svg)](https://github.com/Data-Wise/obsidian-cli-ops/releases)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://www.python.org/)
[![Tests](https://img.shields.io/badge/tests-400%20passing-brightgreen.svg)](https://github.com/Data-Wise/obsidian-cli-ops)

**An Intelligent Command-Line Tool for Obsidian Vault Management with AI-Powered Graph Analysis.**

`obs` is a laser-focused CLI tool for managing Obsidian vaults with AI-powered knowledge graph analysis.

**Current Version**: 4.0.0

## 🚀 Quick Start

```bash
obs                    # List your vaults
obs stats <vault>      # Show vault statistics
obs discover <path>    # Find new vaults
obs analyze <vault>    # Analyze knowledge graph
```

## ✨ Features

### 📊 Core Features (v3.0.0)

- **Vault Discovery**: Automatically find and scan Obsidian vaults
- **Graph Analysis**: PageRank, centrality, clustering coefficients
- **Link Resolution**: Resolve wikilinks and detect broken links
- **Orphan Detection**: Find notes with no connections
- **Hub Detection**: Identify highly connected notes
- **Analytics**: Comprehensive vault statistics and insights
- **Rich CLI Output**: Beautiful terminal output with tables, colors, progress bars

### 🤖 AI-Powered Features

- **Multi-Provider AI**: Choose from Gemini API, Anthropic API, Gemini CLI, Claude CLI, or Ollama
- **Find Similar Notes**: `obs ai similar` - semantic similarity using embeddings
- **Analyze Notes**: `obs ai analyze` - deep analysis with topics, themes, suggestions
- **Detect Duplicates**: `obs ai duplicates` - find potential duplicate notes
- **Suggest Links**: `obs ai suggest-links` - find unlinked related notes
- **Knowledge Gaps**: `obs ai gaps` - detect stub notes and orphans
- **Vault Summary**: `obs ai summarize` - generate theme analysis across vault
- **Vault Refactor**: `obs ai refactor` - AI-powered vault reorganization suggestions
- **Merge Suggest**: `obs ai merge-suggest` - find note pairs with high content similarity
- **Tag Suggest**: `obs ai tag-suggest` - AI-powered tag suggestions for untagged notes
- **Quality Scoring**: `obs ai quality` - score notes on completeness, connectivity, metadata, freshness
- **Provider Management**: `obs ai status`, `obs ai setup`, `obs ai test`
- **Smart Routing**: Auto-selects best provider for each operation type
- **Embedding Cache**: SQLite-backed cache with mtime invalidation
- **100% Local & Private**: Default providers run entirely on your machine

### 🎯 v3.0.0 Simplification (Proposal A)

**Philosophy:** "Do one thing exceptionally well - manage Obsidian vaults"

**What's New:**

- **Simplified CLI**: 20+ commands → 15 focused commands
- **ZSH-First**: Fast shell integration with Python core
- **Laser Focus**: Removed features unrelated to Obsidian vault management
- **Code Reduction**: 11,500 → ~7,400 lines (36% reduction so far, target: 61%)

**Removed (still in v2.2.0):**

- TUI interface (1,701 lines) - CLI-only for simplicity
- R-Dev integration (307 lines) - Belongs in R package ecosystem
- Legacy v1.x commands (126 lines) - Plugin install, sync, audit

## 🚀 Quick Start

### Installation
```bash
# 1. Provision deps in an isolated venv + symlink the launcher (no manual pip)
./install.sh

# 2. Autoload in .zshrc
echo "autoload -Uz obs" >> ~/.zshrc
```

### Basic Usage

**v3.2.0** - 18 focused commands!

```bash
# PRIMARY COMMANDS
obs                             # List your vaults
obs stats <vault>               # Show vault statistics
obs discover <path>             # Find vaults in directory

# GRAPH ANALYSIS
obs analyze <vault>             # Analyze vault graph metrics
obs health <vault>              # Vault health dashboard

# AI FEATURES (optional)
obs ai status                   # Check provider status
obs ai setup                    # Interactive setup wizard
obs ai test                     # Test all providers
obs ai similar <note_id>        # Find similar notes
obs ai analyze <note_id>        # Analyze a note with AI
obs ai duplicates <vault>       # Find duplicate notes
obs ai suggest-links <note_id>  # Suggest new links
obs ai gaps <vault>             # Find knowledge gaps
obs ai summarize <vault>        # Summarize vault themes
obs ai refactor <vault>         # AI-powered reorganization
obs ai merge-suggest <vault>    # Find merge candidates
obs ai tag-suggest <target>     # Suggest tags for notes
obs ai quality <target>         # Score note quality

# UTILITIES
obs help                        # Show simple help
obs help --all                  # Show all commands
obs version                     # Show version
```

**Pro Tip:** All commands have `--verbose` flag for detailed output!

## 📋 Planning & Development

**Current Status:** v4.0.0 Stable

### Active Planning Files
- **[.STATUS](.STATUS)** - Current state, next steps, and metrics ⭐ What to work on now
- **[SPEC-merge-nexus-cli-v2-2026-06-21.md](SPEC-merge-nexus-cli-v2-2026-06-21.md)** - Active plan (nexus-cli absorption)
- **[IDEAS.md](IDEAS.md)** - Future features and brainstorming 💡 What could be built
- _Archived (historical):_ [docs/planning/TODOS.md](docs/planning/TODOS.md), [docs/planning/IMPLEMENTATION-ROADMAP.md](docs/planning/IMPLEMENTATION-ROADMAP.md)

### For Contributors
- **[CLAUDE.md](CLAUDE.md)** - Developer guide and architecture quick reference
- **[Project Hub](docs/planning/project-hub.md)** - ADHD-friendly control center with current status

**Want to contribute?** Start with [.STATUS](.STATUS) to see current state and next steps!

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
- **[Latest Release](https://github.com/Data-Wise/obsidian-cli-ops/releases/tag/v4.0.0)** - v4.0.0 release notes

## 🧪 Test Coverage

- **235 pytest + 69 Jest** tests passing (2 Jest network-gated, run in CI)
- CI: GitHub Actions on push/PR to `main` and `dev`
- Python coverage reporting via `pytest-cov`

## 📦 Requirements

- **ZSH**: Shell integration
- **Python 3.9+**: Core functionality
- **Dependencies**: See `src/python/requirements.txt`
- **Optional**: Ollama, Gemini API, or Anthropic API for AI features

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
- ✅ v3.0.0: Simplification + AI Enhancement
  - TUI removed, CLI consolidated to 15 commands
  - Modern AI SDKs, 5 providers, embedding cache
  - Vault health dashboard, `--json` on all commands
  - Homebrew formula published
- ✅ v3.1.0: AI Refactor + Docs Redesign
  - `obs ai refactor` — 3-phase vault reorganization
  - Website redesigned (4-tab nav, hero page, expanded cookbook)
  - 206 pytest + 30 Jest tests passing
- ✅ v3.2.0: Quality Features
  - `obs ai merge-suggest` — find merge candidates via embedding similarity
  - `obs ai tag-suggest` — AI-powered tag suggestions for untagged notes
  - `obs ai quality` — score notes on 4 dimensions (no AI required)
  - 235 pytest + 30 Jest tests passing

---

**Repository**: https://github.com/Data-Wise/obsidian-cli-ops
**Documentation**: https://data-wise.github.io/obsidian-cli-ops/
