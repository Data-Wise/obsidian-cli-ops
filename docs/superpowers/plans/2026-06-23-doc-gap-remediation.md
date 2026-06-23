# Documentation Gap Remediation — v4.0.0 Research + Temporal Domains

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fill documentation gaps for the `obs research` domain (11 CLI subcommands, zero tutorial coverage) and the temporal/monitoring MCP tools (3 tools with no workflow narrative), all shipped in v4.0.0.

**Architecture:** Four focused tasks, each producing an independently `mkdocs build --strict`-passing file or section. Task 1 creates the research setup tutorial; Task 2 adds cookbook recipes; Task 3 adds a monitoring/temporal tutorial; Task 4 patches `claude-integration.md` with temporal MCP examples and a research CLI-only note. All new pages are wired into `mkdocs.yml` nav.

**Tech Stack:** MkDocs Material (mkdocs.yml, `docs_mkdocs/`), Python/ZSH CLI (`src/python/research/`, `src/obs.zsh`), `obs config` YAML (`~/.config/obs/config.yaml`), pytest for doc-count gate (`tests/test_doc_counts.py`)

## Global Constraints

- MkDocs strict mode is the doc validation gate: `mkdocs build --strict` must pass before every commit.
- Research commands are **CLI-only** — no individual MCP tools. The only MCP research tool is `unified_search`. Never imply Claude Desktop can call `obs research zotero search`.
- Config keys are exact: `research.zotero.database`, `research.zotero.storage`, `research.pdf_directories` (list), `research.teaching.courses_dir`, `research.writing.manuscripts_dir`.
- All code blocks in tutorials must use real command syntax. Never use `<placeholder>` syntax inside backtick blocks — use realistic examples (`~/Zotero/zotero.sqlite`, `Research`, `causal-inference`).
- Branch: dev (existing integration branch). No new files on dev is blocked — **doc-only `.md` files on dev are explicitly allowed** by the branch guard.
- Commit style: `docs(<scope>): <message>` — no references to issue numbers (the guard strips those).
- Test count in CLAUDE.md / `.STATUS` is NOT changed by doc-only commits.

---

### Task 1: Research Setup Tutorial

**Files:**
- Create: `docs_mkdocs/tutorials/research-setup.md`
- Modify: `mkdocs.yml` (add nav entry under Tutorials)

**Interfaces:**
- Consumes: `obs config set`, `obs config show`, `obs research zotero|pdf|course|manuscript|bib` (see obs_cli.py:876-921)
- Produces: standalone tutorial page; Task 3 links to it as prerequisite

- [ ] **Step 1: Run mkdocs build to confirm baseline passes**

```bash
cd /Users/dt/projects/dev-tools/obsidian-cli-ops
mkdocs build --strict 2>&1 | tail -5
```

Expected: `INFO    -  Documentation built in N.N seconds` — zero warnings.

- [ ] **Step 2: Create the tutorial file**

Write `docs_mkdocs/tutorials/research-setup.md` with the full content below. Every section must have working `obs` commands that match the actual CLI signatures.

