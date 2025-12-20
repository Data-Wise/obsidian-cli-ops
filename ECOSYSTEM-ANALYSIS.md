# 🌐 Dev-Tools Ecosystem Analysis

> **Purpose:** Map the dev-tools landscape to identify overlaps and opportunities
> **Date:** 2025-12-20

---

## 📊 Current Ecosystem Map

```
~/projects/dev-tools/
│
├── 🎯 CORE TOOLS (Established)
│   ├── zsh-configuration     # Shell workflow manager
│   ├── aiterm                 # Terminal optimizer for AI dev
│   └── spacemacs-rstats       # Emacs config for R
│
├── 🤖 AI/LLM TOOLS
│   ├── claude-mcp             # Browser extension for MCP
│   ├── claude-statistical-research  # Statistical research MCP server
│   └── mcp-servers/           # Collection of MCP servers
│
├── 📝 KNOWLEDGE MANAGEMENT
│   ├── obsidian-cli-ops       # ⭐ THIS PROJECT
│   └── (potential: note-tools?)
│
├── 🛠️ UTILITIES
│   ├── zsh-claude-workflow    # Shell automation for Claude
│   ├── apple-notes-sync       # Dashboard sync
│   └── workspace-auditor      # Workspace health checker
│
└── 📦 INFRASTRUCTURE
    ├── homebrew-tap           # Custom formulae
    ├── data-wise.github.io    # GitHub Pages site
    └── dev-planning           # Development planning hub
```

---

## 🔍 Tool-by-Tool Analysis

### 1. **zsh-configuration** (Shell Workflow Manager)

**Purpose:** Manage development workflows with smart dispatchers

**Core Features:**
- 28 curated aliases (was 179, reduced 84%)
- 6 smart dispatchers (`work`, `pp`, `dash`, etc.)
- Project context detection
- ADHD-friendly design

**Scope:**
- Shell integration
- Workflow orchestration
- Project switching
- Git operations (via plugins)

**Status:** ✅ Stable, Phase 2 complete

**Overlap with obs:**
- ❌ Work session management (removed from obs)
- ❌ Project context (removed from obs)
- ❌ Git operations (obs should focus on vaults only)

---

### 2. **aiterm** (Terminal Optimizer)

**Purpose:** Optimize iTerm2 for AI-assisted development

**Core Features:**
- Context-aware terminal profiles
- iTerm2 profile switching
- Claude Code hook management
- MCP server control
- Auto-approval configuration

**Scope:**
- iTerm2 integration
- Terminal appearance
- Claude Code settings
- Context detection

**Status:** ✅ Active development

**Overlap with obs:**
- ✅ AI providers (shared infrastructure)
- ❌ Terminal management (aiterm only)
- ❌ Profile switching (aiterm only)
- ⚠️ Context detection (different contexts: aiterm=terminal, obs=vaults)

---

### 3. **obsidian-cli-ops** (Current State)

**Purpose:** Multi-vault Obsidian knowledge management

**Core Features:**
- Vault discovery and scanning
- Knowledge graph analysis
- AI-powered features (similarity, duplicates)
- Interactive TUI
- R-Dev integration

**Scope:** ⚠️ **TOO BROAD**
- Vault management ✅ (keep)
- Graph analysis ✅ (keep)
- AI features ✅ (keep)
- TUI ❌ (too much overhead)
- R-Dev ❌ (wrong domain)
- Workflow management ❌ (zsh-configuration does this)

**Status:** 🟡 Needs refocusing

---

## 🎯 Proposed Ecosystem After Refocus

```
~/projects/dev-tools/
│
├── 🎯 WORKFLOW ORCHESTRATION
│   ├── zsh-configuration     # Shell workflows, project switching
│   └── aiterm                # Terminal optimization, Claude integration
│
├── 📝 CONTENT MANAGEMENT
│   ├── obsidian-cli-ops     # ⭐ Obsidian vault management + AI
│   └── project-hub/          # Master planning hub
│
├── 🤖 AI INFRASTRUCTURE (Shared)
│   ├── claude-mcp            # Browser MCP
│   ├── statistical-research  # Research MCP server
│   └── mcp-servers/          # MCP collection
│
└── 🛠️ UTILITIES
    └── (existing utilities)
```

**Key Changes:**
1. **Clear boundaries** - Each tool has distinct purpose
2. **No overlap** - Workflow (zsh), Terminal (aiterm), Vaults (obs)
3. **Shared infrastructure** - AI providers used by multiple tools
4. **Integration points** - Tools coordinate but don't duplicate

---

## 🔗 Integration Points

### obs ↔ zsh-configuration

**Current Overlap:** ❌ Both try to manage workflows

**Proposed Integration:**
```bash
# zsh-configuration provides project context
work research              # Sets up environment

# obs operates within that context
obs scan                   # Scans the vault in current context
obs refactor               # Refactors notes in current vault
```

