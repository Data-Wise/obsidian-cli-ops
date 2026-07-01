# SPEC — Research Board Sync & Automation Pipeline

**Status:** DRAFT — written from the /brainstorm output (explore+refine, deep research)
**Date:** 2026-06-30
**Owner:** @dtofighi
**Supersedes:** `ADR-scheduled-tasks-architecture.md` (proposed, vault-side)
**Feeds:** v4.3.0 (board sync) + follow-up v4.4 (Knowledge_Base board)

> **One-line:** Automate the `_RESEARCH-BOARD.md` refresh (currently manual), then promote `obs board refresh` to a first-class command, then update the AI action-board prompt to consume deterministic status. This closes the status-drift gap that the ADR called a stopgap.

---

## 0. Verified Ground Truth (2026-06-30)

Three sources checked during the /brainstorm session:

| Claim | Reality | Source |
|---|---|---|
| `_RESEARCH-BOARD.md` auto-refreshes via CI | **False.** No automation exists. Generated 2026-06-26 manually via Cowork. | vault inspection |
| `_ACTION-BOARD.md` has no stale data | **False.** The 2026-06-30 refresh found 6 items with wrong status (pmed-modern P2 held was 11d stale, measurement error 5% vs 45%, sensitivity paused vs planning). | `_ACTION-BOARD.md` |
| launchd runs the board pipeline | **Partial.** `com.data-wise.atlas-sync` runs `atlas sync` weekly (Mon 09:10) — but does NOT trigger `obs research board`. The render step is disconnected. | launchd plist |
| `obs research board` can write to vault | **True.** `--out FILE` flag writes marker-bounded blocks. `--dry-run` previews changes. Idempotent renderer. | source code |
| Atlas registry has all project data | **True.** `atlas project list --kind manuscript --format json` returns 10 manuscripts + programs. Status, venue, priority, progress all populated. | CLI test |
| `obs doctor --layer sync` detects drift | **True.** Documents vault has 36 ghost rows, Knowledge_Base has 13 ghosts + 4 missing + 2 errors. | CLI test |
| ADR calls current approach a stopgap | **True.** The vault-side ADR-scheduled-tasks-architecture.md says the LLM-generated action board is interim — desired architecture: atlas organizes, obs renders, LLM thinks. | vault ADR |

**Net:** The `obs research board` renderer is built, idempotent, and marker-bounded. The only missing piece is a cron trigger. The AI action-board prompt does rote work (status tables) that the renderer already handles. The fix touches zero Python code for Phase 1 and only a prompt for Phase 4.

---

## 1. Architecture

### Target State (after all 4 phases)

```
launchd (weekly 09:15)          On-demand (Claude Code)
       |                                |
       v                                v
+------------------+          +------------------+
|  board-refresh    |          |  build action     |
|  (shell script)   |          |  board (prompt)   |
|                   |          |                  |
|  atlas sync       |          |  _RESEARCH_BOARD  |
|  obs board refresh|          |  + MOCs          |
|  obs doctor alert |          |  + radar/ledger  |
+--------+---------+          +--------+---------+
         |                             |
         v                             v
+------------------+          +------------------+
| _RESEARCH_BOARD   |          | _ACTION-BOARD     |
| (deterministic)   |          | (LLM-contextual)  |
| status tables     |          | leverage ranking  |
| no AI             |          | threats, scoop    |
+------------------+          +------------------+

+------------------------------------------+
|  obs board subcommand (Phase 2)          |
|                                          |
|  connectors/                             |
|    atlas_connector.py   <- project list  |
|    vault_connector.py   <- notes+links   |
|    status_connector.py  <- .STATUS files |
|    doctor_connector.py  <- drift report  |
|                                          |
|  engine/                                 |
|    merger.py            <- dedup+merge   |
|    renderer.py          <- markdown tbl  |
|                                          |
|  output/                                 |
|    vault_writer.py      <- marker-bound  |
|    stdout_writer.py     <- --dry-run     |
+------------------------------------------+
```

### Three-Layer Data Flow (ADR-aligned)

