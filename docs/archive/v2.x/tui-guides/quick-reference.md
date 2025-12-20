# TUI Quick Reference Card

**Obsidian CLI Ops TUI - Keyboard Shortcuts**

Print this page or keep it open while learning!

---

## 🎯 Universal Keys (Work Everywhere)

| Key | Action | Vim Equivalent |
|-----|--------|----------------|
| `↑↓` or `j/k` | Navigate up/down | `j` = down, `k` = up |
| `Enter` | Select/Open | Same |
| `Esc` | Back | Same |
| `q` | Quit TUI | Same |
| `r` | Refresh | Same |
| `?` | Help | Same |

---

## 📂 Vault Browser

**Navigate vaults → Open notes → View graph/stats**

```
┌────────────────────────────┐
│ Vaults                     │
│ ────────────────────────── │
│ > Research Lab      [100]  │ ← j/k to move
│   Knowledge Base    [50]   │   Enter to open
│   Life Admin        [25]   │   g for graph
└────────────────────────────┘
```

| Key | Action |
|-----|--------|
| `j/k` or `↑↓` | Navigate vaults |
| `Enter` | Open vault (view notes) |
| `d` | Discover vaults in iCloud Obsidian |
| `g` | View graph |
| `s` | View statistics |
| `r` | Refresh vault list |
| `Esc` | Back |
| `q` | Quit |

---

## 📝 Note Explorer

**Browse notes → Search → Preview → Open**

```
┌─ Notes ───────┬─ Preview ──┐
│ Meeting.md    │ # Meeting  │ ← j/k to navigate
│ Ideas.md      │            │   / to search
│ Project.md    │ Content... │   Enter to open
└───────────────┴────────────┘
```

| Key | Action |
|-----|--------|
| `j/k` or `↑↓` | Navigate notes |
| `Enter` | View note details |
| `/` | Search (type to filter) |
| `s` | Cycle sort: Title → Words → Date |
| `r` | Refresh |
| `Esc` | Back to vault browser |
| `q` | Quit |

---

## 🕸️ Graph Visualizer

**Explore connections → Find hubs/orphans → View neighborhoods**

```
┌─ Stats ─┬─ Nodes ─┬─ Graph ─┐
│ Density │ Hub 1   │   O─O   │ ← h/o/c to filter
│ 0.45    │ Hub 2   │   │ │   │   j/k in node list
│ Avg: 5  │ Hub 3   │   O─O   │   Enter for neighborhood
└─────────┴─────────┴─────────┘
```

| Key | Action |
|-----|--------|
| `j/k` or `↑↓` | Navigate node list |
| `Enter` | View neighborhood graph |
| `h` | Toggle hub nodes |
| `o` | Toggle orphan nodes |
| `c` | Toggle clusters |
| `n` | View note details |
| `r` | Refresh graph |
| `Esc` | Back |
| `q` | Quit |

---

## 📊 Statistics Dashboard

**View stats → Export data**

```
┌─ Overview ──┬─ Tag Analytics ─┐
│ Notes: 100  │ ▓▓▓▓░ #idea 25% │ ← Tab to cycle
│ Links: 250  │ ▓▓▓░░ #work 15% │   e to export
│ Tags:  50   │ ▓▓░░░ #note 10% │
└─────────────┴─────────────────┘
```

| Key | Action |
|-----|--------|
| `Tab` | Cycle views: Overview → Tags → Links → History |
| `e` | Export to JSON |
| `r` | Refresh |
| `Esc` | Back |
| `q` | Quit |

---

## 🎓 Vim Motion Cheat Sheet

```
      k (up)
      ↑
      │
h ←───┼───→ l
(left)│    (right)
      ↓
      j (down)
```

**Remember:**
- `h` = left (h is on the left side of the keyboard)
- `l` = right (l is on the right side)
- `j` = down (j looks like a down arrow ↓)
- `k` = up (k points up)

**Hands on home row:**
```
Left:   A S D F     (pinky → index)
Right:  J K L ;     (index → pinky)
              ↑
              Home row for j/k navigation!
```

---

## 🔥 Common Workflows

### Browse Vaults
```
obs graph tui → j j j → Enter
   ↓            ↓         ↓
 Launch    Navigate    Open
```

### Search Notes
```
/ → meeting → Enter → j → Enter
↓      ↓        ↓      ↓     ↓
Search Type   Jump  Select Open
```

### Explore Graph
```
g → h → j j j → Enter → Esc
↓   ↓      ↓       ↓      ↓
Graph Hubs Select Neighborhood Back
```

### View Stats & Export
```
s → Tab → Tab → e → Esc
↓    ↓     ↓     ↓    ↓
Stats Next Next Export Back
```

### Quick Exit
```
Esc → Esc → q
 ↓      ↓     ↓
Back  Back  Quit
```

---

## 💡 Pro Tips

1. **Keep hands on home row:** `j/k` for navigation, `Enter` for selection
2. **Use Tab in stats:** Quickly cycle through different views
3. **Search is powerful:** `/` then type, filters in real-time
4. **Esc is your friend:** Backs out of any screen
5. **Footer shows keys:** Look at bottom of screen for reminders

---

## 🎯 Learning Priority

**Week 1:** Essential
- `j/k` - Navigate (or use arrow keys)
- `Enter` - Select
- `Esc` - Back
- `q` - Quit

**Week 2:** Actions
- `g` - Graph
- `s` - Stats
- `/` - Search
- `r` - Refresh

**Week 3:** Advanced
- `h/o/c` - Filter graph
- `Tab` - Cycle views
- `e` - Export
- `n` - View note

---

## 📋 All Keys Alphabetically

| Key | Action | Where |
|-----|--------|-------|
| `/` | Search | Notes |
| `c` | Clusters | Graph |
| `e` | Export | Stats |
| `Esc` | Back | All |
| `Enter` | Select | All |
| `g` | Graph view | Vaults |
| `h` | Hubs | Graph |
| `j` | Down | All |
| `k` | Up | All |
| `l` | Right | All (if needed) |
| `n` | View note | Graph |
| `o` | Orphans | Graph |
| `q` | Quit | All |
| `r` | Refresh | All |
| `s` | Stats/Sort | Vaults/Notes |
| `Tab` | Cycle views | Stats |
| `?` | Help | All (if available) |

---

## 🚀 Launch Command

```bash
obs graph tui              # Launch TUI
obs graph tui --vault-id X # Open specific vault
```

---

**Print this card and keep it handy!** 📄

After a few sessions, these shortcuts become muscle memory. 🎉
