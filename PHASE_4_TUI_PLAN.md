# Phase 4: TUI/Visualization Implementation Plan

**Priority:** HIGH (moved ahead of Phase 3)
**Status:** 🚧 In Progress
**Target:** Next sprint
**Framework:** Textual (Python TUI framework)

---

## 🎯 Why TUI First?

**Strategic Decision:** Build visualization before AI features

**Rationale:**
1. **Immediate Value** - Visualize existing data (vaults, notes, graphs) from Phase 1
2. **Better UX** - Interactive exploration vs command-line output
3. **Foundation for AI** - TUI ready when Phase 3 features arrive
4. **ADHD-Friendly** - Visual, interactive, clear navigation
5. **Standalone Utility** - Useful even without AI features

---

## 📊 What We Can Visualize Now

### Existing Data from Phase 1-2

✅ **Vault Information:**
- List of discovered vaults
- Vault statistics (note count, link count)
- Scan history

✅ **Note Data:**
- All notes in a vault
- Note metadata (title, path, size)
- Content preview

✅ **Graph Structure:**
- Wikilinks (source → target)
- Backlinks (incoming links)
- Orphaned notes
- Hub notes (highly connected)

✅ **Graph Metrics:**
- PageRank scores
- In/out degree
- Centrality measures
- Clustering coefficients

✅ **Tags:**
- All tags in vault
- Tag usage statistics
- Notes by tag

---

## 🏗️ Architecture

### Technology Stack

**Primary Framework:** Textual
- Modern Python TUI framework
- Rich widget library
- Reactive/async architecture
- Beautiful terminal rendering
- Already in requirements.txt

**Supporting Libraries:**
- `rich` - Text formatting and tables
- `networkx` - Graph data (already used)
- Database - SQLite (already set up)

### Project Structure

```
src/python/
├── tui/
│   ├── __init__.py
│   ├── app.py              # Main TUI application
│   ├── screens/
│   │   ├── __init__.py
│   │   ├── home.py         # Home dashboard
│   │   ├── vaults.py       # Vault browser
│   │   ├── notes.py        # Note explorer
│   │   ├── graph.py        # Graph visualizer
│   │   └── stats.py        # Statistics dashboard
│   ├── widgets/
│   │   ├── __init__.py
│   │   ├── vault_tree.py   # Vault directory tree
│   │   ├── note_list.py    # Searchable note list
│   │   ├── graph_view.py   # ASCII graph visualization
│   │   ├── preview.py      # Note content preview
│   │   └── stats_panel.py  # Statistics panel
│   └── utils.py            # Helper functions
```

---

## 📋 Implementation Phases

### Phase 4.1: Foundation (Week 1, Days 1-2)

**Goal:** Basic TUI framework and navigation

**Tasks:**
- [x] Textual already in requirements.txt
- [ ] Create `src/python/tui/` directory structure
- [ ] Build main app skeleton (`app.py`)
- [ ] Implement home screen with menu
- [ ] Add keyboard navigation (arrow keys, vim keys)
- [ ] Add quit/help functionality

**Deliverable:** Working TUI that launches and navigates between empty screens

**Commands:**
```bash
obs tui              # Launch TUI
obs tui --vault-id 1 # Launch directly to vault view
```

### Phase 4.2: Vault Browser (Week 1, Days 3-4)

**Goal:** Interactive vault exploration

**Features:**
- List all vaults from database
- Show vault statistics
- Select vault to explore
- Navigate with keyboard

**Screen Design:**
```
╭─ Obsidian CLI Ops - Vault Browser ─────────────────────╮
│                                                         │
│  📁 Vaults                                              │
│  ┌───────────────────────────────────────────────────┐ │
│  │ ▸ Research Lab         [1,247 notes] [2,891 links]│ │
│  │ ▸ Knowledge Base       [  456 notes] [  892 links]│ │
│  │ ▸ Personal             [   89 notes] [   45 links]│ │
│  └───────────────────────────────────────────────────┘ │
│                                                         │
│  Last Scanned: 2025-12-13 10:30 AM                     │
│  Database: ~/.config/obs/vault_db.sqlite                │
│                                                         │
│  [↑↓] Navigate  [Enter] Open  [S] Stats  [Q] Quit      │
╰─────────────────────────────────────────────────────────╯
```

**Tasks:**
- [ ] Query vaults from database
- [ ] Display vault list with stats
- [ ] Implement selection
- [ ] Add vault details panel