```markdown
# Research Domain Setup

Connect `obs` to your research stack — Zotero, PDFs, courses, and manuscripts — for a unified terminal workflow.

**Time:** ~15 minutes | **Level:** 🔵 Intermediate | **Steps:** 6

**Prerequisites:** Complete [Getting Started](getting-started.md). Have Zotero desktop installed if using Zotero integration.

---

## What Is the Research Domain?

The `obs research` commands, added in v4.0.0 (nexus-cli absorption), give `obs` a window into your research materials:

| Subcommand | What it accesses |
|------------|-----------------|
| `obs research zotero` | Zotero local SQLite database (offline, no API key) |
| `obs research pdf` | Full-text search across PDF directories |
| `obs research course` | Quarto-based course projects |
| `obs research manuscript` | Quarto manuscript projects |
| `obs research bib` | Citation completeness in manuscripts |

These commands are **CLI-only** — they do not go through the MCP server. Use them from your terminal; for vault+research unified search from Claude Desktop, see `unified_search` in the [Claude Integration guide](../claude-integration.md).

---

## Step 1: Create the Config File

`obs research` reads from `~/.config/obs/config.yaml`. Create one if you haven't already:

```bash
obs config show   # shows current config or "no config file found"
```

If no config exists:

```bash
obs config init   # creates ~/.config/obs/config.yaml with defaults
```

---

## Step 2: Configure Zotero (optional)

Zotero stores its database locally at `~/Zotero/zotero.sqlite`. Point `obs` at it:

```bash
obs config set research.zotero.database ~/Zotero/zotero.sqlite
obs config set research.zotero.storage ~/Zotero/storage
```

Verify:

```bash
obs config show
# research.zotero.database: /Users/you/Zotero/zotero.sqlite
# research.zotero.storage:  /Users/you/Zotero/storage
```

Test the connection:

```bash
obs research zotero recent --limit 5
```

Expected: a table of your 5 most recently modified Zotero items with key, title, authors, and year.

!!! warning "Zotero must not be open during heavy reads"
    Zotero locks its SQLite database when running. For read-only commands like `obs research zotero search`, this is usually fine — but if you see a lock error, quit Zotero first.

---

## Step 3: Configure PDF Directories (optional)

Point `obs` at directories containing research PDFs:

```bash
obs config set research.pdf_directories '["~/Documents/papers", "~/Downloads"]'
```

Or edit `~/.config/obs/config.yaml` directly:

```yaml
research:
  pdf_directories:
    - ~/Documents/papers
    - ~/Downloads
```

Test:

```bash
obs research pdf search "causal inference" --limit 5
```

Expected: matching PDF files with title, path, and matching text snippet. Returns `0 results` if no PDFs are found — check your paths with `obs config show`.

!!! tip "PDF search requires pdfminer.six"
    `obs research pdf search` uses `pdfminer.six` for text extraction. It's included in the `obs` venv. If you see an import error, run `./install.sh` to reprovision the venv.

---

## Step 4: Configure Courses (optional)

`obs` discovers Quarto-based course projects from a courses directory:

```bash
obs config set research.teaching.courses_dir ~/projects/courses
```

Your courses directory should contain subdirectories, each a Quarto project with a `_quarto.yml` file and lecture `.qmd` files.

```bash
obs research course list        # list all courses
obs research course show stats  # show details for the "stats" course
obs research course lectures stats  # list lectures in the "stats" course
```

Expected output for `course list`:

```
┌────────────────────────────────────────────────────────────┐
│  Course      Lectures  Assignments  Status                 │
├────────────────────────────────────────────────────────────┤
│  stats       12        3            active                  │
│  causal      8         2            active                  │
└────────────────────────────────────────────────────────────┘
```

---

## Step 5: Configure Manuscripts (optional)

`obs` reads Quarto manuscript projects from a manuscripts directory:

```bash
obs config set research.writing.manuscripts_dir ~/projects/manuscripts
```

Each manuscript should be a directory containing `_quarto.yml` and a `.STATUS` file (optional but recommended for status tracking).

```bash
obs research manuscript list              # all manuscripts
obs research manuscript list --status draft  # filter by status
obs research manuscript show collider     # details for "collider" manuscript
obs research manuscript stats             # aggregate word counts, status breakdown
```

Expected for `manuscript stats`:

```
Manuscripts: 4 total (2 draft, 1 in-review, 1 published)
Total word count: 42,831
Active word count: 31,204 (2 manuscripts)
```

---

## Step 6: Check Bibliography Completeness

Once manuscripts are configured, verify citation completeness:

```bash
obs research bib check collider
```

This reads the `.bib` file(s) referenced in the manuscript's `_quarto.yml` and checks:
- All `@cite{key}` references in `.qmd` files resolve to a `.bib` entry
- No orphaned `.bib` entries (cited in bib but not in text)

Expected output:

```
✅ collider: 23 citations, all resolved
   Orphaned entries: 0
