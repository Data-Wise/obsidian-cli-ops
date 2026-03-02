# 🚀 Quick Start Guide

> **Get up and running with Obsidian CLI Ops in 5 minutes**

## What is Obsidian CLI Ops?

`obs` is an intelligent command-line tool that **works exactly like the Obsidian app** - just type `obs` and it opens your last vault!

- 🎯 **Zero-Friction Start** - Just type `obs` (opens last vault or shows picker)
- 🌥️ **iCloud-First** - Auto-detects standard Obsidian iCloud location
- 📊 **Graph Analysis** - PageRank, centrality, hub/orphan detection
- 🖥️ **Interactive TUI** - Full-screen terminal UI with vim navigation
- 🔍 **Smart Discovery** - Auto-find and scan all your vaults
- 🤖 **AI Features** - Note similarity, duplicate detection (100% local, free, private)
- 🔗 **R Integration** - Seamless R Project ↔ Obsidian workflow (`obs r`)

**Current Version**: 2.1.0 (Option D - Obsidian App Clone)

---

## 🏃 Quick Setup

### 1. Install Dependencies

```bash
# Install Python packages
pip3 install -r src/python/requirements.txt

# Install Node.js packages (for testing)
npm install
```

### 2. Symlink the Command

```bash
# Create symlink
ln -s "$(pwd)/src/obs.zsh" ~/.config/zsh/functions/obs.zsh

# Add to .zshrc if not already there
echo "autoload -Uz obs" >> ~/.zshrc

# Reload shell
source ~/.zshrc
```

### 3. Initialize Database

```bash
# Create database and schema
python3 src/python/obs_cli.py db init
```

### 4. Start Using (Zero Configuration!)

```bash
# Just type obs - it auto-detects iCloud vaults!
obs

# If no vaults found, use vault picker (press 'd' to discover)
# Default location: ~/Library/Mobile Documents/iCloud~md~obsidian/Documents

# Or discover in specific directory
obs manage open ~/Documents
```

**💡 Pro Tip:** No configuration needed! `obs` automatically detects your iCloud Obsidian vaults.

---

## 🎯 Essential Commands

### The One Command (90% of usage)

```bash
obs                     # Open last vault (or show picker)
```

**That's it!** Works exactly like launching the Obsidian app.

---

### Primary Commands (Obsidian-style)

```bash
obs switch              # Vault switcher (like "Open another vault")
obs manage              # Manage vaults (like "Manage Vaults" menu)
obs open <name>         # Open specific vault
```

### Quick Actions

```bash
obs graph [vault]       # Show graph visualization
obs stats [vault]       # View statistics
obs search <query>      # Search across vaults (coming soon)
```

### Vault Management

```bash
obs manage create       # Create new vault
obs manage open <path>  # Open folder as vault
obs manage info <id>    # Show vault details
```

### Graph Analysis

```bash
# Analyze vault graph
obs analyze <vault>

# View statistics
obs stats                  # All vaults
obs stats <vault>       # Specific vault
```

### Interactive TUI

```bash
# Launch TUI (now the default!)
obs                           # Opens last vault or shows picker

# Legacy commands (still work)
obs tui                       # Same as obs
obs tui --vault-id <vault> # Open specific vault
obs tui --screen vaults       # Open specific screen
```

### AI Features (Optional)

```bash
# Setup AI (100% local, free, private)
obs ai setup --quick

# Find similar notes
obs ai similar <note_id>
```

---

## 🖥️ Using the TUI

The TUI (Terminal User Interface) is now **the default** - just type `obs`!

### Launch TUI
```bash
obs                     # Opens last vault or shows picker (NEW!)
```

**Works like Obsidian app:** Opens your last vault automatically, or shows vault picker if it's your first time.

### Navigation Basics

**New to vim?** Don't worry! The TUI works with:
- ✅ **Arrow keys** - Move up/down
- ✅ **Enter** - Select/open
- ✅ **Esc** - Go back
- ✅ **q** - Quit

**Want to learn vim motions?** See [TUI Vim Tutorial](../guides/tui/vim-tutorial.md)

### Quick Actions

| Key | Action | Description |
|-----|--------|-------------|
| `d` | Discover | Find vaults in iCloud Obsidian |
| `g` | Graph | View graph visualization |
| `s` | Stats | View statistics dashboard |
| `r` | Refresh | Reload data |
| `q` | Quit | Exit TUI |

