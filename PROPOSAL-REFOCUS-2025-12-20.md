# 🎯 Obsidian CLI Ops - Refocusing Proposals

> **Generated:** 2025-12-20
> **Context:** Redefining project scope to focus on CLI-centric vault management, AI-assisted note organization, and integration with project-hub workflow
>
> **Goal:** Eliminate overlap with existing dev-tools projects (zsh-configuration, aiterm) while creating a laser-focused Obsidian management tool

---

## 📊 Current State Analysis

### What obs Does Now (v2.2.0)
✅ **Strengths:**
- Multi-vault discovery and management
- Knowledge graph analysis (PageRank, centrality)
- AI-powered features (similarity, duplicates, analysis)
- R-Dev integration for research workflows
- Interactive TUI with Textual
- SQLite-backed knowledge base

❌ **Overlaps with Existing Tools:**
- **zsh-configuration**: Workflow management, project context switching
- **aiterm**: Terminal profile management, context detection
- **General shell tools**: File operations, git integration

📈 **Metrics:**
- ~11,500 lines of code
- 394+ tests
- 72% coverage
- Three-layer architecture (Presentation/Core/Data)

### Project-Hub Philosophy
```
Master Hub (project-hub/)
    ↓
Domain Hubs (mediation-planning/, dev-planning/)
    ↓
Project-Specific .STATUS files
```

**Key Insight:** obs should be a **domain tool** for Obsidian vault management, NOT a general workflow manager

---

## 🎨 Proposals (Divergent Thinking)

---

## ⭐ **PROPOSAL A: Pure Obsidian Knowledge Manager**
> **Philosophy:** "Do one thing exceptionally well - manage Obsidian vaults"

### Core Focus
Remove everything NOT directly related to Obsidian vault management. Let other tools handle their domains.

### What Stays
1. **Vault Management**
   - Discovery, scanning, synchronization
   - Graph analysis and metrics
   - Link resolution and broken link detection

2. **AI-Assisted Note Operations** (NEW FOCUS!)
   - `obs refactor` - Reorganize notes based on topics/themes
   - `obs merge <note1> <note2>` - Intelligent note merging
   - `obs split <note>` - Split notes by topic
   - `obs folder-suggest` - Suggest folder structure
   - `obs tag-suggest` - Suggest tags based on content
   - `obs backlink-audit` - Find missing backlinks
   - `obs note-quality` - Assess note quality (completeness, links, structure)

3. **Vault Health**
   - Orphan detection
   - Hub detection
   - Tag consistency
   - Folder structure analysis

