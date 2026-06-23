# Ideas & Future Features

> **Brainstorming space for enhancements, improvements, and new features**
>
> **Last Updated:** 2026-06-22
>
> **Current Release:** v4.0.0 (Released 2026-06-22) — nexus-cli absorption (Phase 1) + MCP vault-resolution fix + release-check harness
>
> **Strategic Direction:** "Brain + Hands" — obs analyzes/suggests (graph + AI + temporal), official Obsidian CLI executes (CRUD, move, create)
> **Install:** `brew install data-wise/tap/obsidian-cli-ops`

---

## ✅ v4.0.0 — Shipped (2026-06-22)

- ✅ nexus-cli absorption Phase 1: `obs config` (5 subcommands) + `obs research` (11 subcommands — bibliography, courses, manuscript, pdf, zotero)
- ✅ MCP vault-resolution fix: 9 tools now route through `_resolve_vault()` (name → ID → prefix); `rescan_vault` now does a real in-process scan
- ✅ `obs doctor` crash fixed (`last_scan` → `last_scanned`); new `mcp-tool-resolvers` AST check
- ✅ Release-check harness (PR #50): `core/doc_counts.py` + `validate-counts.sh` + `obs doctor --layer docs` + `verify-caveats.sh` + `post-install-check.sh` + `post-release-sweep.sh`
- ✅ `obs ai tag-suggest --apply` IS real (write path at `features_vault.py:354 _apply_tag_to_frontmatter()`) — stale "inert" claim corrected

---

## 🎯 v4.1.0 — Vault CRUD Bridge (In Planning)

> **Decided 2026-06-22.** Spec: `docs/specs/SPEC-next-overhaul-2026-06-22.md` (§1 resolved → delegate, not FS-direct build)
> **Context:** Official Obsidian CLI (~115 commands) owns vault primitives (CRUD, search, tags, backlinks, orphans, daily notes). v4.1 routes vault CRUD to it as obs's "hands" — `obs` keeps the analysis/intelligence moat.

### Theme A — Integration Bridge (delegate to official CLI)

- [ ] **`obs bridge status`** — detect official `obsidian` CLI + running app, report capabilities/version
- [ ] **`obs apply <plan-file> [--execute]`** — execute approved refactor/tag/link plans via the official CLI; dry-run default, interactive confirm
- [ ] **Vault CRUD delegation** — `read / write / daily / template / backlinks / recent / orphans` routed to official CLI. **Trade-off documented**: offline regression (CRUD requires Obsidian app running via IPC)
- [ ] **Read-side enrichment** — alias resolution + accurate backlinks from official CLI when app running; silent fallback to file scan (fixes `graph_builder.py:57` alias TODO)

### Shipped in prior releases (Themes B — Temporal Analytics)

- ✅ **`obs trends <vault>`** — knowledge-growth curve, note/link velocity, activity heatmap
- ✅ **`obs stale <vault>`** — staleness ranked by PageRank × age
- ✅ **`obs ai daily-digest <vault>`** — daily health digest (orphans, decayed hubs, stale-but-important)

**Build order:** bridge `status` → `trends`+`stale` → `apply`+real `--apply` → `daily-digest` → read-side enrichment.

---

## 🎯 Strategic Refocus (2025-12-20)

### Proposal A: Pure Obsidian Knowledge Manager
**Philosophy:** "Do one thing exceptionally well - manage Obsidian vaults"

**Core Focus:**
- Remove features NOT directly related to Obsidian vault management
- Focus on AI-assisted note operations (refactor, merge, split, tag-suggest)
- Eliminate overlap with existing dev-tools (zsh-configuration, aiterm)
- Simplify codebase: 11,500 → ~4,500 lines (61% reduction)

**What's Removed:**
- ❌ TUI (1,701 lines) - too much code for limited value
- ❌ R-Dev integration (500 lines) - belongs in R package ecosystem
- ❌ Sync features - use Obsidian's native sync
- ❌ Generic graph visualization - focus on actionable insights

**What's Enhanced:**
- ✅ AI-powered refactoring (`obs refactor <vault>`)
- ✅ Intelligent note operations (merge, split, quality)
- ✅ Tag and folder suggestions based on content
- ✅ Vault health monitoring (orphans, broken links, structure)

**See:** PROPOSAL-REFOCUS-2025-12-20.md for complete details

---

## 🚀 Phase 5: AI-Powered Features (Complete)

### Multi-Provider AI Architecture
**Status:** ✅ Phase 5A Complete (2025-12-16) | ✅ Phase 5B Complete (2025-12-16)

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
  obs ai duplicates <vault>
  ```

- **Topic Analysis**
  ```bash
  obs ai topics <vault>
  ```

- **Smart Merge Suggestions**
  ```bash
  obs ai suggest <vault>
  ```

- **Provider Management**
  ```bash
  obs ai setup              # Interactive setup
  obs ai status             # Show provider status
  obs ai test               # Test all providers
  ```

---

### Implementation Plan

**Phase 5A: Multi-Provider Foundation ✅ COMPLETE**
1. ✅ Create `src/python/ai/` module structure
2. ✅ Implement `router.py` (smart provider selection)
3. ✅ Add `gemini_api.py` provider (default)
4. ✅ Add `gemini_cli.py` provider
5. ✅ Add `claude_cli.py` provider
6. ✅ Add `ollama.py` provider (refactored)
7. ✅ Add `config.py` with auto_install settings
8. ✅ Add `install.py` for dependency management
9. ✅ Add pyproject.toml with optional extras
10. ✅ Wire up CLI commands (obs ai status/setup/test)
11. ✅ Add 73 tests

**Phase 5B: AI Features (✅ Complete - 2025-12-16)**
1. [x] `obs ai similar` - Find similar notes
2. [x] `obs ai analyze` - Analyze single note
3. [x] `obs ai duplicates` - Detect duplicates
4. [ ] `obs ai topics` - Topic clustering (future)
5. [ ] `obs ai suggest` - Merge suggestions (future)
6. [ ] TUI integration (AI insights panel) (future)

**Current File Structure:**
```
src/python/ai/
├── __init__.py          # Module exports
├── router.py            # Smart provider selection
├── config.py            # Configuration + setup wizard
├── install.py           # Dependency management
└── providers/
    ├── __init__.py
    ├── base.py          # Abstract base class
    ├── gemini_api.py    # Default (embeddings, batch)
    ├── gemini_cli.py    # CLI fallback
    ├── claude_cli.py    # High-quality analysis
    └── ollama.py        # Local, free, private
```

---

## ✅ Phase 7: Proposal A Implementation (v3.0.0 — Complete)

**All 4 phases complete.** v3.0.0 stable released 2026-03-05.

- **Phase 7.1**: Simplification — TUI removed, R-Dev removed, CLI consolidated (14 commands)
- **Phase 7.2**: AI Enhancement — 5 providers, 3 new commands, embedding cache, 125 tests
- **Phase 7.3**: Vault Health & Polish — `obs health`, `--json` on all commands, 183 tests
- **Phase 7.4**: Testing & Release — version sync, CI hardening, 186 tests, Homebrew formula

**Results**: 2,331 lines removed, 186 tests, Homebrew distribution, docs site live.

## 🎯 Phase 8: Future AI Features (Not Started)

### High-Value New Commands

1. **`obs refactor <vault>`** - AI-powered vault reorganization
   - Analyze entire vault structure, suggest folder reorganization
   - Propose note consolidations, interactive approval workflow

2. **`obs tag-suggest <note|vault>`** - Intelligent tag suggestions
   - Analyze note content with AI, suggest relevant tags
   - Show tag co-occurrence patterns, batch apply

3. **`obs quality <note|vault>`** - Note quality assessment
   - Check completeness, identify missing backlinks
   - Quality score with explanations

4. **`obs merge-suggest <vault>`** - Find merge candidates
   - Identify duplicate or highly similar notes
   - Preview merged content, interactive merge workflow

---

## 🔮 Future: Proposal D Features (v3.1+ - Deferred)

**Note:** These features from Proposal D (Hub Integration) are deferred to future releases. Proposal A focuses on pure Obsidian management first.

### Hub Integration (Future v3.1.0)
- [ ] **`obs hub sync`** - Bi-directional sync with project-hub
  - Sync .STATUS files to Obsidian dashboard note
  - Extract action items from weekly notes
  - Update project-hub from Obsidian TODOs

- [ ] **`obs hub export <project>`** - Export project notes to hub
  - Generate .STATUS from project notes
  - Extract deadlines and milestones
  - Create project summary

- [ ] **`obs hub import <vault>`** - Import hub data to vault
  - Create dashboard note from all .STATUS files
  - Import project tasks as Obsidian tasks
  - Link notes to project-hub projects

**Estimated Effort:** 8-12 hours (future release)

### Cross-Vault Operations (Future v3.2.0)
- [ ] **`obs global-search <query>`** - Search across all vaults
- [ ] **`obs cross-link <vault1> <vault2>`** - Find related notes across vaults
- [ ] **`obs cross-merge <vault1> <vault2>`** - Merge similar cross-vault notes

**Estimated Effort:** 6-8 hours (future release)

### Advanced AI Features (Future v3.4.0)

> `daily-digest` promoted into v3.3.0 (see top). Batch ops below become trivial once v3.3.0's `obs apply` write-path lands — they're just `apply` over an auto-generated plan.

- [ ] **`obs ai batch-tag <vault>`** - Batch tag all untagged notes (needs v3.3.0 bridge write-path)
- [ ] **`obs ai batch-link <vault>`** - Add missing backlinks automatically (needs v3.3.0 bridge write-path)
- [ ] **`obs watch <vault>`** - Real-time improvement suggestions (daemon; heavy — defer)

**Estimated Effort:** 8-12 hours (after v3.3.0 bridge ships)

**See:** [docs/planning/IMPLEMENTATION-ROADMAP.md](docs/planning/IMPLEMENTATION-ROADMAP.md) (archived) and PROPOSAL-REFOCUS-2025-12-20.md for complete details

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

## 🎨 TUI (Removed in v3.0.0)

> TUI was removed in Phase 7.1 to focus on CLI-first design.
> If demand warrants it, a future TUI could be re-added as a thin presentation layer over the existing Core.

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

> ⚠️ **Dropped 2026-06-04:** plain/fuzzy/regex/full-text search now belongs to the **official Obsidian CLI** (`search`, `search:context`). Reimplementing them would duplicate native functionality (🔴 avoid zone). Delegate instead. Only graph-native discovery — which the official CLI cannot do — stays on the backlog:

- [ ] Search **within the graph** (find shortest paths between two notes) — graph-native, no overlap
- [ ] ~~Full-text / fuzzy / regex search~~ → use official `obsidian search`

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

- **[.STATUS](.STATUS)** - Current state, next steps, and metrics (live)
- **[docs/planning/TODOS.md](docs/planning/TODOS.md)** - ⚠️ archived (historical, pre-v3.1)
- **[CLAUDE.md](CLAUDE.md)** - Developer guide
- **[docs/planning/project-hub.md](docs/planning/project-hub.md)** - Control center

---

**Remember:** Ideas are cheap, execution is everything. Focus on completing current work (see [.STATUS](.STATUS)) before starting new features! 🚀