**Integration Design:**
- `zsh-configuration`: Detects project type, sets environment
- `obs`: Operates on Obsidian vaults only
- No duplicate commands

---

### obs ↔ aiterm

**Current Overlap:** ⚠️ Both use AI providers

**Proposed Integration:**
```bash
# aiterm manages terminal and Claude Code
ait claude settings        # Configure Claude

# obs uses AI for vault operations
obs refactor               # Uses same AI providers
obs analyze                # Leverages shared infrastructure
```

**Integration Design:**
- **Shared:** AI provider configuration
- **aiterm:** Terminal profiles, hooks, approvals
- **obs:** Note operations, vault analysis
- **Coordination:** Both read from same config location

---

### obs ↔ project-hub

**Current Overlap:** ❌ None (good!)

**Proposed Integration:**
```bash
# project-hub tracks projects
cat ~/projects/project-hub/PROJECT-HUB.md

# obs syncs vault data to hub
obs hub sync                      # Bi-directional sync
obs hub export research           # Export research notes
obs project-notes mediation-planning  # Notes for project
```

**Integration Design:**
- `project-hub`: Master dashboard, weekly planning
- `obs`: Note management, content extraction
- **Flow:** Notes → obs analysis → project-hub status

---

## 📋 Feature Matrix

| Feature | zsh-config | aiterm | obs (current) | obs (proposed) |
|---------|-----------|--------|---------------|----------------|
| **Workflow Management** |
| Project switching | ✅ | ❌ | ⚠️ (R-Dev) | ❌ |
| Work sessions | ✅ | ❌ | ❌ | ❌ |
| Git operations | ✅ (plugin) | ❌ | ❌ | ❌ |
| **Terminal** |
| Profile switching | ❌ | ✅ | ❌ | ❌ |
| Context detection | ✅ (project) | ✅ (terminal) | ❌ | ❌ |
| iTerm2 control | ❌ | ✅ | ❌ | ❌ |
| **AI Integration** |
| Provider config | ❌ | ✅ | ✅ | ✅ |
| Claude Code hooks | ❌ | ✅ | ❌ | ❌ |
| Content analysis | ❌ | ❌ | ✅ | ✅ |
| **Obsidian** |
| Vault scanning | ❌ | ❌ | ✅ | ✅ |
| Graph analysis | ❌ | ❌ | ✅ | ✅ |
| Note refactoring | ❌ | ❌ | ⚠️ (basic) | ✅ (advanced) |
| Structure suggestions | ❌ | ❌ | ❌ | ✅ |

**Key:**
- ✅ Core feature
- ⚠️ Partial/weak implementation
- ❌ Not in scope

---

## 🎨 Design Principles for Each Tool

### zsh-configuration
**Principle:** "Minimal, memorable commands for maximum workflow efficiency"
- Focus: Shell operations
- Style: Aliases and functions
- Target: Daily development tasks
- Philosophy: Muscle memory over documentation

### aiterm
**Principle:** "Optimize the terminal for AI-assisted development"
- Focus: Terminal appearance and Claude integration
- Style: CLI for configuration, automatic for runtime
- Target: Terminal environment optimization
- Philosophy: Context-aware automation

### obsidian-cli-ops (Proposed)
**Principle:** "AI-powered vault management and note organization"
- Focus: Obsidian vaults only
- Style: CLI with rich output
- Target: Knowledge management tasks
- Philosophy: AI does analysis, human approves actions

---

## 🚫 Anti-Overlap Rules

### Rule 1: One Tool, One Domain
- **zsh-configuration:** Shell workflows
- **aiterm:** Terminal environment
- **obs:** Obsidian vaults

### Rule 2: Coordinate, Don't Duplicate
- If feature exists in another tool → use it
- If feature spans tools → integration point
- If feature is unique → implement once

### Rule 3: Share Infrastructure, Not Logic
- ✅ **Shared:** AI provider configs, color schemes, standards
- ❌ **Not Shared:** Business logic, commands, workflows

### Rule 4: Integration Over Combination
- Tools should integrate via:
  - Shared config files
  - Standard output formats
  - Clear APIs
  - Environment variables
- Not via:
  - Calling each other's commands
  - Shared codebases
  - Tight coupling

---

## 📈 Growth Strategy

### Short-term (1-3 months)
**Focus:** Establish clear boundaries

1. **obs:** Remove overlaps, focus on vaults
2. **zsh-configuration:** Mature shell workflows
3. **aiterm:** Terminal optimization features

**Goal:** Each tool has distinct, valuable purpose

### Medium-term (3-6 months)
**Focus:** Integration points

1. **obs ↔ project-hub:** Sync mechanism
2. **zsh-config ↔ aiterm:** Context sharing
3. **All tools:** Shared AI provider config

**Goal:** Tools work together seamlessly

