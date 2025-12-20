# ADHD-Friendly Claude Plugin Proposals

> **For**: Research, Teaching, and Code Development
> **Works with**: Claude Code CLI + Claude UI (Web/Desktop)
> **Design Philosophy**: Reduce cognitive load, maintain momentum, smart defaults

---

## Executive Summary

Three plugin concepts designed around your existing workflow patterns:

| Plugin | Purpose | Key Feature |
|--------|---------|-------------|
| **Focus Flow** | ADHD momentum keeper | Context-aware task guidance |
| **Research Bridge** | Research/teaching workflow | Obsidian ↔ Code ↔ Publication pipeline |
| **Code Scaffold** | Development acceleration | Three-layer auto-generation |

---

## Plugin 1: Focus Flow 🎯

### Concept: ADHD Momentum Keeper

An intelligent assistant that understands your current context and keeps you in flow state by:
- Remembering where you left off
- Breaking complex tasks into bite-sized steps
- Providing gentle nudges without overwhelm
- Auto-generating session summaries

### Workflow Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                     FOCUS FLOW                               │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  START SESSION                                               │
│       │                                                      │
│       ▼                                                      │
│  ┌─────────────┐    "Welcome back! Last session you were    │
│  │ Context     │     working on test_note_explorer.py       │
│  │ Restore     │     (27 failures remaining). Continue?"    │
│  └──────┬──────┘                                            │
│         │                                                    │
│         ▼                                                    │
│  ┌─────────────┐    "Here's your focus list:                │
│  │ Task        │     □ Fix Note mock objects (est. 15min)   │
│  │ Breakdown   │     □ Update conftest.py fixtures          │
│  │             │     □ Run pytest to verify"                │
│  └──────┬──────┘                                            │
│         │                                                    │
│         ▼                                                    │
│  ┌─────────────┐    [Working...]                            │
│  │ Active      │    "✓ Fixed 5/27 failures"                 │
│  │ Tracking    │    "Momentum: 🔥🔥🔥 (3 tasks done)"       │
│  └──────┬──────┘                                            │
│         │                                                    │
│  DISTRACTION DETECTED (context switch)                      │
│         │                                                    │
│         ▼                                                    │
│  ┌─────────────┐    "Bookmark created. When ready:          │
│  │ Gentle      │     'focus resume' to continue where       │
│  │ Bookmark    │     you left off."                         │
│  └──────┬──────┘                                            │
│         │                                                    │
│         ▼                                                    │
│  ┌─────────────┐    Session: 45min                          │
│  │ Auto        │    ✅ Fixed 12 tests                       │
│  │ Summary     │    → Next: 15 failures remaining           │
│  └─────────────┘                                            │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### Commands (CLI + UI)

```bash
# CLI Commands
focus start              # Begin focused session with context restore
focus status             # Show current task + momentum
focus break              # Bookmark + gentle pause reminder
focus resume             # Restore last context instantly
focus done               # Mark current task complete, show next
focus stuck              # Get unstuck suggestions
focus wrap               # End session with auto-summary

# Natural Language (UI)
"What was I working on?"
"I'm stuck on this test"
"Break this into smaller steps"
"I need to switch contexts - save my place"
"What should I do next?"
```

### ADHD-Friendly Features

| Feature | How It Helps |
|---------|--------------|
| **Context Restore** | No "where was I?" anxiety |
| **Micro-tasks** | 15-minute chunks, not hours |
| **Momentum Visualization** | 🔥 streaks for dopamine |
| **Gentle Bookmarks** | Switch contexts guilt-free |
| **Auto-summaries** | Never lose progress |
| **Stuck Detection** | Proactive help when spinning |

### Integration Points

```python
# Reads from your existing workflow
.STATUS                    # Current project state
.claude/sessions/          # Past session context
TODOS.md                   # Task priorities
git log                    # Recent work

# Writes to
.claude/focus/current.json # Active focus state
.claude/focus/bookmarks/   # Saved contexts
.claude/sessions/          # Session summaries
```

### Sample Interaction

