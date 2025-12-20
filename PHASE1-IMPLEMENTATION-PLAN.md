# Phase 1 Implementation Plan - Proposal D: Hybrid

**Start Date:** 2025-12-20
**Target Completion:** Week 1-2 (12-17 hours)
**Goal:** Simplify codebase by removing low-adoption features and consolidating CLI

## Overview

Phase 1 focuses on **removal and consolidation** to create a clean foundation for AI features in Phase 2.

**Code Impact:**
- **Remove:** 2,201 lines (TUI + R-Dev)
- **Consolidate:** ~1,000 lines (CLI unification)
- **Net Reduction:** ~3,200 lines (28% reduction)

## Week 1: Remove TUI (1,701 lines)

### Task 1.1: Delete TUI Files
**Effort:** 15 minutes
**Files to remove:**
```bash
rm -rf src/python/tui/
# Removes:
# - src/python/tui/app.py (282 lines)
# - src/python/tui/screens/vaults.py (267 lines)
# - src/python/tui/screens/notes.py (378 lines)
# - src/python/tui/screens/graph.py (378 lines)
# - src/python/tui/screens/stats.py (420 lines)
# - src/python/tui/styles/ (entire directory)
```

### Task 1.2: Remove TUI Dependencies
**Effort:** 10 minutes
**Update:** `src/python/requirements.txt`
```diff
- textual==0.47.1
- textual-plotext==0.2.1
```

### Task 1.3: Remove TUI Tests
**Effort:** 5 minutes
```bash
rm -f src/python/tests/test_tui_*.py
# Updates test count: 35 → ~30 tests
```

### Task 1.4: Update Documentation
**Effort:** 30 minutes
**Files to update:**
- `README.md` - Remove TUI mentions from Features, Quick Start
- `CLAUDE.md` - Remove TUI from "Essential Commands"
- `docs/user/guides/tui/` - Archive or remove directory
- `.STATUS` - Update metrics

**Total Week 1 Part A:** 1 hour

---

## Week 1: Remove R-Dev Integration (500 lines)

### Task 1.5: Delete R-Dev Files
**Effort:** 10 minutes
```bash
# Remove from obs.zsh (estimate 200 lines)
# Functions to remove:
# - obs_r-dev()
# - obs_r-dev_link()
# - obs_r-dev_log()
# - obs_r-dev_draft()
# - obs_r-dev_context()

# Remove from Python backend
rm -f src/python/r_dev_manager.py  # ~300 lines
```

### Task 1.6: Remove R-Dev Tests
**Effort:** 10 minutes
```bash
rm -f tests/test_r_dev.sh
rm -f src/python/tests/test_r_dev.py
# Updates test count: ~30 → ~28 tests
```

### Task 1.7: Update CLI Help
**Effort:** 20 minutes
**Update:** `src/obs.zsh` - Remove R-Dev from help text, command list

**Total Week 1 Part B:** 40 minutes

---

## Week 2: Consolidate CLI (Single Interface)

### Task 2.1: Merge ZSH + Python CLI
**Effort:** 3-4 hours
**Strategy:** Decide on unified CLI approach

**Option A: ZSH-First (Recommended)**
```bash
# Keep src/obs.zsh as main interface
# Move Python logic to core/ modules
# ZSH calls Python core directly via module imports
```

**Option B: Python-First**
```bash
# Make src/python/obs_cli.py the main entrypoint
# ZSH wrapper becomes minimal dispatcher
# Install as Python package with console_scripts
```

**Decision Point:** Which approach do you prefer?
- **Option A (ZSH-First):** Keeps shell integration, faster for simple commands
- **Option B (Python-First):** More portable, easier testing, standard Python packaging

### Task 2.2: Simplify Command Structure
**Effort:** 2-3 hours
**Current:** 15+ commands across multiple namespaces
**Target:** 8-10 focused commands

