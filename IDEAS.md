# Ideas & Future Features

> **Brainstorming space for enhancements, improvements, and new features**
>
> **Last Updated:** 2025-12-15

---

## 🚀 Phase 5: AI-Powered Features (Future)

### Multi-Provider AI Architecture
**Status:** Planned (brainstorm complete 2025-12-16)

#### Provider Stack (6 providers)

```
TIER 1: Cloud APIs (Fast, Batch, Embeddings)
└── Gemini API ← Default (free tier: 1000 RPD)

TIER 2: CLI Tools (Simple, Use Existing Subscriptions)
├── Gemini CLI (npm: @google/gemini-cli)
├── Claude CLI (Claude Code)
└── Qwen CLI (optional)

TIER 3: Local (Free, Private, Offline)
├── Ollama (easy setup)
└── llama.cpp (lightweight, 90MB)
```

#### Provider Capabilities

| Provider | Embeddings | Analysis | Batch | Cost |
|----------|------------|----------|-------|------|
| gemini-api | ✅ | ✅ | ✅ | Free tier |
| gemini-cli | ❌ | ✅ | ❌ | Free |
| claude-cli | ❌ | ✅ | ❌ | Subscription |
| qwen-cli | ❌ | ✅ | ❌ | Free |
| ollama | ✅ | ✅ | ⚠️ | Free (local) |
| llama-cpp | ✅ | ✅ | ⚠️ | Free (local) |

#### Smart Routing

```python
# Embeddings → API or Local (CLIs don't support)
# Batch ops → API (parallel processing)
# Single analysis → CLI (saves API quota)
# Complex reasoning → Claude CLI or Gemini API
```

#### Config Structure

```json
{
  "default_provider": "gemini-api",
  "fallback_chain": ["gemini-cli", "ollama"],
  "providers": {
    "gemini-api": { "model": "gemini-2.5-flash" },
    "gemini-cli": { "enabled": true },
    "claude-cli": { "enabled": true },
    "ollama": { "url": "http://localhost:11434" }
  }
}
```

---

### AI Features (Using Multi-Provider)

- **Find Similar Notes**
  ```bash
  obs ai similar <note_id>
  obs ai similar <note_id> --provider claude-cli
  ```

- **Duplicate Detection**
  ```bash
  obs ai duplicates <vault_id>
  ```

- **Topic Analysis**
  ```bash
  obs ai topics <vault_id>
  ```

- **Smart Merge Suggestions**
  ```bash
  obs ai suggest <vault_id>
  ```

- **Provider Management**
  ```bash
  obs ai setup              # Interactive setup
  obs ai status             # Show provider status
  obs ai test               # Test all providers
  ```

---

### Implementation Plan

**Phase 5A: Multi-Provider Foundation**
1. Create `src/python/ai/` module structure
2. Implement `router.py` (smart provider selection)
3. Add `gemini_cli.py` provider
4. Add `claude_cli.py` provider
5. Add `qwen_cli.py` provider (optional)
6. Add `llama_cpp.py` provider
7. Update setup wizard
8. Add `obs ai status` command

**Phase 5B: AI Features**
1. `obs ai similar` - Find similar notes
2. `obs ai duplicates` - Detect duplicates
3. `obs ai topics` - Topic clustering
4. `obs ai suggest` - Merge suggestions
5. TUI integration (AI insights panel)

**File Structure:**
```
src/python/ai/
├── __init__.py
├── router.py
├── config.py
├── providers/
│   ├── base.py
│   ├── gemini_api.py
│   ├── gemini_cli.py
│   ├── claude_cli.py
│   ├── qwen_cli.py
│   ├── ollama.py
│   └── llama_cpp.py
└── embeddings.py
```

---

## 🧠 Phase 6: Learning System (Future)

### Adaptive Intelligence
**Status:** Planned (requires Phase 5 first)

- **User Feedback Collection**
  - Accept/reject suggestions
  - Provide reasoning for corrections
  - Build preference database

- **Rule Generation**
  - Learn from user corrections
  - Generate custom rules automatically
  - Export/import preference files

- **Confidence Adaptation**
  - Increase confidence for accepted patterns
  - Decrease for rejected suggestions
  - Tune thresholds per user

- **Interactive Tuning**
  ```bash
  obs learn stats     # What system has learned
  obs learn tune      # Interactive tuning interface
  obs learn export    # Export rules for backup/sharing
  obs learn import    # Import rules from file
  ```

