# 🗺️ Implementation Roadmap: Refocusing obs

> **Based on:** PROPOSAL-REFOCUS-2025-12-20.md (Proposal D - Hybrid)
> **Date:** 2025-12-20
> **Goal:** Transform obs from generic vault manager → focused AI-powered Obsidian tool

---

## 📋 Executive Summary

**What:** Refocus `obs` to be a laser-focused Obsidian vault management tool with AI-powered note organization and project-hub integration

**Why:**
- ❌ Current state has overlap with zsh-configuration and aiterm
- ❌ TUI adds 1,701 lines with limited value
- ❌ R-Dev belongs in R package ecosystem
- ✅ AI-powered features are unique and high-value
- ✅ Hub integration solves real workflow problems

**How:** Three phases over 4-8 weeks

**Impact:**
- **Code:** ~11,500 → ~4,500 lines (61% reduction)
- **Focus:** Multi-purpose → Single-purpose (Obsidian only)
- **Value:** 10x increase in usefulness per line of code

---

## 🎯 Three-Phase Approach

```
Phase 1: SIMPLIFY (Week 1-2)
├── Remove TUI (1,701 lines)
├── Remove R-Dev integration
├── Consolidate to single CLI
└── Update documentation

Phase 2: CORE AI (Week 3-4)
├── obs refactor
├── obs tag-suggest
├── obs quality
├── obs merge-suggest
└── obs split-suggest

Phase 3: INTEGRATE (Week 5-8)
├── Hub sync (bi-directional)
├── Cross-vault operations
├── Task extraction
└── Status generation
```

---

## 📅 PHASE 1: SIMPLIFY (Week 1-2)

### Goal
Remove everything NOT core to Obsidian vault management

### Tasks

#### 🗑️ **Day 1-2: Remove TUI**

**Delete:**
```bash
rm -rf src/python/tui/           # 1,701 lines
rm -rf src/python/tests/test_tui_*
rm -rf src/python/tests/test_*_explorer.py
rm -rf src/python/tests/test_*_visualizer.py
```

**Update:**
- Remove TUI imports from `src/python/obs_cli.py`
- Remove `tui` command from ZSH wrapper
- Update README (remove TUI screenshots/references)
- Update CLAUDE.md (remove TUI architecture)

**Tests:**
- Remove TUI-related tests
- Update test count in docs (394 → ~200)

**Time:** 2-3 hours

**Checklist:**
- [ ] Delete `src/python/tui/` directory
- [ ] Delete TUI tests
- [ ] Remove TUI imports
- [ ] Update CLI help text
- [ ] Update README
- [ ] Update CLAUDE.md
- [ ] Run remaining tests
- [ ] Commit: "refactor: Remove TUI (1,701 lines) - focus on CLI"

---

#### 🗑️ **Day 2-3: Remove R-Dev Integration**

**Delete:**
```bash
# In src/obs.zsh
# Remove obs_r_dev, obs_r_log, obs_r_link, etc.

# In src/python/obs_cli.py
# Remove r-dev subcommand (if exists)
```

**Relocate:**
- Move R-Dev to `~/projects/r-packages/mediation-planning/`
- Or create standalone `obs-r` tool if needed

**Update:**
- README: Remove R-Dev examples
- CLAUDE.md: Remove R-Dev references
- Help text: Remove r/r-dev commands

**Time:** 1-2 hours

**Checklist:**
- [ ] Remove R-Dev code from src/obs.zsh
- [ ] Remove R-Dev tests
- [ ] Update completions
- [ ] Update documentation
- [ ] (Optional) Create standalone tool
- [ ] Commit: "refactor: Remove R-Dev integration - moved to R ecosystem"

---

#### 🔧 **Day 3-4: Consolidate CLI**

**Goal:** Single, beautiful CLI using `rich` library

**Current State:**
- ZSH wrapper (`src/obs.zsh`)
- Python CLI (`src/python/obs_cli.py`)
- Direct Python imports