| Layer | Tool | Responsibility | Automation |
|-------|------|----------------|------------|
| **Organize** | atlas | Single registry of projects, tasks, priorities | launchd weekly |
| **Render** | obs | Deterministic dashboards, marker-bounded tables | Phase 1 launchd + Phase 2 CLI |
| **Think** | LLM (Claude) | Leverage ranking, threat assessment, action sequencing | On-demand prompt |

---

## 2. Phase 1 — Auto-Refresh Pipeline (launchd)

**Effort:** ~1 hour. **Impact:** Eliminates stale `_RESEARCH-BOARD.md`.

### What

A shell script that chains `atlas sync --research` -> `obs research board --out <vault_path>` -> `obs doctor --layer sync <vault>` (alert on drift), triggered by a second launchd plist weekly (Mon 09:15).

### Files to create

- `scripts/board-refresh.sh` — the shell script
- Com.apple launchd plist at `~/Library/LaunchAgents/com.data-wise.obs-board-refresh.plist`

### Idempotency

`obs research board` generates a deterministic block. Same input -> same output -> zero diff -> no file change -> no Obsidian sync trigger. The `--dry-run` flag reports `changed=true/false` so the script can log whether data actually moved.

### Success Criteria

- Monday 09:15: `_RESEARCH-BOARD.md` is updated with latest atlas state
- No spurious Obsidian sync traffic on unchanged weeks
- `obs doctor` drift alerts captured in log

---

## 3. Phase 2 — `obs board refresh` Native Subcommand

**Effort:** ~0.5 day. **Impact:** Discoverable CLI command, extensible to multiple vaults.

### Command Spec

```
obs board refresh [--vault V] [--all] [--dry-run] [--json]
obs board status  [--vault V] [--all] [--json]
obs board watch   [--vault V]          (future)
```

### Connector Architecture

```
obs board refresh --all
  |
  +-- atlas_connector.py
  |    atlas project list --kind manuscript --format json
  |    atlas project list --kind program --format json
  |
  +-- vault_connector.py
  |    SELECT COUNT(*), MAX(last_scanned) FROM notes WHERE vault_id=?
  |    SELECT COUNT(*) FROM links WHERE vault_id=? AND resolved=0
  |
  +-- status_connector.py
  |    ls ~/projects/research/*/.STATUS
  |    ls ~/projects/r-packages/active/*/.STATUS
  |    parse each for status/priority/progress fields
  |
  +-- doctor_connector.py (optional, diagnostic)
  |    obs doctor --layer sync <vault> --json
  |
  +-- engine/
       merger.py    -- merge sources, dedup by project name
       renderer.py  -- render merged data to markdown tables
       vault_writer.py -- marker-bounded write to vault file
```

### Extending `obs research board`

The existing `research_board.py` already has `load_projects()`, `build_block()`, and `write_marked_block()`. Phase 2 creates a new `core/board.py` that wraps the research board logic and adds connectors:

```
obs board refresh -> core/board.py
     BoardEngine
       .refresh(vault_id, sources=[atlas, vault, status])
       .status(vault_id)
       .watch(vault_id)

     Connector (ABC)
       .name -> str
       .fetch() -> list[ProjectStatus]

     AtlasConnector(Connector)
     VaultConnector(Connector)
     StatusConnector(Connector)

     Merger
       .merge(projects: list[ProjectStatus]) -> list[ProjectStatus]

     BoardRenderer
       .render(projects) -> str      # markdown table
       .write(path, block)           # marker-bounded write
```

### Output Format (for each vault)

```
<!-- obs:board:start -->
## Research Board
generated: 2026-06-30 by obs board refresh

### Manuscripts
| Project | Venue | Status | Progress | Next |
|---|---|---|---|---|
| collider | AMPPS | R&R | 95% | submit rev1 by Aug 7 |

### Programs
[...]

### Packages
[...]

### Vault Health
| metric | value |
|--------|-------|
| notes | 2,641 |
| broken links | 13 |
| ghosts | 0 (no drift) |
| last scan | 2026-06-29 |
<!-- obs:board:end -->
```

---

## 4. Phase 3 — Knowledge_Base Board (Deferred)

**Effort:** ~1-2 days. **Impact:** Medium.