**Success Criteria:**
- +15% accuracy improvement after 100 interactions
- User-specific rules that work consistently
- Explainable suggestions (show reasoning)

---

## 🎨 TUI Enhancements

### Current State
- ✅ Interactive vault browser
- ✅ Note explorer with search
- ✅ ASCII graph visualization
- ✅ Statistics dashboard
- ✅ Vim-style navigation

### Future Ideas

**Visual Improvements:**
- [ ] Color themes (dark/light/custom)
- [ ] Graph layout options (force-directed, hierarchical, radial)
- [ ] Minimap for large graphs
- [ ] Split-pane view (graph + notes)
- [ ] Preview pane for note content

**Interaction Improvements:**
- [ ] Mouse support (click nodes, drag to pan)
- [ ] Zoom in/out on graphs
- [ ] Filter by tag/folder
- [ ] Multi-select for batch operations
- [ ] Command palette (Ctrl+P)

**New Screens:**
- [ ] Tag explorer (browse by tags)
- [ ] Timeline view (notes by date)
- [ ] Cluster navigator (explore communities)
- [ ] Link browser (see all connections)
- [ ] Search results view

---

## 📊 Analytics & Insights

### Knowledge Graph Metrics

**Currently Implemented:**
- ✅ PageRank
- ✅ Centrality measures
- ✅ Clustering coefficient
- ✅ Hub/orphan detection

**Future Metrics:**
- [ ] **Temporal Analysis**
  - Note creation patterns over time
  - Link formation velocity
  - Knowledge growth rate
  - Activity heatmaps

- [ ] **Structural Analysis**
  - Community detection (Louvain, Leiden)
  - Betweenness centrality
  - Eigenvector centrality
  - Bridge nodes detection

- [ ] **Content Analysis**
  - Word count distribution
  - Tag co-occurrence patterns
  - Folder usage statistics
  - Backlink analysis

- [ ] **Health Metrics**
  - Broken link ratio
  - Orphan percentage
  - Average note connections
  - Graph density trends

---

## 🔄 Automation & Workflows

### Auto-Categorization
- Watch mode for new notes
- Auto-suggest folder based on content
- Auto-tag based on similarity
- Auto-link to related notes

### Batch Operations
- Bulk rename notes
- Batch tag updates
- Mass link creation
- Folder reorganization

### Integration Ideas
- **Zotero** - Sync citations and references
- **Emacs** - Org-mode integration
- **R Studio** - Enhanced R-Dev features
- **VS Code** - Extension for quick access
- **Alfred/Raycast** - Quick vault switching

---

## 🧪 Testing & Quality

### Sandbox Testing (Partially Implemented)

**✅ Completed (2025-12-15):**
- Synthetic vault generator (`generate_test_vault.py`)
- Quick reference guide
- Test vault templates (small/medium/large)

**Future Improvements:**
- [ ] Automated test suite using fixtures
- [ ] CI/CD integration with test vaults
- [ ] Performance benchmarking suite
- [ ] Stress testing (50k+ notes)
- [ ] Edge case test scenarios

### Test Vault Library
- [ ] Empty vault (new user scenario)
- [ ] Minimal vault (10 notes, basic links)
- [ ] Realistic vault (1k notes, real structure)
- [ ] Stress vault (10k+ notes, complex graph)
- [ ] Edge case vault (broken links, orphans, weird characters)

---

## 🆕 New Features (Brainstorming)

### Export & Sharing
- [ ] Export vault graph to GraphML/DOT
- [ ] Generate static HTML vault visualization
- [ ] Share statistics as infographics
- [ ] Export note clusters as separate vaults

### Search & Discovery
- [ ] Full-text search across all vaults
- [ ] Fuzzy search (typo-tolerant)
- [ ] Regex search support
- [ ] Saved search queries
- [ ] Search within graph (find paths between notes)

### Collaboration Features
- [ ] Compare vaults (diff tool)
- [ ] Merge vaults intelligently
- [ ] Sync specific folders between vaults
- [ ] Shared knowledge base tracking

### Plugin Ecosystem
- [ ] Plugin API for extensions
- [ ] Custom analyzers
- [ ] Custom visualizations
- [ ] Third-party integrations

---

## 🔧 Improvements

### Performance Optimizations
- [ ] Incremental scanning (only changed files)
- [ ] Caching layer for graph queries
- [ ] Parallel processing for large vaults
- [ ] Database query optimization
- [ ] Lazy loading in TUI