```
You: focus start

Focus Flow: 👋 Welcome back!

📍 Last session (2 hours ago):
   - Working on: test_note_explorer.py
   - Progress: Fixed 12/27 failures
   - Stopped at: test_search_filters()

🎯 Suggested focus (15 min):
   □ Fix remaining 15 test failures
   □ Files: test_note_explorer.py, conftest.py

Ready to continue? [Y/n]

You: y

Focus Flow: ✅ Context restored. Let's fix those tests!

   Current file: test_note_explorer.py:89
   Issue: Mock data uses dict, needs Note object

   Quick fix pattern:
   ```python
   # Before
   mock_notes = [{"id": 1, "title": "Test"}]

   # After
   from core.models import Note
   mock_notes = [Note(id=1, title="Test", ...)]
   ```

   Apply this pattern to 15 locations? [Y/n]
```

---

## Plugin 2: Research Bridge 📚

### Concept: Research → Teaching → Publication Pipeline

An intelligent bridge connecting your knowledge management (Obsidian), code development, and academic output. Designed for the research-teaching-code workflow.

### Workflow Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    RESEARCH BRIDGE                           │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  KNOWLEDGE LAYER (Obsidian Vaults)                          │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐                  │
│  │ Theory   │  │ Methods  │  │ Results  │                  │
│  │ Notes    │  │ Notes    │  │ Notes    │                  │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘                  │
│       │             │             │                          │
│       └─────────────┼─────────────┘                          │
│                     │                                        │
│                     ▼                                        │
│  ┌─────────────────────────────────────┐                    │
│  │         RESEARCH BRIDGE              │                    │
│  │                                      │                    │
│  │  "What theory supports this code?"   │                    │
│  │  "Generate teaching example from X"  │                    │
│  │  "Draft methods section for Y"       │                    │
│  │  "Find related work in my notes"     │                    │
│  └─────────────────────────────────────┘                    │
│                     │                                        │
│       ┌─────────────┼─────────────┐                          │
│       │             │             │                          │
│       ▼             ▼             ▼                          │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐                  │
│  │ Code     │  │ Teaching │  │ Papers   │                  │
│  │ Examples │  │ Materials│  │ & Drafts │                  │
│  └──────────┘  └──────────┘  └──────────┘                  │
│                                                              │
│  CODE LAYER          TEACHING LAYER      PUBLICATION LAYER  │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### Commands (CLI + UI)

```bash
# Research Commands
research context "topic"      # Find relevant notes + code
research cite <note_id>       # Generate citation from note
research link                 # Connect current code to theory notes
research gaps                 # Find under-documented areas

# Teaching Commands
teach example <concept>       # Generate teaching example from notes
teach explain <code_file>     # Create explanation for students
teach quiz <topic>            # Generate practice questions
teach simplify <note>         # Create beginner-friendly version

# Publication Commands
publish draft <section>       # Draft paper section from notes
publish methods               # Generate methods from code + notes
publish figures               # Catalog figures with captions
publish bibliography          # Extract citations from notes

# Natural Language (UI)
"What notes do I have about Bayesian inference?"
"Create a teaching example for this algorithm"
"Draft the methods section based on my analysis code"
"What papers should I cite for this approach?"
```

### Workflow: Research → Code → Paper

