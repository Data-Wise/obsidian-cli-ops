# Keyboard Shortcuts Reference

**Complete keyboard reference for Obsidian CLI Ops TUI**

> **New to vim?** See [TUI Vim Tutorial](tui/vim-tutorial.md) for beginner-friendly guide
>
> **Want a printable version?** See [TUI Cheat Sheet](tui/cheat-sheet.txt)

---

## 🎯 Essential Shortcuts (Start Here!)

These work everywhere and will get you started:

| Key | Action | Works In |
|-----|--------|----------|
| `↑↓` / `j k` | Navigate up/down | All screens |
| `Enter` | Select/Open | All screens |
| `Esc` | Go back | All screens |
| `q` | Quit | All screens |
| `?` | Help | All screens |

**Tip:** Arrow keys work everywhere! Vim keys (`j`/`k`) are optional.

---

## 📂 Vault Browser Screen

**Purpose:** Browse and select vaults to analyze

### Navigation
| Key | Action | Description |
|-----|--------|-------------|
| `↑↓` / `j k` | Move | Navigate vault list |
| `Enter` | Select | Open selected vault |
| `Esc` | Back | Return to home screen |

### Actions
| Key | Action | Description |
|-----|--------|-------------|
| `d` | **Discover** | Find vaults in iCloud Obsidian ⭐ NEW! |
| `g` | Graph | View graph visualization |
| `s` | Stats | View statistics dashboard |
| `r` | Refresh | Reload vault list |
| `q` | Quit | Exit application |

**Pro Tip:** Press `d` to auto-discover vaults from your iCloud Obsidian folder!

---

## 📝 Note Explorer Screen

**Purpose:** Browse, search, and preview notes in a vault

### Navigation
| Key | Action | Description |
|-----|--------|-------------|
| `↑↓` / `j k` | Move | Navigate note list |
| `Enter` | View | View note details |
| `Esc` | Back | Return to vault browser |

### Search & Filter
| Key | Action | Description |
|-----|--------|-------------|
| `/` | Search | Focus search box |
| `Esc` | Clear | Clear search (when in search box) |
| `s` | Sort | Toggle sort order |

### Actions
| Key | Action | Description |
|-----|--------|-------------|
| `r` | Refresh | Reload notes |
| `q` | Quit | Exit application |

**Workflow:** Press `/` → type to search → `Enter` to view → `Esc` to go back

---

## 🕸️ Graph Visualizer Screen

**Purpose:** View knowledge graph with ASCII art visualization

### Navigation
| Key | Action | Description |
|-----|--------|-------------|
| `↑↓` / `j k` | Move | Navigate node list |
| `Enter` | Neighborhood | View note's connections |
| `Esc` | Back | Return to previous screen |

### Toggles
| Key | Action | Description |
|-----|--------|-------------|
| `h` | Hubs | Toggle hub node highlighting |
| `o` | Orphans | Toggle orphan node highlighting |
| `c` | Clusters | Toggle cluster visualization |

### Actions
| Key | Action | Description |
|-----|--------|-------------|
| `n` | Note | View selected note details |
| `r` | Refresh | Reload graph |
| `q` | Quit | Exit application |

**Tip:** Toggle hubs (`h`) and orphans (`o`) to highlight important patterns!

---

## 📊 Statistics Dashboard Screen

**Purpose:** View comprehensive vault analytics and metrics

### Navigation
| Key | Action | Description |
|-----|--------|-------------|
| `↑↓` / `j k` | Scroll | Navigate statistics |
| `Tab` | Cycle | Switch between views |
| `Esc` | Back | Return to vault browser |

### Actions
| Key | Action | Description |
|-----|--------|-------------|
| `e` | Export | Export statistics (coming soon) |
| `r` | Refresh | Reload statistics |
| `q` | Quit | Exit application |

**Views:** Press `Tab` to cycle through different stat categories

---

## 🏠 Home Screen

**Purpose:** Main menu for navigating to different sections

| Key | Action | Screen |
|-----|--------|--------|
| `v` | Vaults | Vault browser |
| `n` | Notes | Note explorer |
| `g` | Graph | Graph visualizer |
| `s` | Stats | Statistics dashboard |
| `?` | Help | Help screen |
| `q` | Quit | Exit application |

**Tip:** The TUI usually starts at the Vault Browser, bypassing the home screen.

---

## 🎨 Vim Motion Shortcuts (Optional)

For vim users, these additional motions are supported:

### Movement
| Key | Action | Same As |
|-----|--------|---------|
| `j` | Down | `↓` |
| `k` | Up | `↑` |
| `g g` | Top | Home |
| `G` | Bottom | End |
| `Ctrl+d` | Page Down | Page Down |
| `Ctrl+u` | Page Up | Page Up |

### Navigation
| Key | Action | Same As |
|-----|--------|---------|
| `h` | Back | `Esc` (in some contexts) |
| `l` | Forward | `Enter` (in some contexts) |

**Want to learn vim motions?** See [TUI Vim Tutorial](tui/vim-tutorial.md)

---

## 🌐 Universal Shortcuts

These work in **all screens**:

| Key | Action | Description |
|-----|--------|-------------|
| `q` | Quit | Exit application immediately |
| `Esc` | Back | Go to previous screen |
| `?` | Help | Show context-sensitive help |
| `Ctrl+c` | Force Quit | Emergency exit |

---

## 💡 Quick Workflows

### Discover and Explore Vaults
1. Launch TUI: `obs graph tui`
2. Press `d` to discover vaults
3. Press `Enter` to select vault
4. Press `g` to view graph or `s` for stats

### Search for a Note
1. Navigate to vault
2. Wait for notes to load
3. Press `/` to search
4. Type note name
5. Press `Enter` to view

### Analyze Graph Patterns
1. Navigate to vault
2. Press `g` for graph
3. Press `h` to highlight hubs
4. Press `o` to highlight orphans
5. Press `Enter` on nodes to explore

---

## 🆘 Troubleshooting

**Keyboard not responding:**
- Try clicking in the TUI window first
- Make sure you're not in a text input field (press `Esc`)
- Check if your terminal supports the key combination

**Vim keys not working:**
- Some keys may require focus in the list area
- Click the list first, then try vim keys
- Arrow keys always work as fallback

**Want to exit quickly:**
- Press `q` from any screen
- Or press `Ctrl+c` for emergency exit

---

## 📚 Related Guides

| Guide | Purpose |
|-------|---------|
| [TUI Vim Tutorial](tui/vim-tutorial.md) | Learn vim navigation (beginner-friendly) |
| [TUI Quick Reference](tui/quick-reference.md) | Detailed shortcuts with examples |
| [TUI Cheat Sheet](tui/cheat-sheet.txt) | Printable one-page reference |
| [Quick Start Guide](../getting-started/quickstart.md) | Get started with obs |

---

## ⚙️ Customization

Want to change keyboard shortcuts? See the source code:

```
src/python/tui/screens/vaults.py      # Vault browser bindings
src/python/tui/screens/notes.py       # Note explorer bindings
src/python/tui/screens/graph.py       # Graph visualizer bindings
src/python/tui/screens/stats.py       # Statistics bindings
```

Each screen defines its `BINDINGS` constant at the top of the file.

---

**Last Updated:** 2025-12-15 | **Version:** 2.1.0-beta

**Note:** This reference is manually maintained. For auto-generated shortcuts, see the `?` help screen within the TUI.