### What Goes
- ❌ TUI (too much code for limited value - 1,701 lines!)
- ❌ R-Dev integration (belongs in R package ecosystem)
- ❌ Sync features (use Obsidian's native sync)
- ❌ Generic graph visualization (focus on actionable insights)

### New Command Structure
```bash
# Core operations
obs scan <vault>                   # Scan vault into DB
obs status <vault>                 # Health dashboard

# AI-assisted operations (⭐ NEW!)
obs refactor <vault>               # Suggest reorganization
obs merge <note1> <note2>          # Merge notes intelligently
obs split <note>                   # Split by topic
obs tag-suggest <note|vault>       # Suggest tags
obs folder-suggest <vault>         # Suggest folder structure
obs quality <note|vault>           # Note quality assessment

# Analysis
obs orphans <vault>                # Find orphans
obs hubs <vault>                   # Find hub notes
obs broken-links <vault>           # Find broken links
obs similar <note>                 # Find similar notes

# Cleanup
obs fix-links <vault>              # Auto-fix broken links
obs dedupe <vault>                 # Find and merge duplicates
```

### Benefits
✅ **Laser focus** - One clear purpose
✅ **Unique value** - No overlap with other tools
✅ **AI-powered** - Leverages existing multi-provider architecture
✅ **Actionable** - Commands that DO things, not just show data
✅ **Maintainable** - Remove 1,701 lines of TUI code

### Trade-offs
⚠️ **Less "pretty"** - No TUI (but CLI can be beautiful with Rich)
⚠️ **Less "complete"** - Narrower scope
✅ **More useful** - Focus on high-value operations

### Effort
- **Remove:** 2-3 hours (delete TUI, R-Dev, sync)
- **Refocus:** 4-6 hours (update docs, refactor CLI)
- **New AI features:** 8-12 hours (implement refactor, merge, split)

---

## ⭐ **PROPOSAL B: Obsidian + Project-Hub Integration**
> **Philosophy:** "Bridge Obsidian vaults with project-hub workflow"

### Core Focus
Make obs the **connector** between Obsidian and your project-hub system.

### What Stays
- Vault scanning and analysis
- AI-powered note operations
- Knowledge graph metrics

### What's NEW
1. **Project-Hub Sync**
   ```bash
   obs hub sync                   # Sync .STATUS to Obsidian dashboard
   obs hub export <project>       # Export project notes to hub
   obs hub import <vault>         # Import hub tasks to vault
   ```

2. **Note → Project Mapping**
   ```bash
   obs map <note> <project>       # Link note to project-hub project
   obs project-notes <project>    # List all notes for project
   obs project-status <project>   # Generate .STATUS from notes
   ```

3. **Cross-Vault Operations**
   ```bash
   obs cross-link <vault1> <vault2>  # Find related notes across vaults
   obs cross-merge <vault1> <vault2> # Merge similar cross-vault notes
   obs global-search <query>          # Search across all vaults
   ```

4. **Weekly Planning Integration**
   ```bash
   obs week-notes                 # Extract action items from weekly notes
   obs week-sync                  # Sync weekly plan to Obsidian
   obs deadlines                  # Extract deadlines from vaults
   ```

### Command Structure
```bash
# Vault operations (same as Proposal A)
obs scan, obs status, obs refactor, etc.

# Hub integration (⭐ NEW!)
obs hub sync                       # Bi-directional sync
obs hub export <project>           # Export to hub
obs hub import <vault>             # Import from hub

# Cross-vault (⭐ NEW!)
obs global <command>               # Run command across all vaults
obs cross-link <v1> <v2>           # Cross-vault linking
obs cross-search <query>           # Global search

# Planning integration (⭐ NEW!)
obs extract-tasks <vault>          # Extract TODO items
obs extract-deadlines <vault>      # Extract deadlines
obs update-status <project>        # Update .STATUS from notes
```

### Benefits
✅ **Unique value** - No other tool does this
✅ **Workflow integration** - Connects two ecosystems
✅ **Practical** - Solves real problems (tracking across systems)
✅ **Extensible** - Easy to add more integrations

### Trade-offs
⚠️ **Complexity** - More moving parts
⚠️ **Dependencies** - Coupled to project-hub structure
✅ **High value** - Unique integration point

### Effort
- **Base refactoring:** 4-6 hours
- **Hub integration:** 8-12 hours
- **Cross-vault features:** 6-8 hours

---

## ⭐ **PROPOSAL C: AI-First Note Organizer**
> **Philosophy:** "Let AI do the heavy lifting - you make the decisions"

### Core Focus
Make obs an **AI copilot** for note organization, not just a database viewer.

### What Stays
- Vault scanning (minimal)
- AI provider infrastructure
- Domain models

### What's TRANSFORMED
Everything becomes AI-driven suggestions, user-approved actions.

### Key Features
1. **Intelligent Refactoring**
   ```bash
   obs analyze-structure <vault>     # AI analyzes entire structure
   # Output: Proposed folder reorganization, tag taxonomy, note merges

   obs apply-structure <vault>       # Apply AI suggestions (interactive)
   ```

2. **Smart Note Operations**
   ```bash
   obs improve <note>                # AI suggests improvements
   # - Missing backlinks
   # - Better headings
   # - Tag suggestions
   # - Related notes to link
   # - Content gaps

   obs rewrite <note>                # AI-assisted rewriting
   # - Improve clarity
   # - Fix structure
   # - Add examples
   # - Standardize format
   ```

3. **Automated Workflows**
   ```bash
   obs watch <vault>                 # Watch mode - continuous improvement
   # Monitors vault, suggests improvements in real-time

   obs daily-digest <vault>          # Daily improvement suggestions
   # Email or TUI with prioritized improvements
   ```

4. **Batch Operations**
   ```bash
   obs batch-tag <vault>             # Tag all untagged notes
   obs batch-link <vault>            # Add missing backlinks
   obs batch-folder <vault>          # Move notes to better folders
   ```

### Command Structure
```bash
# Analysis
obs analyze-structure <vault>      # Full structure analysis
obs analyze-note <note>             # Single note analysis

# AI-powered operations
obs improve <note>                  # Improvement suggestions
obs refactor <vault>                # Structure refactor
obs merge-suggest <vault>           # Merge candidates
obs split-suggest <note>            # Split suggestions

# Batch operations
obs batch-tag <vault>               # Auto-tag
obs batch-link <vault>              # Auto-backlink
obs batch-clean <vault>             # Clean up

# Automation
obs watch <vault>                   # Real-time suggestions
obs digest <vault>                  # Daily digest
```

### Benefits
✅ **Unique positioning** - AI-first, not database-first
✅ **High value** - Saves hours of manual work
✅ **Modern** - Leverages LLMs for what they're good at
✅ **Simple** - Fewer commands, more power

### Trade-offs
⚠️ **AI dependency** - Requires AI providers
⚠️ **Cost** - API costs for heavy users
✅ **Value** - Time saved >> cost

### Effort
- **Refactoring:** 6-8 hours
- **Core AI features:** 12-16 hours
- **Batch operations:** 8-10 hours
- **Watch mode:** 6-8 hours

---

## 🎯 **PROPOSAL D: Hybrid - CLI Power + Hub Integration**
> **Philosophy:** "Best of A + B"

### Core Focus
Pure Obsidian management (Proposal A) + Project-hub integration (Proposal B)

### Command Structure
```bash
# Vault Management (Proposal A)
obs scan, refactor, merge, split, tag-suggest, etc.

# Hub Integration (Proposal B)
obs hub sync, hub export, cross-link, etc.

# Skip: Heavy AI automation (Proposal C - too complex)
```

### Benefits
✅ **Focused** - Clear boundaries
✅ **Integrated** - Works with existing workflow
✅ **Practical** - Solves real problems
✅ **Maintainable** - Not too complex

### Effort
- **Moderate:** 16-24 hours total

---

## 📋 Overlap Analysis

### vs. zsh-configuration
| Feature | obs (current) | zsh-configuration | Recommendation |
|---------|--------------|-------------------|----------------|
| Workflow management | ❌ R-Dev commands | ✅ Work sessions, dispatchers | **Remove from obs** |
| Project context | ❌ Vault switching | ✅ Smart context detection | **Remove from obs** |
| CLI aliases | ❌ `obs` shortcuts | ✅ 28 curated aliases | **Keep minimal in obs** |

**Decision:** Remove R-Dev, rely on zsh-configuration for workflow orchestration

### vs. aiterm
| Feature | obs (current) | aiterm | Recommendation |
|---------|--------------|--------|----------------|
| Terminal profiles | ❌ None | ✅ Context-aware profiles | **Stay out** |
| Claude integration | ❌ AI providers | ✅ Hooks, commands, approvals | **Coordinate** |
| iTerm2 control | ❌ None | ✅ Profile switching | **Stay out** |

**Decision:** obs uses AI for note operations, aiterm handles terminal optimization

### vs. project-hub
| Feature | obs (current) | project-hub | Recommendation |
|---------|--------------|-------------|----------------|
| Status tracking | ❌ `.STATUS` in vault | ✅ Central hub | **Integrate** |
| Weekly planning | ❌ None | ✅ Weekly files | **Sync to/from** |
| Cross-domain | ❌ Cross-vault (weak) | ✅ Cross-domain tracking | **Feed data to hub** |

**Decision:** obs should sync WITH hub, not replace it

---

## 🎨 Multiple Perspectives

### 1. **Technical Perspective**
**Current Architecture:** Over-engineered for current use
- **TUI:** 1,701 lines for limited value
- **Three layers:** Good design, but can simplify
- **AI infrastructure:** Excellent, keep and expand
- **Database:** SQLite works well, keep

**Recommendation:**
- Keep: Core layer, Data layer, AI infrastructure
- Simplify: Presentation layer (CLI only, no TUI)
- Focus: AI-powered note operations

### 2. **User Experience Perspective**
**Current UX:** Too many modes (CLI, TUI, Python CLI)
- **CLI:** Good for quick operations
- **TUI:** Pretty but slow workflow
- **Python CLI:** Direct access, power users

**Recommendation:**
- Single CLI with rich output (use `rich` library)
- Interactive prompts for destructive operations
- Batch mode for automation
- Clear, actionable output

### 3. **ADHD-Friendly Perspective**
**Current:** TUI is visually appealing but:
- Too many key bindings to remember
- Context switching between CLI and TUI
- Not keyboard-driven enough

**Recommendation:**
- **Proposal A or D:** Simple CLI, one command = one action
- **Proposal C:** AI does the thinking, you approve
- Progressive disclosure in CLI
- Clear default behaviors

### 4. **Maintenance Perspective**
**Current Burden:**
- TUI screens require constant updates
- Three interfaces to maintain (CLI, Python CLI, TUI)
- Complex test matrix

**Recommendation:**
- Remove TUI → eliminate 1,701 lines + tests
- Single CLI interface → simpler testing
- Focus on core features → less surface area

### 5. **Future Scalability Perspective**
**Growth Paths:**
- More AI features (refactor, merge, split)
- More integrations (project-hub, Obsidian API)
- More automation (watch mode, digests)

**Recommendation:**
- **Proposal C or D:** Best positioned for AI features
- **Proposal B or D:** Best for integrations
- Keep architecture flexible for future GUI (Electron or Tauri)

---

## 🚀 Quick Wins vs. Long-term

### Quick Wins (1-2 weeks)
1. ⚡ **Remove TUI** (2-3 hours)
   - Delete `src/python/tui/` (1,701 lines)
   - Update tests
   - ~1,800 LOC reduction

2. ⚡ **Remove R-Dev** (1-2 hours)
   - Move to R package ecosystem
   - ~500 LOC reduction

3. ⚡ **Simplify CLI** (3-4 hours)
   - Consolidate Python CLI and ZSH CLI
   - Use `rich` for beautiful output
   - Clear command structure

4. ⚡ **Focus AI features** (6-8 hours)
   - `obs refactor`
   - `obs tag-suggest`
   - `obs quality`

**Total Quick Wins:** 12-17 hours, ~2,300 LOC reduction, clearer focus

### Long-term Projects (1-3 months)
1. 🏗️ **Hub Integration** (16-24 hours)
   - Bi-directional sync with project-hub
   - Cross-vault operations
   - Task extraction

2. 🏗️ **Advanced AI** (24-32 hours)
   - `obs merge` (intelligent merging)
   - `obs split` (topic-based splitting)
   - `obs watch` (continuous monitoring)

3. 🏗️ **Batch Operations** (16-20 hours)
   - Auto-tagging
   - Auto-linking
   - Structure cleanup

---

## 🎯 Recommended Path

### **Phase 1: Simplify (1-2 weeks)**
Follow **Proposal A** to establish clear focus:

**Week 1:**
1. Remove TUI (1,701 lines)
2. Remove R-Dev integration
3. Consolidate to single CLI
4. Update documentation

**Week 2:**
1. Implement `obs refactor`
2. Implement `obs tag-suggest`
3. Implement `obs quality`
4. Test suite cleanup

**Outcome:** ~2,300 LOC reduction, laser-focused tool

### **Phase 2: Integrate (2-4 weeks)**
Add **Proposal B** features:

**Weeks 3-4:**
1. Hub sync mechanism
2. Cross-vault search
3. Task extraction

**Weeks 5-6:**
1. Status generation from notes
2. Deadline extraction
3. Weekly planning sync

**Outcome:** Integration with project-hub workflow

### **Phase 3: Enhance (Optional, 2-3 months)**
Add **Proposal C** features as needed:

- Advanced AI operations
- Batch processing
- Watch mode

**Outcome:** AI-first note organization

---

## 💡 Hybrid Solutions

### Option 1: A + Light B
- Core: Proposal A (pure Obsidian focus)
- Add: Basic hub sync (`obs hub sync`, `obs hub export`)
- Skip: Cross-vault complexity, heavy automation

### Option 2: A + Light C
- Core: Proposal A (pure Obsidian focus)
- Add: Basic AI suggestions (`obs improve`, `obs suggest`)
- Skip: Watch mode, batch operations

### Option 3: Minimal MVP
- Core vault operations only
- AI-powered refactoring
- Single CLI interface
- **Total:** ~4,000 lines (down from 11,500)

---

## 📊 Complexity vs. Value Matrix

```
High Value ─────────────────────────────────
   │
   │  obs refactor        obs hub sync
   │  obs tag-suggest     obs cross-link
   │  obs quality
   │
   │                      obs batch-tag
   │  obs similar         obs watch
   │  obs orphans
   │
   │  TUI (❌)            obs sync (❌)
   │  Graph viz (❌)      R-Dev (❌)
   │
Low Value ─────────────────────────────────
      Low Complexity            High Complexity
```

**Keep:** Top-left quadrant (high value, low complexity)
**Remove:** Bottom row (low value regardless of complexity)
**Optional:** Top-right (high value, high complexity)

---

## 🎯 Final Recommendation

### **Start with Proposal D (Hybrid)**

**Rationale:**
1. ✅ **Clear focus** - Obsidian vault management only
2. ✅ **Unique value** - AI-powered + hub integration
3. ✅ **No overlap** - Distinct from zsh-configuration and aiterm
4. ✅ **Practical** - Solves real workflow problems
5. ✅ **Maintainable** - Simpler codebase, clearer purpose

### **Implementation Plan**

**Immediate (This Week):**
1. Remove TUI
2. Remove R-Dev
3. Document new scope in README

**Short-term (Next 2 Weeks):**
1. Consolidate CLI
2. Implement core AI features
3. Basic hub sync

**Medium-term (Next 1-2 Months):**
1. Advanced AI features
2. Cross-vault operations
3. Automation features

---

## 🤔 Questions to Resolve

Before proceeding, clarify:

1. **AI Dependency:** Are you comfortable relying on AI providers for core features?
2. **Hub Structure:** Is project-hub structure stable enough to integrate?
3. **TUI Users:** Any users who would miss the TUI?
4. **R-Dev:** Should R-Dev move to mediation-planning or separate tool?
5. **Timeline:** Quick refactor (2 weeks) or gradual evolution (2-3 months)?

---

## 📝 Next Steps

Choose one:

### Option A: Aggressive Refactor (Recommended)
1. Accept Proposal D
2. Remove TUI and R-Dev this week
3. Implement core AI features next week
4. Add hub integration in 2-4 weeks

### Option B: Gradual Evolution
1. Keep TUI for now
2. Add AI features alongside
3. Deprecate TUI slowly
4. Add hub integration later

### Option C: Minimal Viable Product
1. Strip down to essentials
2. Just vault scan + AI refactor
3. Build up from there

---

**Recommendation:** **Option A** (Aggressive Refactor)
- Clear the deck NOW
- Fast pivot to high-value features
- Clean codebase for future work
- Less maintenance burden

---

*Created: 2025-12-20*
*Author: Claude Sonnet 4.5*
*Context: Brainstorm mode for project refocusing*