```
┌─────────────────────────────────────────────────────────────┐
│ SCENARIO: Writing a methods section                         │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│ Step 1: Find relevant knowledge                             │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ You: research context "optimization algorithms"          │ │
│ │                                                          │ │
│ │ Bridge: Found 12 notes across 2 vaults:                  │ │
│ │   📝 gradient_descent.md (PageRank: 0.89)               │ │
│ │   📝 adam_optimizer.md (PageRank: 0.76)                 │ │
│ │   📝 hyperparameter_tuning.md (PageRank: 0.71)          │ │
│ │   🔗 Links to: analysis/train_model.py                  │ │
│ └─────────────────────────────────────────────────────────┘ │
│                                                              │
│ Step 2: Connect code to theory                              │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ You: research link analysis/train_model.py              │ │
│ │                                                          │ │
│ │ Bridge: Linked code to notes:                           │ │
│ │   Line 45-89: Uses Adam optimizer                       │ │
│ │   → See: adam_optimizer.md                              │ │
│ │   → Citation: Kingma & Ba, 2014                         │ │
│ └─────────────────────────────────────────────────────────┘ │
│                                                              │
│ Step 3: Draft methods section                               │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ You: publish draft methods                               │ │
│ │                                                          │ │
│ │ Bridge: Generated draft (450 words):                     │ │
│ │                                                          │ │
│ │ "## Methods                                              │ │
│ │                                                          │ │
│ │ ### Optimization                                         │ │
│ │ We employed the Adam optimizer (Kingma & Ba, 2014)      │ │
│ │ with learning rate η=0.001 and momentum β₁=0.9,         │ │
│ │ β₂=0.999 (see train_model.py:45-89).                    │ │
│ │                                                          │ │
│ │ [Draft saved to: 02_Drafts/methods_v1.md]"              │ │
│ └─────────────────────────────────────────────────────────┘ │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### Workflow: Code → Teaching Materials

```
┌─────────────────────────────────────────────────────────────┐
│ SCENARIO: Creating lecture materials                        │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│ You: teach example "gradient descent" --level beginner      │
│                                                              │
│ Bridge: Generated teaching example from your notes:         │
│                                                              │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ # Gradient Descent: A Simple Example                    │ │
│ │                                                          │ │
│ │ ## Intuition (from your note: gradient_descent.md)      │ │
│ │ Imagine you're blindfolded on a hill...                 │ │
│ │                                                          │ │
│ │ ## Code Example                                          │ │
│ │ ```python                                                │ │
│ │ def gradient_descent(f, x0, lr=0.01, steps=100):        │ │
│ │     x = x0                                               │ │
│ │     for _ in range(steps):                               │ │
│ │         x = x - lr * gradient(f, x)                      │ │
│ │     return x                                             │ │
│ │ ```                                                      │ │
│ │                                                          │ │
│ │ ## Practice Questions                                    │ │
│ │ 1. What happens if lr is too large?                     │ │
│ │ 2. When would gradient descent fail?                    │ │
│ │                                                          │ │
│ │ [Saved to: Teaching/gradient_descent_example.md]        │ │
│ └─────────────────────────────────────────────────────────┘ │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### Integration with obs r-dev

```bash
# Seamless integration with existing R-Dev workflow
obs r link research_vault          # Link R project
obs r context "machine learning"   # Existing command

# New Research Bridge extensions
research sync                      # Sync code artifacts to notes
research changelog                 # Generate research log entry
research timeline                  # Visualize research progress
```

---

## Plugin 3: Code Scaffold 🏗️

### Concept: Three-Layer Auto-Generation

Understands your three-layer architecture and auto-generates boilerplate, tests, and documentation when you define new features.

### Workflow Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    CODE SCAFFOLD                             │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  INPUT: Define feature in Core layer                        │
│  ┌─────────────────────────────────────────────────────────┐│
│  │ # vault_manager.py                                      ││
│  │ def archive_vault(self, vault_id: int) -> bool:        ││
│  │     """Archive a vault (hide from listings)"""         ││
│  │     ...                                                 ││
│  └─────────────────────────────────────────────────────────┘│
│                          │                                   │
│                          ▼                                   │
│  ┌─────────────────────────────────────────────────────────┐│
│  │              CODE SCAFFOLD ENGINE                        ││
│  │                                                          ││
│  │  Analyzes:                                               ││
│  │  - Method signature                                      ││
│  │  - Docstring                                             ││
│  │  - Return type                                           ││
│  │  - Similar patterns in codebase                          ││
│  └─────────────────────────────────────────────────────────┘│
│                          │                                   │
│          ┌───────────────┼───────────────┐                  │
│          ▼               ▼               ▼                  │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐        │
│  │ CLI Layer    │ │ TUI Layer    │ │ Tests        │        │
│  │              │ │              │ │              │        │
│  │ obs_cli.py   │ │ screens/     │ │ test_*.py    │        │
│  │ + argparse   │ │ vault.py     │ │ + fixtures   │        │
│  │ + help text  │ │ + keybinding │ │ + mocks      │        │
│  └──────────────┘ └──────────────┘ └──────────────┘        │
│          │               │               │                  │
│          └───────────────┼───────────────┘                  │
│                          ▼                                   │
│  ┌─────────────────────────────────────────────────────────┐│
│  │ OUTPUT: Complete feature implementation                  ││
│  │                                                          ││
│  │ ✅ CLI: obs vault archive <id>                          ││
│  │ ✅ TUI: 'a' key in vault browser                        ││
│  │ ✅ Tests: 8 test cases generated                        ││
│  │ ✅ Docs: Command reference updated                       ││
│  └─────────────────────────────────────────────────────────┘│
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### Commands (CLI + UI)