**Proposed State:**
- Single entry point: `obs` command
- Python CLI with `rich` for beautiful output
- ZSH wrapper is minimal dispatcher

**Implementation:**
```python
# Enhanced CLI with rich
from rich.console import Console
from rich.table import Table
from rich.progress import track

console = Console()

def scan_vault(vault_path):
    """Scan vault with beautiful progress bar."""
    with console.status("[bold green]Scanning vault..."):
        # Do scan
        pass

    # Beautiful table output
    table = Table(title="Scan Results")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="magenta")
    table.add_row("Notes", str(note_count))
    table.add_row("Links", str(link_count))
    console.print(table)
```

**Time:** 3-4 hours

**Checklist:**
- [ ] Add `rich` to requirements.txt
- [ ] Create rich-based output functions
- [ ] Update all commands to use rich
- [ ] Test output in terminal
- [ ] Update examples in README
- [ ] Commit: "feat: Add rich CLI output for better UX"

---

#### 📝 **Day 4-5: Update Documentation**

**Update Files:**
1. **README.md**
   - Remove TUI sections
   - Remove R-Dev sections
   - Update feature list
   - New Quick Start
   - Add "Why obs?" section (unique value prop)

2. **CLAUDE.md**
   - Update architecture (no TUI layer)
   - Remove TUI workflows
   - Update LOC counts
   - New command structure

3. **IDEAS.md**
   - Archive old TUI ideas
   - Add new AI-focused ideas

4. **.STATUS**
   - Update progress (98% → 50% due to scope change)
   - New goals
   - Updated metrics

**Time:** 2-3 hours

**Checklist:**
- [ ] Update README.md
- [ ] Update CLAUDE.md
- [ ] Update IDEAS.md
- [ ] Update .STATUS
- [ ] Update docs/
- [ ] Commit: "docs: Update for refocused scope"

---

### Phase 1 Deliverables

✅ **Code Reduction:**
- ~2,300 lines removed (TUI + R-Dev)
- ~9,200 lines remaining

✅ **Clarity:**
- Single CLI interface
- Beautiful rich output
- Clear focus on Obsidian

✅ **Foundation:**
- Clean slate for AI features
- Simplified testing
- Better maintenance

**Total Time:** 12-17 hours (1.5-2 weeks part-time)

---

## 📅 PHASE 2: CORE AI (Week 3-4)

### Goal
Implement high-value AI-powered features for note organization

### Tasks

#### 🤖 **Week 3: AI-Powered Refactoring**

**Feature 1: `obs refactor <vault>`**

Analyzes vault structure and suggests reorganization.

**Implementation:**
```python
def refactor_vault(vault_id: str, provider: str = "gemini-api"):
    """
    Analyze vault structure and suggest improvements.

    Returns:
    - Folder reorganization suggestions
    - Tag taxonomy proposal
    - Note merge candidates
    - Orphan resolution suggestions
    """
    # 1. Scan vault structure
    notes = vault_manager.get_notes(vault_id)

    # 2. Analyze with AI
    analysis = ai_client.analyze_structure(notes)

    # 3. Generate suggestions
    suggestions = {
        "folders": analysis.folder_suggestions,
        "tags": analysis.tag_taxonomy,
        "merges": analysis.merge_candidates,
        "orphans": analysis.orphan_solutions
    }

    # 4. Display with rich
    display_refactor_suggestions(suggestions)

    # 5. Prompt for approval
    if confirm("Apply suggestions?"):
        apply_refactor(suggestions)
```

**Prompt Template:**
```
Analyze this Obsidian vault structure:

Notes: {note_list}
Current folders: {folder_structure}
Current tags: {tag_list}

Provide:
1. Suggested folder reorganization
2. Improved tag taxonomy
3. Notes that should be merged
4. Solutions for orphaned notes

Format as JSON.
```

**Time:** 6-8 hours