**Proposed Command Set:**
```bash
# Core (4 commands)
obs                    # Open last vault (Option D design)
obs switch             # Vault switcher
obs scan <vault>       # Scan/rescan vault
obs stats <vault>      # Statistics

# Graph (2 commands)
obs graph <vault>      # Graph visualization
obs orphans <vault>    # Find orphaned notes

# AI (4-5 commands) - Prepared for Phase 2
obs ai refactor        # AI-powered refactoring (Phase 2)
obs ai tags            # Tag suggestions (Phase 2)
obs ai quality         # Quality analysis (Phase 2)
obs ai merge           # Merge duplicates (Phase 2)

# Hub (2 commands) - Prepared for Phase 3
obs hub sync           # Sync with project-hub (Phase 3)
obs hub status         # Show hub integration status (Phase 3)
```

### Task 2.3: Update Tests
**Effort:** 1-2 hours
- Remove TUI/R-Dev tests (already done in 1.3, 1.6)
- Update CLI integration tests for new command structure
- Ensure core layer tests still pass (35 tests)
- Target: Maintain 95%+ pass rate

### Task 2.4: Update Documentation
**Effort:** 2 hours
**Files to update:**
- `README.md` - New command structure, remove TUI/R-Dev
- `CLAUDE.md` - Update "Essential Commands" section
- `docs/user/guides/` - Rewrite for simplified CLI
- `.claude/rules/workflows.md` - Update examples

**Total Week 2:** 8-11 hours

---

## Phase 1 Completion Checklist

### Code Changes
- [ ] TUI removed (1,701 lines deleted)
- [ ] R-Dev removed (500 lines deleted)
- [ ] CLI consolidated (ZSH or Python approach chosen)
- [ ] Command set reduced to 8-10 core commands
- [ ] Dependencies updated (textual removed)

### Testing
- [ ] All core tests passing (28-30 tests, 95%+ pass rate)
- [ ] CLI integration tests updated
- [ ] Manual testing of essential commands

### Documentation
- [ ] README.md updated
- [ ] CLAUDE.md updated
- [ ] User guides updated or archived
- [ ] `.STATUS` reflects new metrics

### Git
- [ ] Commit Phase 1 changes
- [ ] Tag as `v2.3.0-phase1` or similar
- [ ] Update release notes

---

## Phase 1 Success Metrics

**Before Phase 1:**
- Total lines: 11,500
- Commands: 15+
- Dependencies: 25+
- Test suite: 35 tests
- Complexity: High (3 interfaces)

**After Phase 1:**
- Total lines: ~8,300 (28% reduction)
- Commands: 8-10 (40% reduction)
- Dependencies: 23 (textual removed)
- Test suite: 28-30 tests (95%+ pass rate)
- Complexity: Medium (1 unified interface)

---

## Decision Point: CLI Approach

**Before proceeding to Task 2.1, we need your input:**

Which CLI consolidation approach do you prefer?

**Option A: ZSH-First** (Recommended for your workflow)
- Pros: Native shell integration, fast for simple ops, matches your dev-tools pattern
- Cons: Less portable (ZSH-specific), harder to test

**Option B: Python-First** (Standard packaging)
- Pros: Portable, standard Python packaging, easier unit testing
- Cons: Slower startup, less shell integration

**Your current dev-tools projects use Option A** (zsh-configuration, aiterm both use ZSH-first). For consistency, **I recommend Option A**.

---

## Next Steps After Phase 1

Once Phase 1 is complete (simplified codebase), we move to **Phase 2: Core AI Features** (Week 3-4):

1. **AI Refactoring Engine** - Analyze note structure, suggest folder reorganization
2. **Tag Suggestion System** - AI-powered tag recommendations
3. **Quality Analysis** - Identify poorly structured notes
4. **Merge Suggestions** - Find and merge duplicate content

Then **Phase 3: Hub Integration** (Week 5-8):

1. **Bi-directional Sync** - project-hub ↔ Obsidian vaults
2. **Task Extraction** - Auto-create tasks from notes
3. **Cross-Vault Search** - Unified search across all vaults

---

## Ready to Start?

Would you like to:
1. **Start Phase 1 immediately** - Begin with TUI removal (Task 1.1)
2. **Decide on CLI approach first** - Choose Option A or B for Task 2.1
3. **Review/modify plan** - Adjust tasks or timeline

Let me know how you'd like to proceed!