### Phase 4.3: Note Explorer (Week 1, Days 5-7)

**Goal:** Browse and search notes within a vault

**Features:**
- List all notes in selected vault
- Search/filter by title
- Sort by various criteria
- Preview note content

**Screen Design:**
```
╭─ Research Lab Notes ────────────────────────────────────╮
│                                                         │
│ Search: [mediation________]           347 notes found  │
│                                                         │
│ ┌─ Notes ─────────────┐  ┌─ Preview ────────────────┐ │
│ │ ▸ Mediation Anal... │  │ # Mediation Analysis     │ │
│ │   Causal Mediati... │  │                          │ │
│ │   Direct Effects... │  │ Overview of mediation    │ │
│ │   Indirect Path ... │  │ methods in causal...     │ │
│ │   ...               │  │                          │ │
│ │                     │  │ ## Key Concepts          │ │
│ │                     │  │ - Direct effects         │ │
│ │                     │  │ - Indirect effects       │ │
│ └─────────────────────┘  └──────────────────────────┘ │
│                                                         │
│ [↑↓] Navigate  [/] Search  [Enter] View  [Esc] Back    │
╰─────────────────────────────────────────────────────────╯
```

**Tasks:**
- [ ] Query notes from database
- [ ] Implement search/filter
- [ ] Add note preview pane
- [ ] Show note metadata (links, tags, size)

### Phase 4.4: Graph Visualizer (Week 2, Days 1-3)

**Goal:** Visual representation of knowledge graph

**Features:**
- ASCII art graph visualization
- Show connections between notes
- Highlight orphans and hubs
- Display metrics

**Screen Design:**
```
╭─ Knowledge Graph ───────────────────────────────────────╮
│                                                         │
│         Methods ●───┬───● Applications                  │
│            │        │                                   │
│            │        └───● Theory                        │
│            │                                            │
│         Papers ●────────● Projects                      │
│            │                                            │
│            └────────────● Statistics                    │
│                                                         │
│ Metrics:                                                │
│  • Total Notes: 1,247                                   │
│  • Total Links: 2,891                                   │
│  • Orphans: 23 (1.8%)                                   │
│  • Hubs: 12 (PageRank > 0.05)                          │
│  • Avg Connections: 4.6                                 │
│                                                         │
│ [↑↓←→] Navigate  [Z] Zoom  [H] Hubs  [O] Orphans       │
╰─────────────────────────────────────────────────────────╯
```

**Tasks:**
- [ ] Generate ASCII graph from NetworkX
- [ ] Implement zoom/pan
- [ ] Highlight special nodes (orphans, hubs)
- [ ] Show interactive tooltips

### Phase 4.5: Statistics Dashboard (Week 2, Days 4-5)

**Goal:** Visual analytics and insights

**Features:**
- Vault-level statistics
- Tag analytics
- Link distribution
- Growth over time

**Screen Design:**
```
╭─ Statistics Dashboard ──────────────────────────────────╮
│                                                         │
│ Vault: Research Lab                                     │
│                                                         │
│ ┌─ Overview ───────────┐  ┌─ Top Tags ──────────────┐ │
│ │ Notes:        1,247  │  │ #research        156    │ │
│ │ Links:        2,891  │  │ #statistics       89    │ │
│ │ Tags:           234  │  │ #mediation        67    │ │
│ │ Orphans:         23  │  │ #causal           45    │ │
│ │ Hubs:            12  │  │ #methods          34    │ │
│ └──────────────────────┘  └─────────────────────────┘ │
│                                                         │
│ ┌─ Link Distribution ─────────────────────────────────┐│
│ │ 0-2 links:   ████████░░░░░░░░░░  234 notes (18.7%) ││
│ │ 3-5 links:   ████████████████░░  456 notes (36.6%) ││
│ │ 6-10 links:  ██████████░░░░░░░░  345 notes (27.7%) ││
│ │ 11+ links:   ████████░░░░░░░░░░  212 notes (17.0%) ││
│ └──────────────────────────────────────────────────────┘│
│                                                         │
│ [Tab] Switch View  [E] Export  [R] Refresh  [Q] Quit   │
╰─────────────────────────────────────────────────────────╯
```

**Tasks:**
- [ ] Query statistics from database
- [ ] Create bar charts with rich
- [ ] Show distributions
- [ ] Add export to CSV