**Checklist:**
- [ ] Create `refactor` command
- [ ] Implement structure analysis
- [ ] Create AI prompts
- [ ] Add rich output
- [ ] Add confirmation prompts
- [ ] Write tests
- [ ] Update documentation
- [ ] Commit: "feat: Add AI-powered vault refactoring"

---

**Feature 2: `obs tag-suggest <note|vault>`**

Suggests tags for untagged or poorly-tagged notes.

**Implementation:**
```python
def suggest_tags(target: str, context: str = "vault"):
    """
    Suggest tags based on note content and vault context.

    Args:
        target: Note ID or vault ID
        context: "vault" or "global"
    """
    if context == "vault":
        # Use vault's existing tag taxonomy
        existing_tags = get_vault_tags(vault_id)
        prompt = f"Suggest tags from: {existing_tags}"
    else:
        # Generate new tags
        prompt = "Suggest appropriate tags"

    # Analyze content
    suggestions = ai_client.suggest_tags(note_content, prompt)

    # Display
    display_tag_suggestions(note, suggestions)

    # Apply
    if confirm("Apply tags?"):
        apply_tags(note_id, suggestions)
```

**Time:** 4-6 hours

**Checklist:**
- [ ] Create `tag-suggest` command
- [ ] Implement tag analysis
- [ ] Support batch mode
- [ ] Add rich output
- [ ] Write tests
- [ ] Commit: "feat: Add AI-powered tag suggestions"

---

#### 🎯 **Week 4: Quality & Merge Operations**

**Feature 3: `obs quality <note|vault>`**

Assesses note quality and suggests improvements.

**Metrics:**
- Completeness (word count, structure)
- Connectivity (backlinks, tags)
- Clarity (readings, structure)
- Actionability (TODOs, next steps)

**Implementation:**
```python
def assess_quality(note_id: str):
    """Assess note quality and suggest improvements."""
    note = vault_manager.get_note(note_id)

    metrics = {
        "word_count": len(note.content.split()),
        "backlinks": count_backlinks(note_id),
        "tags": len(note.tags),
        "headings": count_headings(note.content),
        "todos": count_todos(note.content)
    }

    # AI analysis
    ai_suggestions = ai_client.assess_note(note.content, metrics)

    # Score (0-100)
    score = calculate_quality_score(metrics, ai_suggestions)

    # Display
    display_quality_report(note, score, ai_suggestions)
```

**Time:** 4-6 hours

---

**Feature 4: `obs merge-suggest <vault>`**

Finds notes that should be merged.

**Implementation:**
```python
def suggest_merges(vault_id: str, threshold: float = 0.8):
    """Find notes that should be merged based on similarity."""
    notes = vault_manager.get_notes(vault_id)

    # Generate embeddings
    embeddings = {n.id: ai_client.embed(n.content) for n in notes}

    # Find similar pairs
    candidates = []
    for n1, n2 in combinations(notes, 2):
        similarity = cosine_similarity(embeddings[n1.id], embeddings[n2.id])
        if similarity > threshold:
            candidates.append((n1, n2, similarity))

    # Display
    display_merge_candidates(candidates)

    # Allow interactive merge
    for c in candidates:
        if confirm(f"Merge {c[0].title} + {c[1].title}?"):
            merge_notes(c[0], c[1])
```

**Time:** 6-8 hours

---

### Phase 2 Deliverables

✅ **New Features:**
- `obs refactor` - Structure analysis
- `obs tag-suggest` - Tag suggestions
- `obs quality` - Quality assessment
- `obs merge-suggest` - Merge candidates

✅ **Value:**
- Saves hours of manual work
- Leverages AI for insights
- Actionable recommendations

**Total Time:** 20-28 hours (2-3 weeks part-time)

---

## 📅 PHASE 3: INTEGRATE (Week 5-8)

### Goal
Integrate with project-hub workflow

### Tasks

#### 🔗 **Week 5-6: Hub Sync**

**Feature: `obs hub sync`**

Bi-directional sync with project-hub.