### Error Handling
- [ ] Better error messages with recovery suggestions
- [ ] Graceful degradation when features unavailable
- [ ] Detailed logging with levels
- [ ] Error reporting with diagnostics

### Configuration
- [ ] Per-vault settings
- [ ] Global configuration file
- [ ] Environment variable support
- [ ] Configuration validation
- [ ] Interactive config wizard

---

## 🐛 Known Issues & Wishlist

### Edge Cases to Handle
- [ ] Very long note titles (>255 chars)
- [ ] Special characters in filenames
- [ ] Circular links (A → B → C → A)
- [ ] Case-sensitive vs case-insensitive filesystems
- [ ] Unicode in wikilinks

### Platform Support
- [ ] Windows compatibility testing
- [ ] Linux compatibility testing
- [ ] WSL (Windows Subsystem for Linux) support
- [ ] Docker container version

---

## 🤔 To Explore

### Research Topics
- [ ] **Graph Neural Networks** - Could GNNs improve link prediction?
- [ ] **Knowledge Graph Embedding** - Better note similarity via embeddings
- [ ] **Community Detection** - Advanced clustering algorithms
- [ ] **Temporal Graph Analysis** - How knowledge evolves over time
- [ ] **Natural Language Processing** - Extract entities, relationships

### Tools & Libraries
- [ ] **Neo4j** - Graph database for complex queries?
- [ ] **Cytoscape** - Better graph visualization?
- [ ] **D3.js** - Interactive web visualizations?
- [ ] **NetworkX** - More graph algorithms (currently using)
- [ ] **spaCy** - NLP for content analysis?

### Design Patterns
- [ ] Event-driven architecture for watch mode
- [ ] Plugin system design
- [ ] Caching strategies
- [ ] Multi-threading for scanning

---

## 💡 Community Ideas

> **Got an idea?** Add it here or create an issue on GitHub!

**How to contribute ideas:**
1. Add to appropriate section above
2. Describe the problem it solves
3. Sketch out how it might work
4. Tag with priority (nice-to-have, must-have, game-changer)

**Discussion:**
- GitHub Discussions: https://github.com/Data-Wise/obsidian-cli-ops/discussions
- GitHub Issues: https://github.com/Data-Wise/obsidian-cli-ops/issues

---

## 🎯 Prioritization Framework

**When evaluating new ideas:**

1. **Impact** - How many users benefit?
2. **Effort** - How long to implement?
3. **Alignment** - Fits project vision?
4. **Dependencies** - Requires other features?
5. **Maintenance** - Ongoing cost?

**Priority Levels:**
- 🔴 **Game Changer** - Core to vision, high impact
- 🟡 **High Value** - Significant improvement, reasonable effort
- 🟢 **Nice to Have** - Useful but not critical
- ⚪ **Low Priority** - Cool idea but low impact or high effort

---

## 📚 Appendix: Research & Architecture

### CLI/GUI Application Best Practices

**Date:** 2025-12-15
**Status:** ✅ Research completed and implemented
**Implementation:** Three-layer architecture is production ready

This research informed our three-layer architecture design. Key findings:

#### Architecture Pattern: Three-Layer Design ✅ IMPLEMENTED

```
Presentation Layer (CLI/TUI/GUI)
        ↓
Application Layer (Core Logic)
        ↓
Data Layer (Database/Files)
```

**What We Built:**
- **Presentation**: `obs.zsh` (CLI), `tui/` (TUI) - 2,019 lines
- **Application**: `core/` (VaultManager, GraphAnalyzer, Models) - 859 lines
- **Data**: `db_manager.py`, `vault_scanner.py`, `graph_builder.py` - 1,149 lines

**Key Achievement:** CLI and TUI share 100% of business logic with zero duplication.

#### Why This Matters

**Before (2025-12-10):**
```
ZSH CLI → Python CLI → Database
```
- Business logic mixed with presentation
- Hard to add TUI
- Would require duplicating code

**After (2025-12-14):**
```
ZSH CLI ──┐
Python CLI├──> Core Layer → Data Layer
TUI ──────┘
```
- Business logic in Core only
- CLI and TUI both use same VaultManager
- Adding GUI just means new presentation layer

**Future Ready:**
```
ZSH CLI ──┐
Python CLI│
TUI ──────├──> Core Layer → Data Layer
GUI ──────┘  (Just add new presentation layer)
Web API ───┘
```