### Phase 4.6: Polish & Integration (Week 2, Days 6-7)

**Goal:** Professional finish and CLI integration

**Features:**
- Help system
- Error handling
- Loading states
- Smooth transitions
- CLI integration

**Tasks:**
- [ ] Add help modal (? key)
- [ ] Loading spinners for DB queries
- [ ] Error messages (database not found, etc.)
- [ ] Keyboard shortcuts reference
- [ ] Integrate with `obs` command

---

## 🎨 UI/UX Design Principles

### ADHD-Friendly Design

1. **Visual Hierarchy**
   - Clear boxes and borders
   - Color coding (errors=red, success=green, info=blue)
   - Emojis for quick recognition
   - Consistent spacing

2. **Navigation**
   - Always show available actions
   - Multiple input methods (arrows, vim keys, mouse)
   - Breadcrumb trail
   - Easy escape (Esc always goes back)

3. **Information Density**
   - Not too much on one screen
   - Progressive disclosure
   - Collapsible sections
   - Focus on one task at a time

4. **Responsiveness**
   - Instant feedback
   - Loading indicators
   - Smooth transitions
   - No mysterious pauses

### Color Scheme

```python
# Using Textual's built-in colors
PRIMARY = "cyan"      # Headers, selected items
SECONDARY = "blue"    # Info, metadata
SUCCESS = "green"     # Confirmations, positive metrics
WARNING = "yellow"    # Cautions
ERROR = "red"         # Errors, destructive actions
MUTED = "dim"         # Secondary text
```

---

## 🧪 Testing Strategy

### Manual Testing
- [ ] Launch TUI and verify all screens load
- [ ] Navigate with keyboard
- [ ] Test with empty database
- [ ] Test with large vault (1000+ notes)
- [ ] Test all keyboard shortcuts

### Automated Testing
- [ ] Unit tests for widgets
- [ ] Screen navigation tests
- [ ] Database query tests
- [ ] Error handling tests

---

## 📚 Dependencies

### Already Installed
- ✅ `textual>=0.47.0` (in requirements.txt)
- ✅ `rich>=13.7.0` (in requirements.txt)
- ✅ `networkx>=3.2` (in requirements.txt)

### May Need to Add
- `textual-dev` - Development tools for Textual
- `textual-plotext` - Plotting extension (if we want charts)

---

## 🚀 Launch Commands

```bash
# Main TUI
obs tui

# Direct to specific screen
obs tui --screen vaults
obs tui --screen notes --vault-id 1
obs tui --screen graph --vault-id 1
obs tui --screen stats --vault-id 1

# With options
obs tui --theme dark    # Dark/light theme
obs tui --mouse         # Enable mouse support
obs tui --help          # Show TUI help
```

---

## 🎯 Success Criteria

**Phase 4 is complete when:**
- [x] TUI launches without errors
- [ ] Can browse all vaults
- [ ] Can view all notes in a vault
- [ ] Can search/filter notes
- [ ] Can view note content
- [ ] Can see graph visualization
- [ ] Can view statistics
- [ ] All keyboard navigation works
- [ ] Help system is accessible
- [ ] Error handling is robust

---

## 🔮 Future Enhancements (Post-Phase 4)

**After Phase 3 (AI Features) is done:**
- AI similarity results viewer
- Duplicate detection interface
- Topic cluster visualization
- Merge suggestion reviewer with preview
- Interactive undo/redo

**Advanced Features:**
- Graph editing (add/remove links)
- Note editing within TUI
- Multi-vault comparison
- Export visualizations as images
- Theme customization

---

## 📊 Timeline

```
Week 1:
  Day 1-2: Foundation & home screen
  Day 3-4: Vault browser
  Day 5-7: Note explorer

Week 2:
  Day 1-3: Graph visualizer
  Day 4-5: Statistics dashboard
  Day 6-7: Polish & integration

Total: 2 weeks
```

---

## 🎓 Learning Resources

**Textual Framework:**
- Official Docs: https://textual.textualize.io/
- Tutorial: https://textual.textualize.io/tutorial/
- Widget Gallery: https://textual.textualize.io/widget_gallery/
- Examples: https://github.com/Textualize/textual/tree/main/examples

**Inspiration:**
- `lazygit` - Git TUI
- `k9s` - Kubernetes TUI
- `htop` - Process monitor
- `ranger` - File manager TUI

---

**Next Step:** Begin Phase 4.1 - Create TUI foundation