**Sync Operations:**
1. **Vault → Hub:**
   - Extract .STATUS from vault notes
   - Generate project summaries
   - Extract deadlines
   - Extract action items

2. **Hub → Vault:**
   - Import weekly plan
   - Import cross-domain tasks
   - Import project status

**Implementation:**
```python
def hub_sync(vault_id: str, project: str):
    """Sync vault with project-hub."""
    # 1. Extract from vault
    vault_data = extract_vault_data(vault_id)

    # 2. Update hub
    update_hub_status(project, vault_data)

    # 3. Import from hub
    hub_data = read_hub_data(project)

    # 4. Update vault
    update_vault_notes(vault_id, hub_data)

    # 5. Report
    display_sync_report(vault_data, hub_data)
```

**Time:** 8-12 hours

---

**Feature: `obs extract-tasks <vault>`**

Extracts TODO items from vault notes.

**Implementation:**
```python
def extract_tasks(vault_id: str):
    """Extract all TODO items from vault."""
    notes = vault_manager.get_notes(vault_id)

    tasks = []
    for note in notes:
        # Find TODO items
        todos = extract_todos(note.content)
        for todo in todos:
            tasks.append({
                "text": todo,
                "note": note.title,
                "path": note.path
            })

    # Display
    display_task_list(tasks)

    # Export
    export_to_hub(tasks, "tasks.md")
```

**Time:** 4-6 hours

---

#### 🌐 **Week 7-8: Cross-Vault**

**Feature: `obs cross-link <vault1> <vault2>`**

Finds related notes across vaults.

**Implementation:**
```python
def cross_link(vault1_id: str, vault2_id: str):
    """Find related notes across vaults."""
    notes1 = vault_manager.get_notes(vault1_id)
    notes2 = vault_manager.get_notes(vault2_id)

    # Generate embeddings
    emb1 = {n.id: ai_client.embed(n.content) for n in notes1}
    emb2 = {n.id: ai_client.embed(n.content) for n in notes2}

    # Find matches
    matches = []
    for n1 in notes1:
        for n2 in notes2:
            sim = cosine_similarity(emb1[n1.id], emb2[n2.id])
            if sim > 0.7:
                matches.append((n1, n2, sim))

    # Display
    display_cross_links(matches)

    # Create links
    if confirm("Create cross-vault links?"):
        create_cross_links(matches)
```

**Time:** 6-8 hours

---

**Feature: `obs global-search <query>`**

Search across all registered vaults.

**Implementation:**
```python
def global_search(query: str):
    """Search across all vaults."""
    vaults = vault_manager.list_vaults()

    results = []
    for vault in vaults:
        vault_results = vault_manager.search_notes(query, vault.id)
        results.extend([(vault, r) for r in vault_results])

    # Display with rich
    display_global_results(results)
```

**Time:** 3-4 hours

---

### Phase 3 Deliverables

✅ **Integration:**
- Hub sync (bi-directional)
- Task extraction
- Cross-vault operations
- Global search

✅ **Value:**
- Connects Obsidian ↔ project-hub
- Works across multiple vaults
- Automates tedious tasks

**Total Time:** 21-30 hours (3-4 weeks part-time)

---

## 📊 Final State

### Code Metrics

**Before:**
- Total: ~11,500 lines
- Python: ~7,500 lines
- ZSH: ~680 lines
- Tests: 394

**After:**
- Total: ~4,500 lines (-61%)
- Python: ~3,500 lines
- ZSH: ~200 lines (minimal wrapper)
- Tests: ~200 (focused)

### Feature Comparison

| Feature | Before | After |
|---------|--------|-------|
| TUI | ✅ 1,701 lines | ❌ Removed |
| R-Dev | ✅ ~500 lines | ❌ Removed |
| Graph viz | ✅ ASCII art | ⚠️ Minimal |
| AI features | ⚠️ Basic | ✅ Advanced |
| Hub integration | ❌ None | ✅ Full sync |
| Cross-vault | ❌ None | ✅ Yes |

### Command Structure