### Long-term (6-12 months)
**Focus:** Ecosystem maturity

1. Standardize config formats
2. Document integration patterns
3. Create unified documentation
4. Potential: dev-tools CLI (`dt <tool> <command>`)

**Goal:** Coherent ecosystem, not collection of tools

---

## 🎯 Refocusing Impact

### Before (Current State)
```
obsidian-cli-ops:
├── Vault management (✅ core)
├── Graph analysis (✅ core)
├── AI features (✅ core)
├── TUI (❌ 1,701 lines, limited value)
├── R-Dev (❌ wrong domain)
└── Sync (❌ overlaps with Obsidian native)

Total: ~11,500 lines, unclear purpose
```

### After (Proposed)
```
obsidian-cli-ops:
├── Vault scanning & health
├── AI-powered refactoring
├── Note operations (merge, split, improve)
├── Structure suggestions
├── Project-hub integration
└── Cross-vault analysis

Total: ~4,000-5,000 lines, laser-focused
```

**Reduction:** 60% code reduction, 10x clearer purpose

---

## 💡 Quick Decision Framework

When adding a feature to obs, ask:

1. **Domain Check**
   - ❓ Is this about Obsidian vaults?
   - ✅ Yes → Consider adding
   - ❌ No → Wrong tool

2. **Overlap Check**
   - ❓ Does zsh-configuration or aiterm do this?
   - ✅ Yes → Don't add, integrate instead
   - ❌ No → Proceed

3. **Value Check**
   - ❓ Would AI assistance make this 10x better?
   - ✅ Yes → Good fit for obs
   - ❌ No → Consider if worth adding

4. **Complexity Check**
   - ❓ Is this worth the maintenance burden?
   - ✅ Yes → Add with tests
   - ❌ No → Skip or simplify

**Example:**
- "Add git integration" → ❌ (zsh-configuration does this)
- "AI-powered note merging" → ✅ (unique to obs, high value)
- "Terminal profile switching" → ❌ (aiterm does this)
- "Cross-vault search" → ✅ (unique to obs)

---

## 🎨 Visual Ecosystem After Refocus

```
┌─────────────────────────────────────────────────┐
│         DEVELOPMENT WORKFLOW                    │
│                                                 │
│  ┌───────────────┐      ┌──────────────┐       │
│  │ zsh-config    │      │  aiterm      │       │
│  │ ────────────  │      │  ─────────── │       │
│  │ • work        │      │ • Profiles   │       │
│  │ • pp          │      │ • Context    │       │
│  │ • dash        │      │ • Hooks      │       │
│  │ • Git ops     │      │ • Claude cfg │       │
│  └───────────────┘      └──────────────┘       │
│         ▲                      ▲                │
│         │                      │                │
│         └──────────────────────┘                │
│                 │                               │
│                 ▼                               │
│         Shared Configs                          │
│         (AI providers, colors)                  │
│                 │                               │
│                 ▼                               │
│  ┌────────────────────────────────────┐        │
│  │  obsidian-cli-ops                  │        │
│  │  ──────────────────────────────    │        │
│  │  • Vault operations                │        │
│  │  • AI refactoring                  │        │
│  │  • Note analysis                   │        │
│  │  • Structure suggestions           │        │
│  │  • Hub integration                 │        │
│  └──────────────┬─────────────────────┘        │
│                 │                               │
│                 ▼                               │
│  ┌────────────────────────────────────┐        │
│  │  project-hub                       │        │
│  │  ────────────────────────────────  │        │
│  │  • Master dashboard                │        │
│  │  • Weekly planning                 │        │
│  │  • Cross-domain tracking           │        │
│  └────────────────────────────────────┘        │
└─────────────────────────────────────────────────┘
```

**Data Flow:**
1. User runs `work research` (zsh-config)
2. Terminal changes profile (aiterm)
3. User operates on vault: `obs refactor` (obs)
4. Results sync to project-hub: `obs hub sync` (obs → hub)

**Clean separation, clear integration points!**

---

## 📝 Recommendations

### Immediate Actions (This Week)
1. ✅ Accept ecosystem boundaries
2. ✅ Remove TUI from obs (1,701 lines)
3. ✅ Remove R-Dev from obs (move to mediation-planning)
4. ✅ Update documentation to reflect new scope

### Short-term (2-4 Weeks)
1. Implement core AI features in obs
2. Establish integration points
3. Document coordination patterns
4. Create shared config standards

### Medium-term (1-3 Months)
1. Mature each tool in its domain
2. Implement cross-tool integrations
3. Standardize interfaces
4. Consider meta-CLI (optional)

---

**Key Insight:** The ecosystem is healthier with focused tools that integrate, rather than one tool trying to do everything.

---

*Created: 2025-12-20*
*Purpose: Map ecosystem to guide obsidian-cli-ops refocusing*