```bash
# Scaffold Commands
scaffold feature <name>       # Generate full feature from core method
scaffold cli <method>         # Generate CLI command only
scaffold tui <method>         # Generate TUI binding only
scaffold test <method>        # Generate test suite only
scaffold docs <method>        # Generate documentation only

# Analysis Commands
scaffold analyze              # Analyze codebase patterns
scaffold diff                 # Show what would be generated
scaffold validate             # Check architecture consistency

# Fix Commands
scaffold fix-tests            # Auto-fix failing tests
scaffold sync                 # Sync all layers with core

# Natural Language (UI)
"Generate CLI for this method"
"Add TUI keybinding for archive_vault"
"Create tests for the new feature"
"What's missing from the three-layer implementation?"
```

### Workflow: Core → Full Feature

```
┌─────────────────────────────────────────────────────────────┐
│ SCENARIO: Adding a new feature                              │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│ Step 1: Define in Core (you write this)                     │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ # core/vault_manager.py                                  │ │
│ │                                                          │ │
│ │ def archive_vault(self, vault_id: int) -> bool:         │ │
│ │     """Archive a vault to hide from listings.           │ │
│ │                                                          │ │
│ │     Args:                                                │ │
│ │         vault_id: The vault to archive                   │ │
│ │                                                          │ │
│ │     Returns:                                             │ │
│ │         True if archived successfully                    │ │
│ │     """                                                  │ │
│ │     vault = self.db.get_vault(vault_id)                 │ │
│ │     if not vault:                                        │ │
│ │         return False                                     │ │
│ │     return self.db.update_vault(vault_id, archived=True)│ │
│ └─────────────────────────────────────────────────────────┘ │
│                                                              │
│ Step 2: Run scaffold                                        │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ You: scaffold feature archive_vault                      │ │
│ │                                                          │ │
│ │ Scaffold: Analyzing method signature...                  │ │
│ │                                                          │ │
│ │ Will generate:                                           │ │
│ │ ┌─────────────────────────────────────────────────────┐ │ │
│ │ │ CLI (obs_cli.py):                                    │ │ │
│ │ │   Subcommand: vault archive <vault_id>               │ │ │
│ │ │   Help: "Archive a vault to hide from listings"     │ │ │
│ │ │   Args: vault_id (required, int)                     │ │ │
│ │ └─────────────────────────────────────────────────────┘ │ │
│ │ ┌─────────────────────────────────────────────────────┐ │ │
│ │ │ TUI (screens/vault_browser.py):                      │ │ │
│ │ │   Keybinding: 'a' (archive selected vault)           │ │ │
│ │ │   Confirmation dialog: "Archive {vault.name}?"       │ │ │
│ │ │   Status message: "Vault archived"                   │ │ │
│ │ └─────────────────────────────────────────────────────┘ │ │
│ │ ┌─────────────────────────────────────────────────────┐ │ │
│ │ │ Tests (test_vault_manager.py):                       │ │ │
│ │ │   test_archive_vault_success                         │ │ │
│ │ │   test_archive_vault_not_found                       │ │ │
│ │ │   test_archive_vault_already_archived                │ │ │
│ │ │   test_archive_vault_cli_integration                 │ │ │
│ │ └─────────────────────────────────────────────────────┘ │ │
│ │                                                          │ │
│ │ Proceed? [Y/n]                                          │ │
│ └─────────────────────────────────────────────────────────┘ │
│                                                              │
│ Step 3: Review generated code                               │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ Scaffold: Generated 4 files:                             │ │
│ │                                                          │ │
│ │ ✅ src/python/obs_cli.py (+15 lines)                    │ │
│ │ ✅ src/python/tui/screens/vault_browser.py (+22 lines)  │ │
│ │ ✅ src/python/tests/test_vault_manager.py (+45 lines)   │ │
│ │ ✅ docs/user/commands.md (+8 lines)                     │ │
│ │                                                          │ │
│ │ Run tests? [Y/n]                                        │ │
│ └─────────────────────────────────────────────────────────┘ │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### Auto-Fix Failing Tests

```
┌─────────────────────────────────────────────────────────────┐
│ SCENARIO: Fixing test failures after refactor              │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│ You: scaffold fix-tests                                     │
│                                                              │
│ Scaffold: Analyzing 53 test failures...                     │
│                                                              │
│ Found patterns:                                              │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ Pattern 1: Mock data type mismatch (27 failures)        │ │
│ │   Files: test_note_explorer.py                          │ │
│ │   Issue: Using dict instead of Note objects             │ │
│ │   Fix: Convert mock_notes to Note instances             │ │
│ │                                                          │ │
│ │ Pattern 2: Method signature change (14 failures)        │ │
│ │   Files: test_graph_visualizer.py                       │ │
│ │   Issue: get_graph() now requires vault_id              │ │
│ │   Fix: Add vault_id parameter to mock calls             │ │
│ │                                                          │ │
│ │ Pattern 3: Missing fixtures (12 failures)               │ │
│ │   Files: test_vault_scanner.py, test_quick_wins.py      │ │
│ │   Issue: Tests missing shared fixtures                  │ │
│ │   Fix: Add imports from conftest.py                     │ │
│ └─────────────────────────────────────────────────────────┘ │
│                                                              │
│ Apply fixes? [All/Select/None]                              │
│                                                              │
│ You: all                                                    │
│                                                              │
│ Scaffold: Applying fixes...                                 │
│   ✅ Fixed 27 failures in test_note_explorer.py            │
│   ✅ Fixed 14 failures in test_graph_visualizer.py         │
│   ✅ Fixed 12 failures in other files                      │
│                                                              │
│ Running pytest...                                           │
│   ✅ 451/461 tests passing (98% pass rate)                 │
│   ⚠️  10 failures remaining (need manual review)           │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## Implementation Comparison