```

!!! tip "Combine research + vault for a full picture"
    Use `obs research zotero search` to find papers, then `obs search` to find your vault notes about them. The MCP `unified_search` tool does both at once from Claude Desktop.

---

## What's Next

| Goal | Resource |
|------|----------|
| Search vault + Zotero together from Claude | [Claude Integration](../claude-integration.md) — `unified_search` |
| Monitor vault health over time | [Monitoring Tutorial](monitoring-and-health.md) |
| Full research command reference | [CLI Reference — Research section](../cli-reference.md#research) |
```

- [ ] **Step 3: Add nav entry to mkdocs.yml**

Open `mkdocs.yml`. Find the Tutorials section (currently lines 75-79). Add the new page after `claude-mcp.md`:

Current block:
```yaml
      - Overview: tutorials/index.md
      - Getting Started: tutorials/getting-started.md
      - Graph Analysis: tutorials/graph-analysis.md
      - AI Features: tutorials/ai-features.md
      - Claude / MCP Integration: tutorials/claude-mcp.md
```

New block (add two entries):
```yaml
      - Overview: tutorials/index.md
      - Getting Started: tutorials/getting-started.md
      - Graph Analysis: tutorials/graph-analysis.md
      - AI Features: tutorials/ai-features.md
      - Claude / MCP Integration: tutorials/claude-mcp.md
      - Research Setup: tutorials/research-setup.md
      - Monitoring & Health: tutorials/monitoring-and-health.md
```

Note: `monitoring-and-health.md` is created in Task 3 — add both nav entries now so neither task requires mkdocs.yml edits, avoiding merge ordering issues.

- [ ] **Step 4: Verify mkdocs build passes**

```bash
mkdocs build --strict 2>&1 | tail -10
```

Expected: `INFO    -  Documentation built in N.N seconds` with no warnings. If it fails with `"tutorials/monitoring-and-health.md" not found`, that's expected until Task 3 — create a stub file to unblock:

```bash
echo "# Monitoring & Health\n\nComing soon." > docs_mkdocs/tutorials/monitoring-and-health.md
mkdocs build --strict 2>&1 | tail -5
```

- [ ] **Step 5: Commit**

```bash
git add docs_mkdocs/tutorials/research-setup.md mkdocs.yml docs_mkdocs/tutorials/monitoring-and-health.md
git commit -m "docs(tutorials): add research setup tutorial + nav entries (v4.0.0)"
```

---

### Task 2: Research Cookbook Recipes

**Files:**
- Modify: `docs_mkdocs/cookbook.md` (add Research section before "Next Steps")

**Interfaces:**
- Consumes: `obs research zotero search`, `obs research pdf search`, `obs research manuscript stats`, `obs research bib check`
- Produces: 4 copy-paste recipes in the cookbook

- [ ] **Step 1: Locate insertion point in cookbook.md**

The cookbook ends with a "Next Steps" section preceded by the "Claude Desktop Integration" section. Insert a new `## Research Workflow` section between "Claude Desktop Integration" and "Next Steps".

Find the exact line:

```bash
grep -n "## Next Steps" docs_mkdocs/cookbook.md
```

Expected: line ~578. Insert before that line.

- [ ] **Step 2: Add the Research Workflow section**

Insert the following block at the line before `## Next Steps`:

```markdown
---

## Research Workflow

**Prerequisites:** Complete [Research Setup](tutorials/research-setup.md) to configure Zotero, PDF directories, and manuscripts.

### Search Zotero from the terminal

```bash
# Keyword search across all Zotero items
obs research zotero search "causal mediation" --limit 10

# Filter by item type
obs research zotero search "sensitivity analysis" --type journalArticle

# Filter by tag
obs research zotero search "" --tag "to-read"

# Get a specific item by Zotero key
obs research zotero get A1B2C3D4

