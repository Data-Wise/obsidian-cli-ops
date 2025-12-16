# Usage Guide

> **Works exactly like the Obsidian app - just type `obs`!**

## Philosophy

**Version 2.2.0** implements **Option D** - a complete redesign that mimics the official Obsidian app's behavior, plus AI-powered features.

- **Zero-Friction Start**: Just type `obs` (like clicking the Obsidian icon)
- **iCloud-First**: Auto-detects `~/Library/Mobile Documents/iCloud~md~obsidian/Documents`
- **Last-Vault Tracking**: Remembers where you were (like Obsidian app)
- **ADHD-Friendly**: One command, smart defaults, progressive disclosure

## The One Command

```bash
obs
```

**What it does:**
1. Opens your last-used vault automatically (like Obsidian app)
2. Shows vault picker if no last vault
3. Auto-detects iCloud vaults on first run

**That's it!** Works exactly like launching Obsidian.

## Primary Commands (90% of usage)

```bash
obs                     # Open last vault (or show picker)
obs switch [name]       # Vault switcher (like "Open another vault")
obs manage              # Manage vaults (like "Manage Vaults" menu)
```

**Obsidian App Equivalent:**
- `obs` = Clicking Obsidian icon
- `obs switch` = "Open another vault" command
- `obs manage` = "Manage Vaults" menu

## Quick Actions

### Open Specific Vault

```bash
obs open <name>         # Open vault by name
```

**Example:**
```bash
obs open Research_Lab
```

### Graph Visualization

```bash
obs graph [vault]       # Show graph (current vault or specified)
```

**Examples:**
```bash
obs graph               # Graph of current/last vault
obs graph <vault_id>    # Graph of specific vault
```

### Statistics

```bash
obs stats [vault]       # Show stats (all vaults or specified)
```

**Examples:**
```bash
obs stats               # Global statistics
obs stats <vault_id>    # Vault-specific statistics
```

## Vault Management

### Manage Vaults Menu

```bash
obs manage              # Show manage menu (like Obsidian)
```

**Subcommands:**

```bash
obs manage create       # Create new vault
obs manage open <path>  # Open folder as vault
obs manage remove <id>  # Remove vault from database
obs manage rename       # Rename vault
obs manage info <id>    # Show vault details
```

**Examples:**
```bash
# Open folder as vault (discovers and scans)
obs manage open ~/Documents/MyVault

# Show vault information
obs manage info vault_123
```

## AI Features

**Version 2.2.0** adds powerful AI-powered note analysis with multi-provider support.

### AI Provider Management

```bash
obs ai status           # Check provider availability
obs ai setup            # Interactive setup wizard
obs ai test             # Test provider functionality
```

**Supported Providers:**
- `gemini-api` - Fast batch operations (default)
- `gemini-cli` - CLI fallback
- `claude-cli` - High-quality analysis
- `ollama` - Local, free, private

### Find Similar Notes

```bash
obs ai similar <note_id>              # Find similar notes
obs ai similar <note_id> --limit 20   # Limit results
obs ai similar <note_id> --threshold 0.5  # Min similarity
```

**Example:**
```bash
obs ai similar abc123 --limit 10
```

### Analyze Note

```bash
obs ai analyze <note_id>              # Deep note analysis
obs ai analyze <note_id> --provider gemini-api
```

**Returns:**
- Topics and themes
- Suggested tags
- Quality scores
- Improvement suggestions

### Find Duplicates

```bash
obs ai duplicates <vault_id>          # Scan vault for duplicates
obs ai duplicates <vault_id> --threshold 0.85
obs ai duplicates <vault_id> --limit 50
```

**Example:**
```bash
obs ai duplicates my-vault --threshold 0.9
```

## R Integration

**Shortened from `obs r-dev` to `obs r`** (ADHD-friendly!)

### Link R Project

```bash
obs r link              # Link current R project to vault folder
obs r unlink            # Remove R project mapping
obs r status            # Show current link status
```

### Copy Artifacts

```bash
obs r log <file>        # Copy result to vault (06_Analysis)
obs r draft <file>      # Copy draft to vault (02_Drafts)
```

**Example:**
```bash
obs r log result.png -m "Analysis complete"
```

### Search Theory Notes

```bash
obs r context <term>    # Search Knowledge_Base for theory
```

**Example:**
```bash
obs r context "mediation analysis"
```

## Legacy Commands

**All old commands still work** (backward compatible):

| Legacy Command | New Command | Notes |
|----------------|-------------|-------|
| `obs tui` | `obs` | Now the default! |
| `obs discover` | `obs manage open` | Still works |
| `obs vaults` | `obs switch` | Still works |
| `obs r-dev` | `obs r` | Both work |

## Getting Help

### Simple Help (5 commands)

```bash
obs help                # Quick start guide
```

### Detailed Help (12 commands)

```bash
obs help --all          # Show all commands
```

### Namespace Help

```bash
obs manage              # Show manage subcommands
obs ai                  # Show AI subcommands
obs r                   # Show R subcommands
```

## Common Workflows

### Daily Usage

```bash
# Open last vault (works like Obsidian app)
obs

# Navigate with vim keys or arrows
# Press 'g' for graph, 's' for stats
# Press 'q' to quit
```

### Switch Between Vaults

```bash
# Show vault switcher
obs switch

# Or open specific vault directly
obs open Research_Lab
```

### Discover New Vaults

```bash
# Open folder as vault
obs manage open ~/Documents/NewVault

# Or in TUI: press 'd' to discover from iCloud
obs
# (then press 'd')
```

### R Project Workflow

```bash
# In your R project directory
cd ~/projects/my-r-project

# Link to vault folder
obs r link Research_Lab

# Copy a plot
obs r log figure1.png -m "Final version"

# Search for theory
obs r context "regression"
```

## Configuration

### Default iCloud Location

```
~/Library/Mobile Documents/iCloud~md~obsidian/Documents
```

**Auto-detected on first run** - no configuration needed!

### Last Vault Tracking

```
~/.config/obs/last_vault
```

Updated automatically when you open a vault.

### Custom Configuration (Optional)

```
~/.config/obs/config
```

Set `OBS_ROOT` to override iCloud default:

```bash
OBS_ROOT="/path/to/my/vaults"
```

## Progressive Disclosure

**ADHD-Friendly Design:**

1. **Level 1**: Just type `obs` (one command)
2. **Level 2**: Learn `switch` and `manage` (3 commands)
3. **Level 3**: Explore quick actions (6 commands)
4. **Level 4**: Use AI and R features (advanced)

**You only need Level 1 to get started!**

## Keyboard Shortcuts in TUI

Press `?` in TUI for complete keyboard reference.

**Quick shortcuts:**
- `g` - Show graph visualization
- `s` - Show statistics
- `d` - Discover vaults from iCloud
- `r` - Refresh current view
- `q` - Quit TUI

## Troubleshooting

### "No vaults found"

```bash
# Check iCloud location
ls ~/Library/Mobile\ Documents/iCloud~md~obsidian/Documents/

# Or discover in specific location
obs manage open ~/Documents
```

### "Command not found: obs"

```bash
# Reload shell
source ~/.zshrc

# Or check symlink
ls -la ~/.config/zsh/functions/obs.zsh
```

### "Python CLI not found"

```bash
# Check Python path in obs.zsh
# Should be: /opt/homebrew/bin/python3
which python3
```

---

**Remember:** Just type `obs` - it does the right thing! 🚀