| Aspect | Focus Flow | Research Bridge | Code Scaffold |
|--------|------------|-----------------|---------------|
| **Primary User** | Developer with ADHD | Researcher/Teacher | Developer |
| **Main Value** | Momentum & context | Knowledge connection | Speed & consistency |
| **Complexity** | Medium | High | Medium |
| **Dependencies** | Git, .STATUS | Obsidian vaults, AI | AST parsing |
| **Effort to Build** | 2-3 weeks | 4-6 weeks | 3-4 weeks |

---

## Recommended Implementation Order

### Phase 1: Focus Flow (Weeks 1-3)
**Why first**: Immediate value, builds on existing session-wrap skill

```
Week 1: Context restore + task breakdown
Week 2: Momentum tracking + bookmarks
Week 3: Integration + polish
```

### Phase 2: Code Scaffold (Weeks 4-7)
**Why second**: Directly helps with current test failures

```
Week 4: AST analysis + pattern detection
Week 5: CLI/TUI generation
Week 6: Test generation
Week 7: Auto-fix capabilities
```

### Phase 3: Research Bridge (Weeks 8-13)
**Why third**: Builds on Focus Flow + Code Scaffold

```
Week 8-9: Obsidian integration
Week 10-11: Teaching material generation
Week 12-13: Publication pipeline
```

---

## Technical Architecture

### Shared Components