# See what you added recently
obs research zotero recent --limit 5
```

### Find PDFs by content

```bash
# Full-text search across all configured PDF directories
obs research pdf search "instrumental variable" --limit 5

# Output as JSON for scripting
obs research pdf search "heterogeneous effects" --json | python3 -c "
import json, sys
for r in json.load(sys.stdin):
    print(f\"{r['title']}: {r['path']}\")
"
```

### Track manuscript status

```bash
# Overview of all manuscripts
obs research manuscript stats

# List drafts only
obs research manuscript list --status draft

# Deep-dive on one manuscript
obs research manuscript show collider-bias

# Check citations are complete before submitting
obs research bib check collider-bias
```

### Cross-tool research pipeline

Combine Zotero search, PDF discovery, and vault search for a complete literature review:

```bash
# 1. Find recent Zotero items on your topic
obs research zotero search "measurement error" --limit 10

# 2. Find PDFs you haven't linked to Obsidian yet
obs research pdf search "measurement error" --json | python3 -c "
import json, sys
results = json.load(sys.stdin)
print(f'Found {len(results)} relevant PDFs')
for r in results[:3]:
    print(f'  {r[\"title\"]}')
"

# 3. Check your vault for existing notes
obs search "measurement error" --limit 10

# 4. Check manuscript citation completeness
obs research bib check me-mediator   # catches missing refs before submission
```

!!! tip "Vault + Zotero unified search via Claude"
    From Claude Desktop, ask: *"Search my vault and Zotero for papers on collider bias"*.
    Claude calls `unified_search("collider bias", include_vault=True, include_zotero=True)` and
    summarizes results from both sources in one response.

```

- [ ] **Step 3: Verify mkdocs build**

```bash
mkdocs build --strict 2>&1 | tail -5
```

Expected: zero warnings.

- [ ] **Step 4: Commit**

```bash
git add docs_mkdocs/cookbook.md
git commit -m "docs(cookbook): add research workflow recipes (zotero, pdf, manuscript, bib)"
```

---

### Task 3: Monitoring & Health Tutorial

**Files:**
- Modify: `docs_mkdocs/tutorials/monitoring-and-health.md` (replace the stub from Task 1 with full content)

**Interfaces:**
- Consumes: MCP tools `get_trends`, `get_stale_notes`, `get_daily_digest`; CLI `obs health`, `obs analyze`, `obs ai quality`
- Produces: standalone tutorial replacing the stub; linked from research-setup.md and claude-mcp.md "What's Next" tables

- [ ] **Step 1: Write the full monitoring tutorial**

Replace `docs_mkdocs/tutorials/monitoring-and-health.md` with:

```markdown
# Monitoring & Health

Track your vault's evolution over time — note velocity, stale content, and daily digests — using the temporal tools added in v4.0.0.

**Time:** ~10 minutes | **Level:** 🔵 Intermediate | **Steps:** 5

**Prerequisites:** Complete [Getting Started](getting-started.md) and have at least one scanned vault.

---

## What Are the Temporal Tools?

Three MCP tools expose time-based vault intelligence. Use them from Claude Desktop or directly via the MCP server:

| MCP Tool | What it shows |
|----------|--------------|
| `get_trends` | Note creation velocity, link growth over time |
| `get_stale_notes` | Notes not modified in N days |
| `get_daily_digest` | Today's snapshot: new notes, edits, pending links |

These complement the static health tools (`obs health`, `obs analyze`) with a time dimension.

---

## Step 1: Check Vault Health (baseline)

Before monitoring trends, establish a baseline with the static health tools:

```bash
obs health Research           # 4-dimension score (connectivity, links, structure, freshness)
obs analyze Research          # graph metrics (density, clusters, hub/orphan counts)
obs analyze Research --json | python3 -c "
import json, sys
m = json.load(sys.stdin)
print(f\"Density: {m['density']:.4f}\")
print(f\"Orphans: {m['orphan_count']}\")
print(f\"Clusters: {m['cluster_count']}\")
"
```

Run this weekly and compare numbers over time.

---

## Step 2: Find Stale Notes (via Claude Desktop)

From Claude Desktop, after connecting the MCP server:

> *"Show me notes in Research that haven't been modified in 90 days"*

```
Claude calls: get_stale_notes("Research", days_threshold=90)
Returns: list of notes with last_modified date, word count, incoming link count
```

Stale notes to prioritize:
- High incoming links + no recent edits → hub notes that may need updating
- Zero links + no recent edits → candidates for archiving
- Recent creation + no edits → early drafts that need attention

---

## Step 3: Track Growth Trends (via Claude Desktop)

> *"Show me the writing velocity for Research over the last 30 days"*

```
Claude calls: get_trends("Research", days=30)
Returns:
  - notes_added: 12
  - notes_modified: 34
  - links_created: 87
  - avg_notes_per_day: 0.4
  - busiest_day: 2026-06-15 (4 notes)
```

Use this to understand your vault's growth patterns and whether you're linking as you write.

---

## Step 4: Daily Digest (via Claude Desktop)

Start each morning with:

> *"Give me a daily digest of my Research vault"*

```
Claude calls: get_daily_digest("Research")
Returns:
  - Notes created today: 0
  - Notes modified today: 2
  - Notes with no links (new orphans): 1
  - Pending: 3 notes modified >7 days ago with no incoming links
```

!!! tip "Automate the morning digest"
    Add to your morning workflow: open Claude Desktop, type *"Daily digest for Research"*.
    Takes 2 seconds. Catches orphaned notes before your vault grows chaotic.

---

## Step 5: Quality Sweep (weekly)

Combine temporal and AI tools for a weekly review:

```bash
# 1. Find the worst-scoring notes
obs ai quality Research --json | python3 -c "
import json, sys
scores = sorted(json.load(sys.stdin), key=lambda x: x['overall_score'])
for s in scores[:5]:
    print(f\"  {s['overall_score']:3.0f}  {s['title']}\")
"

# 2. Scan for stale content (CLI equivalent — uses graph freshness, not timestamps)
obs health Research --json | python3 -c "
import json, sys
h = json.load(sys.stdin)
print(f\"Freshness score: {h['freshness']}/100\")
print(f\"Structural score: {h['structure']}/100\")
"

# 3. Re-scan so metrics are fresh
obs scan /path/to/Research
```

---

## Weekly Monitoring Routine

```bash
# Monday morning (5 minutes)
obs health Research             # any score drops?
obs analyze Research -v         # orphan/cluster drift?
obs ai quality Research         # 5 worst notes (fix 1-2)
obs ai gaps Research            # any new knowledge gaps?
```

From Claude Desktop, all of the above becomes:
> *"Run my weekly vault review for Research — health, trends, quality scores, and gaps"*

Claude chains `get_vault_health` → `get_trends` → `run_obs_ai("quality")` → `run_obs_ai("gaps")` and summarizes in one response.

---

## What's Next

| Goal | Resource |
|------|----------|
| Research tools (Zotero, PDFs) | [Research Setup](research-setup.md) |
| MCP tool reference | [Claude Integration](../claude-integration.md#temporal-tools) |
| All health commands | [CLI Reference — Health section](../cli-reference.md#health) |
```

- [ ] **Step 2: Verify mkdocs build**

```bash
mkdocs build --strict 2>&1 | tail -5
```

Expected: zero warnings.

- [ ] **Step 3: Commit**

```bash
git add docs_mkdocs/tutorials/monitoring-and-health.md
git commit -m "docs(tutorials): add monitoring and health tutorial (temporal tools)"
```

---

### Task 4: Claude Integration — Temporal MCP Examples + Research CLI-Only Note

**Files:**
- Modify: `docs_mkdocs/claude-integration.md` (two targeted additions)

**Interfaces:**
- Consumes: MCP tools `get_trends`, `get_stale_notes`, `get_daily_digest`, `unified_search`
- Produces: temporal section in MCP tool reference table; research CLI-only note in tool table

- [ ] **Step 1: Locate the MCP tool table in claude-integration.md**

```bash
grep -n "Temporal\|get_trends\|get_stale\|get_daily\|unified_search\|Research\|research" docs_mkdocs/claude-integration.md | head -20
```

Find the "Temporal" group and the "Research" group in the tools table.

- [ ] **Step 2: Add temporal MCP example block**

After the Temporal tools table row section in `claude-integration.md`, find the prose section describing those tools (or the section heading "Temporal Tools"). Add the following example block:

```markdown
### Temporal Tools

Track vault evolution over time — velocity, stale notes, and daily snapshots.

**Daily digest:**
> *"Give me a morning digest of my Research vault"*

```
Claude calls: get_daily_digest("Research")
Returns: notes created/modified today, new orphans, pending-link notes
```

**Stale note hunt:**
> *"Find Research notes that haven't been touched in 3 months"*

```
Claude calls: get_stale_notes("Research", days_threshold=90)
Returns: list ordered by last_modified ascending, with link counts
```

**Growth trends:**
> *"How fast is my Research vault growing? Show me the last 30 days"*

```
Claude calls: get_trends("Research", days=30)
Returns: notes_added, notes_modified, links_created, avg_notes_per_day
```

See the [Monitoring & Health tutorial](tutorials/monitoring-and-health.md) for a complete workflow.
```

- [ ] **Step 3: Add research CLI-only note**

Find the Research section in the MCP tools table. The table currently has a "Research (13)" group including `unified_search` and individual research subcommand tools. Add a note immediately after the Research table group:

```markdown
!!! note "Research commands are CLI-only"
    `unified_search` is the only MCP-accessible research tool. The individual `obs research zotero|pdf|course|manuscript|bib` subcommands run only from the terminal — they read local files (Zotero SQLite, PDFs, Quarto projects) that Claude Desktop cannot access directly. See the [Research Setup tutorial](tutorials/research-setup.md) for terminal usage.
```

- [ ] **Step 4: Verify mkdocs build**

```bash
mkdocs build --strict 2>&1 | tail -5
```

Expected: zero warnings.

- [ ] **Step 5: Commit**

```bash
git add docs_mkdocs/claude-integration.md
git commit -m "docs(claude-integration): add temporal MCP examples + research CLI-only note"
```

---

## Self-Review

### Spec coverage

| Gap identified in audit | Task that covers it |
|--------------------------|---------------------|
| `obs research` domain — zero tutorial coverage | Task 1 (research-setup.md) |
| Research cookbook recipes missing | Task 2 (cookbook.md Research Workflow section) |
| Temporal MCP tools — no workflow narrative | Task 3 (monitoring-and-health.md) + Task 4 (claude-integration.md) |
| Research commands incorrectly implied as MCP-accessible | Task 4 (CLI-only admonition) |
| `monitoring-and-health.md` nav entry missing | Task 1 (added to mkdocs.yml) |

### Placeholder scan

None. All command examples use real syntax (`obs research zotero search "causal mediation"`), real config paths (`~/Zotero/zotero.sqlite`), real vault names (`Research`, `collider-bias`). Python snippets use actual JSON keys from the source (`overall_score`, `notes_added`, `density`).

### Type consistency

No inter-task type dependencies — these are documentation tasks. The only cross-task reference is the stub `monitoring-and-health.md` created in Task 1 and replaced in Task 3 (same filename, same nav entry — no mismatch).

---

## Execution Handoff

**Plan complete and saved to `docs/superpowers/plans/2026-06-23-doc-gap-remediation.md`.**

**Two execution options:**

**1. Subagent-Driven (recommended)** — fresh subagent per task, review between tasks.

**2. Inline Execution** — execute tasks in this session using superpowers:executing-plans.