**Before (15 commands):**
```bash
obs, obs switch, obs manage, obs open, obs graph,
obs stats, obs ai, obs r, obs discover, obs tui,
obs vaults, obs sync, obs install, obs audit, obs help
```

**After (12 commands):**
```bash
# Core (4)
obs scan, obs status, obs analyze, obs health

# AI-powered (5)
obs refactor, obs tag-suggest, obs quality,
obs merge-suggest, obs split-suggest

# Integration (3)
obs hub, obs cross, obs global
```

**Simpler, more focused, higher value per command**

---

## ✅ Success Criteria

### Metrics
- [ ] Code reduced by >50% (~11,500 → ~4,500 lines)
- [ ] No feature overlap with zsh-configuration or aiterm
- [ ] At least 3 new AI-powered features
- [ ] Hub integration working bi-directionally
- [ ] Test coverage maintained at 70%+
- [ ] Documentation fully updated

### Quality
- [ ] Clear, single-purpose tool ("Obsidian AI assistant")
- [ ] Beautiful CLI output (rich library)
- [ ] Fast performance (<2s for most operations)
- [ ] Reliable AI features (90%+ useful suggestions)
- [ ] Easy to maintain (<100 LOC per feature)

### Adoption
- [ ] Used weekly for vault management
- [ ] Integrated into daily workflow
- [ ] Saves >2 hours per week
- [ ] Positive user feedback

---

## 🚧 Risks & Mitigation

### Risk 1: AI Quality
**Risk:** AI suggestions aren't useful

**Mitigation:**
- Start with high-quality providers (Claude, Gemini)
- Add user feedback loop
- Allow manual override
- Iterate on prompts

### Risk 2: Hub Integration Complexity
**Risk:** Project-hub structure changes

**Mitigation:**
- Use well-defined interfaces
- Version the sync format
- Make integration optional
- Fall back gracefully

### Risk 3: Missing TUI
**Risk:** Users miss visual interface

**Mitigation:**
- Make CLI beautiful with rich
- Consider web UI later (separate project)
- Focus on value, not prettiness

### Risk 4: Scope Creep
**Risk:** Feature requests pull back to general tool

**Mitigation:**
- Strict "Obsidian only" rule
- Document what's out of scope
- Point to other tools for their domains

---

## 🎯 Next Steps

### This Week (Dec 20-27)
1. [ ] Review proposals with stakeholders
2. [ ] Decide on approach (recommend: Proposal D)
3. [ ] Create feature branch: `refactor/focus-obsidian`
4. [ ] Start Phase 1: Remove TUI

### Week 2 (Dec 27-Jan 3)
1. [ ] Complete Phase 1: Simplify
2. [ ] Update all documentation
3. [ ] Merge to main
4. [ ] Tag as v3.0.0-alpha

### Weeks 3-4 (Jan 3-17)
1. [ ] Implement Phase 2: Core AI
2. [ ] Test with real vaults
3. [ ] Iterate on AI prompts
4. [ ] Tag as v3.0.0-beta

### Weeks 5-8 (Jan 17-Feb 14)
1. [ ] Implement Phase 3: Integration
2. [ ] Test hub sync
3. [ ] Document integration patterns
4. [ ] Tag as v3.0.0

---

## 📝 Decision Points

Before proceeding, confirm:

- [ ] **Scope:** Obsidian-only tool (no general workflows)
- [ ] **TUI:** Remove (yes, it's 1,701 lines of limited value)
- [ ] **R-Dev:** Remove (move to R ecosystem)
- [ ] **AI:** Focus on note operations (refactor, tag, quality)
- [ ] **Hub:** Integrate with project-hub
- [ ] **Timeline:** 6-8 weeks part-time is acceptable

---

**Recommendation:** Proceed with Phase 1 immediately. It's low-risk, high-value, and creates foundation for everything else.

---

*Created: 2025-12-20*
*Based on: PROPOSAL-REFOCUS-2025-12-20.md*
*Ready to implement: Yes*
