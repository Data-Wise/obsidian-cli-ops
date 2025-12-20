# TUI Vim Navigation Tutorial for Beginners

**Welcome!** This guide will teach you how to navigate the Obsidian CLI Ops TUI using vim-style keyboard shortcuts.

---

## 🎯 Philosophy: Keep Your Hands on the Home Row

Vim shortcuts keep your hands centered on the keyboard's home row, making navigation faster and more comfortable than reaching for arrow keys or the mouse.

**Home Row Position:**
```
Left hand:  A S D F
Right hand: J K L ;
```

---

## 📚 Level 1: Essential Movement (Start Here!)

### Arrow Keys Work!
If you're new to vim, **arrow keys work perfectly** in the TUI. Use them while you learn the vim shortcuts.

### Basic Vim Movement

| Key | Direction | Remember As |
|-----|-----------|-------------|
| `j` | Down | **J**ump down |
| `k` | Up | **K**ick up |
| `h` | Left | ← **H** is on the left |
| `l` | Right | → **L** is on the right |

**Try this in the TUI:**
1. Launch: `obs graph tui`
2. Press `j` several times → cursor moves down
3. Press `k` several times → cursor moves up
4. Press `h` and `l` → (if horizontal scrolling is available)

---

## 📚 Level 2: Actions & Navigation

### Universal Keys (Work on All Screens)

| Key | Action | What It Does |
|-----|--------|--------------|
| `Enter` | Select/Open | Opens selected item |
| `Esc` | Back | Go back to previous screen |
| `q` | Quit | Exit the TUI |
| `r` | Refresh | Reload current screen data |
| `?` | Help | Show help (if available) |

**Practice Flow:**
1. `j` to move down to a vault
2. `Enter` to open it
3. `Esc` to go back
4. `q` to quit

---

## 📚 Level 3: Screen-Specific Shortcuts

### Vault Browser (Main Screen)

```
  ┌─ Vault List ─┐
  │ > Vault 1    │  ← Use j/k to navigate
  │   Vault 2    │
  │   Vault 3    │
  └──────────────┘
```

| Key | Action | What It Does |
|-----|--------|--------------|
| `j/k` | Navigate | Move through vault list |
| `Enter` | Open | Open selected vault's notes |
| `d` | Discover | Find vaults in iCloud Obsidian (auto-scan) |
| `g` | Graph | View vault's knowledge graph |
| `s` | Stats | View vault statistics |
| `r` | Refresh | Reload vault list |
| `Esc` | Back | Return to previous screen |
| `q` | Quit | Exit TUI |

**Common Workflow:**
```bash
j j j         # Move down 3 vaults
Enter         # Open vault
Esc           # Go back
g             # View graph
Esc           # Go back
s             # View stats
```

### Note Explorer

```
  ┌─ Notes ─┬─ Preview ─┐
  │ Note 1  │ Content   │  ← j/k to navigate notes
  │ Note 2  │ appears   │    Enter to view full note
  │ Note 3  │ here      │    / to search
  └─────────┴───────────┘
```

| Key | Action | What It Does |
|-----|--------|--------------|
| `j/k` | Navigate | Move through note list |
| `Enter` | View | Open note in detail view |
| `/` | Search | Focus search bar (type to filter) |
| `s` | Sort | Cycle: Title → Word Count → Date |
| `r` | Refresh | Reload notes |
| `Esc` | Back | Return to vault browser |
| `q` | Quit | Exit TUI |

**Search Workflow:**
```bash
/             # Press slash to search
meeting       # Type search term
Enter         # Jump to results
j j           # Navigate results
Enter         # Open a note
Esc           # Go back
```

### Graph Visualizer

```
  ┌─ Stats ─┬─ Nodes ─┬─ Graph ─┐
  │         │ Hub 1   │   O─O   │  ← j/k in node list
  │ Metrics │ Hub 2   │   │ │   │    h/o/c to filter
  │         │ Hub 3   │   O─O   │    Enter for neighborhood
  └─────────┴─────────┴─────────┘
```

| Key | Action | What It Does |
|-----|--------|--------------|
| `j/k` | Navigate | Move through node lists |
| `Enter` | Neighborhood | View 1-hop neighborhood graph |
| `h` | Hubs | Toggle hub nodes view |
| `o` | Orphans | Toggle orphan nodes view |
| `c` | Clusters | Toggle clusters view |
| `n` | View Note | Open selected note |
| `r` | Refresh | Recalculate graph |
| `Esc` | Back | Return to vault browser |
| `q` | Quit | Exit TUI |

**Exploration Workflow:**
```bash
h             # Show hub nodes
j j j         # Navigate to interesting hub
Enter         # View its neighborhood
Esc           # Go back
o             # Show orphan nodes
j             # Navigate to orphan
n             # View note details
```