#### Technology Choices Evaluated

**For GUI (If Needed in Future):**
- **Winner:** PySide6 (Qt for Python)
- **Reason:** Professional look, graph visualization support, LGPL license
- **Status:** Not needed yet (TUI is sufficient)

**For TUI (Current):**
- **Winner:** Textual ✅ IMPLEMENTED
- **Reason:** Python-native, rich widgets, vim-friendly
- **Status:** Production ready

#### Patterns Used

**✅ Repository Pattern** - Data layer abstracts database
**✅ Domain Models** - Vault, Note, ScanResult, GraphMetrics
**✅ Command Pattern** - VaultManager methods are commands
**✅ Master-Detail UI** - TUI vault browser uses this
**✅ Three-Panel Layout** - Graph visualizer uses this

#### Real-World Examples Studied

1. **Git Ecosystem**
   - Core: libgit2 (library)
   - CLI: git command
   - GUIs: GitKraken, GitHub Desktop
   - **Lesson:** Core library enables multiple frontends

2. **Docker Ecosystem**
   - Backend: Docker daemon (REST API)
   - CLI: docker command
   - GUI: Docker Desktop
   - **Lesson:** API-first design

3. **Jupyter**
   - Backend: Jupyter server
   - Frontends: JupyterLab, notebooks, VS Code
   - **Lesson:** Protocol-based communication

#### Best Practices Applied

**CLI Design:**
- ✅ Composable with Unix tools (`obs list --json | jq`)
- ✅ Machine-readable output (JSON)
- ✅ Progressive disclosure (simple → complex)
- ✅ Standard conventions (verb-noun structure)

**Architecture:**
- ✅ Business logic is interface-agnostic
- ✅ Domain models for data transfer
- ✅ Clear layer separation
- ✅ Unit tests for core layer (70% coverage)

**Graph Visualization:**
- ✅ Force-directed layout (NetworkX + ASCII)
- ✅ Node sizing by PageRank
- ✅ Hub/orphan highlighting
- 📋 Future: Interactive Qt-based visualization

#### Metrics

**Code Distribution:**
- Presentation: 2,019 lines (CLI 318 + TUI 1,701)
- Application: 859 lines (Core business logic)
- Data: 1,149 lines (Database, scanning, parsing)

**Achievement:**
- Completed Phase 1 & 2 in 4 days (estimated 2-3 weeks)
- Zero code duplication between CLI and TUI
- Ready for GUI without core changes

#### Future GUI Considerations

**When to build:**
- User demand (survey needed)
- GUI-specific features identified
- TUI limitations reached

**What to build:**
- Master-detail vault browser
- Interactive graph with zoom/pan
- Visual diff and merge tools
- Settings configuration UI

**How to build:**
1. Install PySide6
2. Create `gui/` directory
3. Import VaultManager from core
4. Build Qt widgets
5. No changes to core layer needed!

#### Quick Reference

**Architecture Checklist:**
- ✅ Separate presentation, application, data
- ✅ Business logic is interface-agnostic
- ✅ Use domain models
- ✅ Repository pattern for data
- ✅ Command pattern for operations
- ✅ Unit test core layer

**CLI Checklist:**
- ✅ Use argparse
- ✅ Support --json
- ✅ Use rich for output
- ✅ Follow verb-noun structure
- ✅ Add --verbose flag
- ✅ Clear error messages
- ✅ Correct exit codes

**GUI Checklist (Future):**
- [ ] Use layouts, not fixed positions
- [ ] Support window resizing
- [ ] Save/restore window state
- [ ] Master-detail pattern
- [ ] Debounce search input
- [ ] Loading indicators
- [ ] Error dialogs
- [ ] Keyboard shortcuts

#### Documentation

**Full Research:** See `docs/developer/research/cli-gui-practices.md` (comprehensive guide)
**Architecture:** See `docs/developer/architecture.md` (890 lines)
**CLAUDE.md:** Quick developer reference with three-layer design

---

## 🔗 Related Files

- **[TODOS.md](TODOS.md)** - Current active work items
- **[.STATUS](.STATUS)** - Project status and metrics
- **[CLAUDE.md](CLAUDE.md)** - Developer guide
- **[docs/planning/project-hub.md](docs/planning/project-hub.md)** - Control center

---

**Remember:** Ideas are cheap, execution is everything. Focus on completing current work (see TODOS.md) before starting new features! 🚀
