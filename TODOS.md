# Current TODOs

> **Active work items and immediate next steps**
>
> **Last Updated:** 2026-03-04
> **Status:** v3.0.0-beta.2 | Phase 7.4 In Progress
> **Strategic Direction:** Proposal A - Pure Obsidian Knowledge Manager

---

## 🎯 High Priority (Do Next)

### Phase 7.4: Testing & Release Prep (In Progress)
- [x] **Inc 1: Version sync & stale cleanup** ✅
  - Sync all version strings to 3.0.0-beta.2
  - Remove stale TUI dep, fix Gemini SDK to google-genai>=1.0.0
  - Add anthropic optional dep
  - Consolidate pytest config (pytest.ini → pyproject.toml)
  - Extend version consistency tests (186 tests)
- [ ] **Inc 2: Release validation**
  - Full test suite verification (186+ tests)
  - CI pipeline green
  - docs sync + mkdocs build
  - PR to dev then main for v3.0.0-beta.2 release

---

## 🟡 Medium Priority (Soon)

### Documentation
- [x] Organize docs/ structure (user/developer/planning/releases)
- [x] Update all documentation to v3.0.0
- [x] Optimize CLAUDE.md for developers
- [x] Consolidate planning docs into IDEAS.md and TODOS.md
- [ ] Update MkDocs site with v3.0.0 content and tutorials

### Testing & Quality
- [ ] **Increase test coverage** to 80%
  - Current: ~70% overall
  - Core layer: 85% (good)
  - Database layer: 75% (needs work)
- [ ] **Performance testing**
  - Test with large vaults (10k+ notes)
  - Memory profiling
  - Query optimization
- [ ] **Error handling improvements**
  - Better error messages
  - Graceful degradation
  - Recovery suggestions

### Features
- [ ] **Search improvements** - Fuzzy search, regex support
- [ ] **Export functionality** - Export stats to JSON/CSV

---

## 🟢 Low Priority (Future)

### CLI Enhancements
- [ ] `obs config` command - Manage configuration interactively
- [ ] `obs init` - Interactive setup wizard

### AI Features (Phase 5 - Future Enhancements)
- [x] Find similar notes - `obs ai similar <note_id>` ✅ v2.2.0
- [x] Detect duplicates - `obs ai duplicates <vault>` ✅ v2.2.0
- [x] Analyze notes - `obs ai analyze <note_id>` ✅ v2.2.0
- [ ] Topic analysis - `obs ai topics <vault>`
- [ ] Merge suggestions - `obs ai suggest <vault>`

### Learning System (Phase 6 - Deferred)
- [ ] User feedback collection
- [ ] Rule generation from corrections
- [ ] Confidence adaptation
- [ ] Interactive tuning interface

---

## ✅ Recently Completed

### 2026-03 (Phase 7.4 Inc 1)
- [x] **Version sync to 3.0.0-beta.2** — pyproject.toml, package.json, __init__.py
- [x] **Removed stale TUI dep** — textual dependency, tui optional extra
- [x] **Fixed Gemini SDK** — google-generativeai → google-genai>=1.0.0
- [x] **Added anthropic optional dep** — anthropic>=0.40.0
- [x] **Consolidated pytest config** — merged pytest.ini → pyproject.toml, deleted pytest.ini
- [x] **Extended version consistency tests** — 186 tests total

### 2026-01 (Phase 7.3 Complete)
- [x] **Phase 7.3: Testing & Polish** ✅
  - Scanner integration tests (7 tests)
  - Vault fixture with .obsidian marker
  - 183 tests total passing
  - Version consistency tests (3 tests)

### 2026-01 (Phase 7.2 Complete)
- [x] **Phase 7.2: AI Architecture** ✅
  - 5-provider AI system (gemini-api, anthropic-api, ollama, gemini-cli, claude-cli)
  - Shared models (AnalysisResult, ComparisonResult, SimilarNote)
  - Embedding cache with mtime invalidation
  - 13 AI CLI commands
  - Retry decorator on all API methods

### 2025-12 (Phase 7.1 Complete)
- [x] **Phase 7.1: Simplification** ✅
  - Removed TUI (1,701 lines)
  - Removed R-Dev integration (307 lines)
  - Simplified CLI: 14 focused commands
  - v3.0.0-beta released

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