### Statistics Dashboard

```
  ┌─ Overview ─┬─ Details ────┐
  │ Total: 100 │ ▓▓▓▓░ Tags   │  ← Tab to switch views
  │ Links: 50  │ ▓▓░░░ Links  │    e to export
  │ Tags: 20   │ ▓░░░░ Types  │    r to refresh
  └────────────┴──────────────┘
```

| Key | Action | What It Does |
|-----|--------|--------------|
| `Tab` | Next View | Cycle: Overview → Tags → Links → History |
| `e` | Export | Export statistics to JSON |
| `r` | Refresh | Reload statistics |
| `Esc` | Back | Return to vault browser |
| `q` | Quit | Exit TUI |

**Analysis Workflow:**
```bash
s             # Open stats from vault browser
Tab           # View tag analytics
Tab           # View link distribution
Tab           # View scan history
e             # Export to JSON
Esc           # Go back
```

---

## 📚 Level 4: Advanced Patterns

### Rapid Navigation

**Jump Down Multiple Lines:**
```bash
j j j j j     # Press j five times
# OR
5j            # Type number then j (if supported)
```

**Quick Exploration:**
```bash
obs graph tui → j j j → Enter → / search → j → Enter → Esc → q
   ↓            ↓         ↓       ↓          ↓    ↓      ↓     ↓
  Launch    Navigate   Open   Search    Select View  Back  Quit
```

### Muscle Memory Training

**Practice these combos:**
1. `j j j Enter` - Navigate and open
2. `/ term Enter` - Search and jump to results
3. `Esc Esc q` - Back out and quit
4. `r` - Refresh when data looks stale

---

## 🎓 Learning Path

### Day 1: Use Arrow Keys + Actions
- ↑↓ for navigation
- `Enter` to open
- `Esc` to go back
- `q` to quit

### Day 2-3: Add j/k Movement
- Replace ↓ with `j`
- Replace ↑ with `k`
- Keep using `Enter`, `Esc`, `q`

### Week 1: Add Screen Actions
- Learn `g` (graph), `s` (stats), `n` (notes)
- Practice `/` for search
- Try `r` for refresh

### Week 2+: Flow State
- Navigation becomes automatic
- Hands stay on home row
- Fast exploration without thinking

---

## 💡 Tips for Vim Beginners

### 1. **Don't Panic!**
Arrow keys work perfectly. Learn vim shortcuts gradually.

### 2. **Remember the Patterns**
Most screens use the same keys:
- `j/k` = navigate
- `Enter` = select
- `Esc` = back
- `q` = quit
- `r` = refresh

### 3. **Muscle Memory Takes Time**
Your fingers will reach for arrow keys at first. That's normal! After a few sessions, `j/k` becomes natural.

### 4. **Use the Footer**
The bottom of the screen shows available keys:
```
Esc: Back | Enter: Open | g: Graph | s: Stats | r: Refresh | q: Quit
```

### 5. **Start Simple**
Master `j`, `k`, `Enter`, `Esc` first. Add more keys as you feel comfortable.

---

## 🚀 Quick Start Cheat Sheet

**First Time User:**
```bash
obs graph tui    # Launch TUI
j j j            # Move down (or use arrow keys)
Enter            # Open something
Esc              # Go back
q                # Quit
```

**Comfortable User:**
```bash
obs graph tui → g → j j → Enter → Esc → s → Tab → e → Esc → q
```

**Power User:**
```bash
obs graph tui
/research        # Search
j j Enter        # Navigate and open
g                # View graph
h                # Show hubs
j Enter          # Explore neighborhood
n                # View note details
Esc Esc q        # Exit
```

---

## 🔗 Related Docs

- **Quick Reference:** `TUI_QUICK_REFERENCE.md` - One-page cheat sheet
- **Full Manual:** `docs_mkdocs/tui-guide.md` - Complete TUI documentation
- **Keyboard Shortcuts:** `KEYBOARD_SHORTCUTS.md` - All bindings

---

## ❓ Common Questions

**Q: Do I have to use vim keys?**
A: No! Arrow keys work perfectly. Vim keys are optional for speed.

**Q: Why are the keys hjkl?**
A: Historical reasons - old keyboards didn't have arrow keys. `h` and `l` are left/right on the home row, `j` looks like a down arrow, `k` points up.

**Q: Can I remap keys?**
A: Not currently, but it's on the roadmap.

**Q: What if I press the wrong key?**
A: `Esc` is your friend! It backs out of most screens. Worst case, `q` quits.

---

**Happy exploring!** 🎉 Remember: Start with arrow keys, add vim shortcuts gradually, and you'll be navigating like a pro in no time.