Simplified board for the 2641-note Knowledge_Base vault. YAML frontmatter scan for tags, status, next actions. Reuses same connector architecture. Delayed until Phase 1+2 are stable.

---

## 5. Phase 4 — Action Board Prompt Update

**Effort:** ~2 hours. **Impact:** Eliminates LLM status-hallucination, reserves AI for thinking.

### Current Problem

The `research--action-board.md` prompt has Claude:
1. Read 7 sources (including `.STATUS` files, MOCs, radar)
2. Regenerate ALL status tables from scratch (rote work)
3. Rank actions by leverage (thinking)
4. Identify threats and scoop (thinking)

This duplicated the deterministic `obs research board` output and introduced drift (the 06-30 refresh found 6 wrong status values).

### Updated Prompt Strategy

The prompt should be rewritten to:

1. **Read `_RESEARCH-BOARD.md` as primary status source** — no re-deriving status from raw `.STATUS`
2. **Flag discrepancies** — if the action board's reading differs from `_RESEARCH-BOARD.md`, note the delta rather than silently overwriting
3. **Reserve LLM for:** leverage ranking, threat/scoop assessment, next-action sequencing, and the TL;DR
4. **Output only the thinking sections** — markdown tables are already deterministic

### Prompt Structure (Revised)

```
SOURCES (priority order):
1. _RESEARCH-BOARD.md — PRIMARY for all status/progress/next tables
   (Deterministic, from obs board refresh. Do NOT re-derive from .STATUS)
2. Program MOCs + WORKFLOW.md — phase-level progress and blockers
3. _RADAR-MOC + _SCOOP-WATCH — threats and literature changes
4. _IDEA-LEDGER — live seeds (status != done)
5. Newest SESSION-*.md — recent shipped items

PROCEDURE:
1. Read _RESEARCH-BOARD.md -> get all status/progress/next columns
2. Cross-check with MOCs for phase-level detail, blockers, recent commits
3. Cross-check with radar/scoop for threats
4. Rank "Act on now" by leverage = priority * readiness * unblock-value
   Cap at 7. Bold the single highest-leverage move.
5. Write _ACTION-BOARD.md using the OUTPUT TEMPLATE:
   - TL;DR (<=5 bullets, from _RESEARCH-BOARD.md + MOCs)
   - Act on now (ranked, with [time] + risk)
   - Status at a glance (copied from _RESEARCH-BOARD.md, not re-derived)
   - Future ideas & new proposals (from radar/ledger)
   - Threats / scoop-watch (from radar/scoop)
   - This week (sequenced)
```

---

## 6. Sequencing & Dependencies

| Step | What | Depends On | Effort |
|------|------|------------|--------|
| P1a | Write `scripts/board-refresh.sh` | nothing | ~15 min |
| P1b | Install launchd plist + test | P1a | ~15 min |
| P2a | Create `core/board.py` + connector ABC | nothing | ~2 hr |
| P2b | Wire CLI `obs board refresh/status` | P2a | ~1 hr |
| P2c | Update `scripts/board-refresh.sh` to use `obs board refresh` | P2b | ~15 min |
| P3 | Knowledge_Base board | P2b | ~1-2 days |
| P4 | Rewrite `research--action-board.md` prompt | P1a (so _RESEARCH_BOARD.md stays fresh) | ~2 hr |

**Recommended start:** P1a + P1b (immediate, no code changes). Then P2a + P2b (subcommand). Then P4 (prompt). Defer P3.

---

## 7. Risks & Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| iCloud vault path changes | Low | Medium | Script hardcodes path; add a `--vault-path` override |
| `atlas` or `obs` missing from PATH in launchd context | Medium | High | `EnvironmentVariables` in plist sets explicit PATH |
| launchd log rotation fills disk | Low | Low | Logs are small (<1KB per run); add `logrotate` or cleanup if needed |
| _RESEARCH-BOARD.md has hand-edits outside marker bounds | Low | Low | `write_marked_block()` only touches content between markers |
| _ACTION-BOARD.md prompt still hallucinates | Medium | Medium | Cross-reference check: prompt says "if _RESEARCH_BOARD.md says X but you think Y, flag it, don't overwrite" |
