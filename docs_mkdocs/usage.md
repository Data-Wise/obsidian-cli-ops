# Usage Guide

> **Just type `obs` - it does the right thing!**

## Philosophy

**Version 3.0** focuses on doing one thing exceptionally well: managing Obsidian vaults from the command line.

- **Zero-Friction Start**: Just type `obs`
- **iCloud-First**: Auto-detects your Obsidian vaults
- **ADHD-Friendly**: 15 focused commands, smart defaults, progressive disclosure
- **AI-Powered**: Optional AI features for deeper vault analysis

---

## The One Command

```bash
obs
```

Lists all your registered vaults with stats at a glance. This is your starting point for everything.

---

## Command Reference

### Primary Commands

| Command | What It Does |
|---------|-------------|
| `obs` | List all vaults |
| `obs stats <vault>` | Show vault statistics |
| `obs discover <path>` | Find vaults in a directory |

### Graph Analysis

| Command | What It Does |
|---------|-------------|
| `obs analyze <vault>` | Analyze vault graph metrics |

### AI Features

| Command | What It Does |
|---------|-------------|
| `obs ai status` | Check AI provider availability |
| `obs ai setup` | Interactive setup wizard |
| `obs ai test` | Test provider connections |
| `obs ai similar <note_id>` | Find semantically similar notes |
| `obs ai analyze <note_id>` | Deep AI analysis of a note |
| `obs ai duplicates <vault>` | Detect potential duplicate content |
| `obs ai suggest-links <note_id>` | Find unlinked related notes |
| `obs ai gaps <vault>` | Detect stub notes and knowledge gaps |
| `obs ai summarize <vault>` | Generate theme analysis across vault |
| `obs ai refactor <vault>` | AI-powered vault reorganization suggestions |

### Utilities

| Command | What It Does |
|---------|-------------|
| `obs help` | Quick help (essential commands) |
| `obs help --all` | Full command reference |
| `obs version` | Show version |

---

## Common Workflows

### First-Time Setup

```bash
# Install dependencies
pip3 install -r src/python/requirements.txt

# Initialize the database
python3 src/python/obs_cli.py db init

# Discover your vaults
obs discover ~/Documents
obs discover ~/Library/Mobile\ Documents/iCloud~md~obsidian/Documents
```

### Daily Usage

```bash
# See all your vaults
obs

# Check a vault's health
obs stats MyVault

# Analyze the knowledge graph
obs analyze MyVault
```

### Vault Lookup

Commands that take `<vault>` accept either a vault name or an ID prefix:

```bash
obs stats MyVault        # By name
obs stats a812           # By ID prefix
obs analyze Research_Lab # By name
```

If a prefix matches multiple vaults, obs tells you which ones matched so you can be more specific.

### AI-Powered Analysis

```bash
# Check which providers are available
obs ai status

# Set up a provider
obs ai setup

# Find similar notes
obs ai similar <note_id>

# Detect duplicates across a vault
obs ai duplicates MyVault
```

??? tip "Choosing an AI provider"
    - **Privacy first**: Use `ollama` (100% local)
    - **Quality first**: Use `claude-cli`
    - **Speed first**: Use `gemini-api`
    - **No API key**: Use `gemini-cli` or `claude-cli`

---

## Vault Discovery

obs finds Obsidian vaults by looking for directories containing `.obsidian` folders.

```bash
# Search a directory
obs discover ~/Documents

# Auto-discover from iCloud
obs discover ~/Library/Mobile\ Documents/iCloud~md~obsidian/Documents

# Discover and scan in one step
obs discover ~/Documents --scan
```

---

## Graph Analysis

The `analyze` command calculates knowledge graph metrics:

```bash
obs analyze MyVault
```

**Metrics include:**

- **Density** - How interconnected your vault is (0.0 to 1.0)
- **Clusters** - Groups of tightly related notes
- **Hub notes** - Highly connected central notes
- **Orphans** - Notes with no links (may need integration)
- **Broken links** - Wikilinks pointing to non-existent notes

Add `-v` for detailed output including top hub notes:

```bash
obs analyze MyVault -v
```

See the [Graph Analysis Tutorial](tutorials/graph-analysis.md) for a deep dive.

---

## Configuration

### Default iCloud Location

```
~/Library/Mobile Documents/iCloud~md~obsidian/Documents
```

Auto-detected on first run - no configuration needed.

### Database Location

```
~/.config/obs/vault_db.sqlite
```

All data is stored locally. No data leaves your machine.

### Custom Root (Optional)

Set `OBS_ROOT` to override the default vault search location:

```bash
OBS_ROOT="/path/to/my/vaults"
```

---

## Progressive Disclosure

obs is designed for ADHD-friendly progressive learning:

1. **Level 1**: Just type `obs` (one command)
2. **Level 2**: Learn `stats` and `discover` (3 commands)
3. **Level 3**: Use `analyze` for graph insights (4 commands)
4. **Level 4**: Explore AI features (10 commands)

**You only need Level 1 to get started.**

---

## Troubleshooting

### "No vaults found"

```bash
# Check iCloud location
ls ~/Library/Mobile\ Documents/iCloud~md~obsidian/Documents/

# Or discover in a specific location
obs discover ~/Documents
```

### "Command not found: obs"

```bash
# Reload shell
source ~/.zshrc

# Check symlink
ls -la ~/.config/zsh/functions/obs.zsh
```

### "Python CLI not found"

```bash
# Check Python path (should be /opt/homebrew/bin/python3)
which python3
```

---

## Next Steps

| Want to... | Go to |
|------------|-------|
| Follow a step-by-step guide | [Getting Started Tutorial](tutorials/getting-started.md) |
| Learn graph analysis | [Graph Analysis Tutorial](tutorials/graph-analysis.md) |
| Set up AI features | [AI Features Tutorial](tutorials/ai-features.md) |
| See all commands | `obs help --all` |