**See full shortcuts**: [TUI Quick Reference](../guides/tui/quick-reference.md)

---

## 📚 Next Steps

### Beginner Path

1. ✅ **You are here** - Quick start complete!
2. 📖 [TUI Vim Tutorial](../guides/tui/vim-tutorial.md) - Learn vim navigation (5 min)
3. 🖨️ [TUI Cheat Sheet](../guides/tui/cheat-sheet.txt) - Print for desk reference
4. 🎮 Try the TUI - Explore your vaults interactively

### Advanced Path

1. 📊 [Graph Analysis](../../developer/architecture.md) - Understanding the knowledge graph
2. 🤖 [AI Setup](../guides/ai-setup.md) - Enable AI features (local, free, private)
3. 🔧 [Unified Command](../guides/unified-command.md) - Master the CLI
4. 🧪 [Testing Guide](../../developer/testing/overview.md) - Run the test suite

### Developer Path

1. 🏗️ [Architecture](../../developer/architecture.md) - Three-layer design
2. 🧪 [Testing](../../developer/testing/overview.md) - Test suite overview
3. 📝 [CLAUDE.md](../../../CLAUDE.md) - Developer guide
4. 🤝 Contributing - Pick a feature and start building!

---

## 🎓 Learning Resources

### Documentation Structure

```
docs/
├── user/           # User guides (you are here!)
│   ├── getting-started/
│   ├── guides/tui/     # TUI navigation guides
│   └── guides/         # Command guides
├── developer/      # Architecture and testing
├── planning/       # Project roadmap and status
└── releases/       # Release notes
```

### Key Documents

| Document | Purpose |
|----------|---------|
| [TUI Vim Tutorial](../guides/tui/vim-tutorial.md) | Learn vim navigation (beginner-friendly) |
| [TUI Quick Reference](../guides/tui/quick-reference.md) | All keyboard shortcuts |
| [TUI Cheat Sheet](../guides/tui/cheat-sheet.txt) | Printable one-page reference |
| [Architecture](../../developer/architecture.md) | How the system works |
| [Project Hub](../../planning/project-hub.md) | ADHD-friendly control center |

---

## 💡 Common Workflows

### Daily Vault Exploration

```bash
# Launch TUI
obs tui

# Press 'd' to discover vaults from iCloud
# Press 'Enter' to select a vault
# Press 'g' to view graph
# Press 's' to view statistics
# Press 'q' to quit
```

### Analyze Specific Vault

```bash
# List vaults to get ID
obs vaults

# Analyze vault
obs analyze vault_123

# View detailed stats
obs stats vault_123
```

### Find and Fix Issues

```bash
# Launch TUI
obs tui

# Navigate to vault
# Press 'g' to see graph
# Look for orphaned notes (highlighted in red)
# Press 's' to see statistics
# Check broken links section
```

---

## 🆘 Troubleshooting

### Command not found: obs

```bash
# Make sure you sourced your .zshrc
source ~/.zshrc

# Or manually load the function
autoload -Uz obs
```

### Python not found

```bash
# The tool uses full path to Python
# If you get errors, check your Python installation
which python3

# Should be: /opt/homebrew/bin/python3
```

### TUI errors

```bash
# Reinitialize the database
python3 src/python/obs_cli.py db init

# Rescan your vaults
obs discover ~/Documents --scan
```

### Need more help?

- 📖 [Troubleshooting Guide](../../developer/troubleshooting.md)
- 🐛 [Report Issues](https://github.com/Data-Wise/obsidian-cli-ops/issues)
- 💬 [Discussions](https://github.com/Data-Wise/obsidian-cli-ops/discussions)

---

## ✨ What's Next?

You're all set! Here are some ideas:

1. 🎮 **Try the TUI** - Launch `obs tui` and explore
2. 📊 **Analyze your vaults** - See your knowledge graph
3. 📚 **Learn vim motions** - Make navigation effortless
4. 🤖 **Enable AI** - Try local, free note similarity
5. 🔧 **Customize** - Explore all the features

**Happy knowledge management! 🚀**

---

**Last Updated:** 2025-12-15
**Version:** 2.1.0-beta
**Status:** Production Ready (Phases 1-4 Complete)