```
┌─────────────────────────────────────────────────────────────┐
│                    PLUGIN ARCHITECTURE                       │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌─────────────────────────────────────────────────────────┐│
│  │                    CLAUDE INTERFACE                      ││
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ││
│  │  │ CLI Commands │  │ Slash Cmds   │  │ Natural Lang │  ││
│  │  │ (focus, etc) │  │ (/focus)     │  │ (UI chat)    │  ││
│  │  └──────────────┘  └──────────────┘  └──────────────┘  ││
│  └─────────────────────────────────────────────────────────┘│
│                          │                                   │
│                          ▼                                   │
│  ┌─────────────────────────────────────────────────────────┐│
│  │                   PLUGIN CORE                            ││
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ││
│  │  │ Focus Flow   │  │ Research     │  │ Code         │  ││
│  │  │ Engine       │  │ Bridge       │  │ Scaffold     │  ││
│  │  └──────────────┘  └──────────────┘  └──────────────┘  ││
│  └─────────────────────────────────────────────────────────┘│
│                          │                                   │
│                          ▼                                   │
│  ┌─────────────────────────────────────────────────────────┐│
│  │                 SHARED SERVICES                          ││
│  │  ┌────────────┐  ┌────────────┐  ┌────────────┐        ││
│  │  │ Context    │  │ Obsidian   │  │ Code       │        ││
│  │  │ Manager    │  │ API        │  │ Analyzer   │        ││
│  │  └────────────┘  └────────────┘  └────────────┘        ││
│  │  ┌────────────┐  ┌────────────┐  ┌────────────┐        ││
│  │  │ Git        │  │ AI Router  │  │ Template   │        ││
│  │  │ Integration│  │ (existing) │  │ Engine     │        ││
│  │  └────────────┘  └────────────┘  └────────────┘        ││
│  └─────────────────────────────────────────────────────────┘│
│                          │                                   │
│                          ▼                                   │
│  ┌─────────────────────────────────────────────────────────┐│
│  │                    DATA LAYER                            ││
│  │  ┌────────────┐  ┌────────────┐  ┌────────────┐        ││
│  │  │ SQLite DB  │  │ File       │  │ Git        │        ││
│  │  │ (existing) │  │ System     │  │ History    │        ││
│  │  └────────────┘  └────────────┘  └────────────┘        ││
│  └─────────────────────────────────────────────────────────┘│
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### File Structure

```
.claude/
├── plugins/
│   ├── focus-flow/
│   │   ├── engine.py          # Core logic
│   │   ├── context.py         # Context management
│   │   ├── momentum.py        # Streak tracking
│   │   └── commands.md        # Slash commands
│   │
│   ├── research-bridge/
│   │   ├── engine.py          # Core logic
│   │   ├── obsidian.py        # Vault integration
│   │   ├── teaching.py        # Teaching materials
│   │   ├── publish.py         # Publication helpers
│   │   └── commands.md        # Slash commands
│   │
│   └── code-scaffold/
│       ├── engine.py          # Core logic
│       ├── analyzer.py        # AST analysis
│       ├── generator.py       # Code generation
│       ├── templates/         # Code templates
│       └── commands.md        # Slash commands
│
├── focus/                     # Focus Flow data
│   ├── current.json          # Active context
│   ├── bookmarks/            # Saved contexts
│   └── momentum.json         # Streak data
│
└── sessions/                  # Existing session data
```

---

## Quick Start: Focus Flow MVP

### Minimum Viable Plugin (1 week)

```python
# .claude/plugins/focus-flow/engine.py

class FocusFlow:
    """ADHD-friendly momentum keeper."""

    def start(self):
        """Begin focused session with context restore."""
        context = self.load_last_context()
        if context:
            print(f"📍 Last session: {context['task']}")
            print(f"   Progress: {context['progress']}")

        tasks = self.get_next_tasks()
        print(f"\n🎯 Focus list:")
        for task in tasks[:3]:
            print(f"   □ {task}")

    def done(self):
        """Mark current task complete."""
        self.update_momentum()
        print(f"✅ Task complete! Momentum: {'🔥' * self.streak}")

    def stuck(self):
        """Get unstuck suggestions."""
        suggestions = self.analyze_blockers()
        print("💡 Try one of these:")
        for s in suggestions:
            print(f"   → {s}")

    def wrap(self):
        """End session with summary."""
        summary = self.generate_summary()
        self.save_session(summary)
        print(summary)
```

### Slash Command Definition

```markdown
# .claude/commands/focus.md

Start a focused work session with ADHD-friendly guidance.

## Usage
/focus [start|done|stuck|wrap|status]

## Subcommands
- start: Begin session, restore context
- done: Mark task complete, show next
- stuck: Get unstuck suggestions
- wrap: End session with summary
- status: Show current momentum

## Examples
/focus start     # "Welcome back! You were working on..."
/focus done      # "✅ Task complete! Momentum: 🔥🔥🔥"
/focus stuck     # "💡 Try: break into smaller steps"
/focus wrap      # Generate session summary
```

---

## Summary

| Plugin | Best For | Key Benefit |
|--------|----------|-------------|
| **Focus Flow** | Daily development | Never lose context or momentum |
| **Research Bridge** | Academic work | Seamless knowledge → publication |
| **Code Scaffold** | Feature development | 10x faster three-layer implementation |

**Recommendation**: Start with **Focus Flow** - it directly addresses ADHD needs, builds on your existing session-wrap skill, and provides immediate value with relatively low implementation effort.

---

*Generated for obsidian-cli-ops project - December 2025*
