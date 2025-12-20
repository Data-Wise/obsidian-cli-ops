# Current TODOs

> **Active work items and immediate next steps**
>
> **Last Updated:** 2025-12-20
> **Status:** 99% Complete | v2.2.0 Released

---

## 🎯 High Priority (Do Next)

### v2.2.1 Test Quality Release (or v2.3)
- [ ] **Fix test_note_explorer.py** - Convert mock data to Note domain objects (27 failures) [60-90 min]
- [ ] **Fix test_graph_visualizer.py** - Update mock method calls (14 failures) [30-45 min]
- [ ] **Fix remaining test failures** - vault_scanner (6), quick_wins (5), ai_client (1) [30 min]
- [ ] **Target:** 440+/461 tests passing (95%+)
- [ ] **Create v2.2.1 release** - Test quality improvements only

**OR** skip to Phase 6:
- [ ] **Start v2.3 Learning System** - User feedback collection and rule generation

### Documentation
- [x] Organize docs/ structure (user/developer/planning/releases)
- [x] Update all documentation to v2.1-beta
- [x] Create TUI navigation guides (tutorial, reference, cheat sheet)
- [x] Optimize CLAUDE.md for developers
- [x] Consolidate planning docs into IDEAS.md and TODOS.md

---

## 🟡 Medium Priority (Soon)

### Testing & Quality
- [ ] **Increase test coverage** to 80%
  - Current: 70% overall
  - Core layer: 85% (good)
  - Database layer: 75% (needs work)
  - TUI layer: Need more tests
- [ ] **Performance testing**
  - Test with large vaults (10k+ notes)
  - Memory profiling
  - Query optimization
- [ ] **Error handling improvements**
  - Better error messages
  - Graceful degradation
  - Recovery suggestions

### Features
- [ ] **Keyboard shortcut generator** - Auto-generate from BINDINGS
- [ ] **TUI help screen improvements** - Context-sensitive help
- [ ] **Search improvements** - Fuzzy search, regex support
- [ ] **Export functionality** - Export stats to JSON/CSV

---

## 🟢 Low Priority (Future)

### v1.x Maintenance
- [ ] `obs config` command - Manage configuration interactively
- [ ] `obs r-dev list` - Show all R project mappings in table
- [ ] Plugin update checker - `obs install --update`
- [ ] `obs init` - Interactive setup wizard

### AI Features (Phase 5 - Future Enhancements)
- [x] Find similar notes - `obs ai similar <note_id>` ✅ v2.2.0
- [x] Detect duplicates - `obs ai duplicates <vault_id>` ✅ v2.2.0
- [x] Analyze notes - `obs ai analyze <note_id>` ✅ v2.2.0
- [ ] Topic analysis - `obs ai topics <vault_id>`
- [ ] Merge suggestions - `obs ai suggest <vault_id>`

### Learning System (Phase 6 - Deferred)
- [ ] User feedback collection
- [ ] Rule generation from corrections
- [ ] Confidence adaptation
- [ ] Interactive tuning interface

---

## ✅ Recently Completed

### 2025-12-20
- [x] **v2.2.0 Release**
  - Verified GitHub Pages deployment (navigation, badges, features all correct)
  - Created annotated git tag `v2.2.0` with comprehensive release notes
  - Pushed tag to GitHub: https://github.com/Data-Wise/obsidian-cli-ops/releases/tag/v2.2.0
  - Updated .STATUS, IDEAS.md, TODOS.md

### 2025-12-17
- [x] **Documentation Quality Improvements**
  - Fixed version mismatch (v2.1.0 → v2.2.0)
  - Added 9 orphan pages to MkDocs navigation
  - Added 5 badges to README
  - Deployed to GitHub Pages

### 2025-12-16
- [x] **Phase 5: Multi-Provider AI Architecture (v2.2.0)**
  - Multi-provider support (Gemini API, Gemini CLI, Claude CLI, Ollama)
  - `obs ai similar` - Find similar notes using embeddings
  - `obs ai analyze` - Deep note analysis with topics/themes
  - `obs ai duplicates` - Detect potential duplicate notes
  - Smart routing and provider management
  - 96 AI tests passing

### 2025-12-15
- [x] Unified `obs` command with three domains (graph/open/sync)
- [x] TUI vault discovery with `d` key (iCloud default)
- [x] Fixed Python path issues in obs.zsh
- [x] Fixed TUI TypeErrors (limit parameters)
- [x] Created comprehensive TUI documentation
  - Vim tutorial for beginners
  - Quick reference guide
  - Printable cheat sheet
- [x] Organized documentation structure
- [x] Updated all docs to v2.1-beta

### Earlier December 2025
- [x] Phase 4: TUI/Visualization (100%)
  - Interactive vault browser
  - Note explorer with search
  - ASCII graph visualization
  - Statistics dashboard
  - Vim-style navigation
- [x] Phase 2: AI Integration (100%)
  - FREE local AI (HuggingFace + Ollama)
  - Interactive setup wizard
  - Embedding generation
  - Note similarity analysis
- [x] Phase 1: Foundation (100%)
  - SQLite database
  - Vault scanner
  - Graph builder
  - Link resolution

---

## 📋 Not Started (Backlog)

### Nice to Have
- [ ] Multi-vault operations - Work across all vaults simultaneously
- [ ] Watch mode - Auto-scan on file changes
- [ ] Integration with Zotero - Citation management
- [ ] Graph export - Export graph to formats (GraphML, DOT, etc.)
- [ ] Plugin ecosystem - Allow custom extensions

### Research Needed
- [ ] Performance at scale - Test with 50k+ notes
- [ ] Graph algorithms - Better clustering, community detection
- [ ] AI optimization - Faster embeddings, better prompts
- [ ] Cross-platform support - Windows, Linux testing

---

## 🗑️ Removed/Cancelled

- ~~Phase 3 in original plan~~ - Merged into Phase 4 (TUI)
- ~~Paid AI APIs by default~~ - Switched to 100% free local AI
- ~~Complex plugin system~~ - Keep it simple for now
- ~~Multi-language support~~ - English only for v2.x

---

## 💡 How to Use This File

**Adding TODOs:**
```bash
# Add to appropriate priority section
# Use [ ] for pending items
# Use [x] for completed items
# Move completed items to "Recently Completed"
```

**Prioritization:**
- 🎯 **High** - Do now (this week)
- 🟡 **Medium** - Do soon (this month)
- 🟢 **Low** - Do eventually (this quarter)
- 📋 **Backlog** - Nice to have (someday)

**Review Frequency:**
- High priority: Daily
- Medium priority: Weekly
- Low priority: Monthly
- Backlog: Quarterly

---

## 🔗 Related Files

- **[IDEAS.md](IDEAS.md)** - Future features and brainstorming
- **[.STATUS](.STATUS)** - Project metrics and status
- **[CLAUDE.md](CLAUDE.md)** - Developer guide
- **[docs/planning/project-hub.md](docs/planning/project-hub.md)** - ADHD-friendly control center

---

**Remember:** Focus on HIGH priority first. Don't get distracted by shiny LOW priority items! 🧠✨
