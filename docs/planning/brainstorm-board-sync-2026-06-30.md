# Brainstorm: Smarter Board Sync

> Generated: 2026-06-30 during a /brainstorm session
> Context: obsidian-cli-ops v4.2.0, atlas v0.12.2
> Sources: vault inspection, atlas repo review, web research, open-source landscape

---

## Current State Assessment

### Vaults & Boards

| Board | Lines | Type | Freshness |
|-------|-------|------|-----------|
| `_ACTION-BOARD.md` | 111 | AI-generated tactical (research front door) | Last refreshed 2026-06-30 (manual, Claude Code) |
| `_RESEARCH-BOARD.md` | 27 | Auto-generated from atlas registry (`obs research board`) | Stale (generated 2026-06-26 via Cowork) |
| `RESEARCH_HUB.md` | 223 | Strategic reference (hand-maintained) | Manual |
| `MediationVerse_Dashboard.md` | 61 | Auto-synced from `.STATUS` (Python script) | Needs separate automation |
| `Research_Lab_Dashboard.md` | 95 | Dataview queries (live in Obsidian) | Good, but vault-local only |

### Pain Points

1. **Multi-hop pipeline is partially manual**: `.STATUS` → `atlas sync` (via launchd weekly) → `obs research board` (MANUAL) → vault
2. **Status drift**: The action board itself documented cases of stale data (pmed-modern P2 held 11d, measurement error 5→45%, sensitivity wrong)
3. **No cross-vault visibility**: Knowledge_Base (2641 notes, 0 boards), Documents (3529 notes, 0 boards)
4. **LLM doing rote work**: The `research--action-board.md` prompt has Claude re-generate status tables that `obs research board` already produces deterministically
5. **ADR explicitly calls this a stopgap**: The ADR-scheduled-tasks-architecture.md says status rendering should be deterministic (atlas/obs), with LLM only for thinking

### Existing Building Blocks

| Block | Status | Location/Notes |
|-------|--------|----------------|
| `obs research board --out FILE` | ✅ Shipped v4.0.0 | Deterministic, idempotent, marker-bounded renderer |
| `atlas sync --research` | ✅ Shipped v0.12.x | Updates atlas registry from `.STATUS` files |
| `atlas project list --format json` | ✅ Shipped | Data source for `obs research board` |
| launchd (com.data-wise.atlas-sync) | ✅ Running weekly | Only triggers `atlas sync`, NOT the board render |
| `obs bridge` | ✅ Shipped v4.0.0 | Read-side Obsidian CLI bridge |
| `obs doctor --layer sync` | ✅ Shipped v4.2.0 | Drift detection between vault and index |
| `research--action-board.md` prompt | ✅ Active prompt | Currently sole generator of `_ACTION-BOARD.md` |
| `obs link` | ✅ Shipped | Creates `.obs/sync.yml` mirror maps (ADR-001) |

---

## Idea 1: Auto-Refresh Pipeline (launchd)

Add a second launchd job that runs `obs research board --out <vault_path>` after `atlas sync`.

| Pros | Cons |
|------|------|
| Builds on existing launchd infra | Only updates `_RESEARCH-BOARD.md`, not `_ACTION-BOARD.md` |
| Idempotent renderer (zero diff when state unchanged) | Needs iCloud vault path resolution |
| Single weekend-morning cron = no stale status tables | iCloud sync timing — board may lag render by minutes |
| ~30 lines of shell + plist, zero code changes | No error notification if obs or atlas fails |

**Implementation sketch:**
```bash
#!/usr/bin/env zsh
# scripts/board-refresh.sh — called by launchd weekly
VAULT_PATH="$HOME/Library/Mobile Documents/iCloud~md~obsidian/Documents/Research"
atlas sync --research --dry-run  # silent; no output unless something changed
obs research board --out "$VAULT_PATH/00_meta/_RESEARCH-BOARD.md"
```

---

## Idea 2: `obs board refresh` — Native Subcommand

First-class `obs board refresh [vault] [--all]` that reads atlas registry AND vault DB, diffs, and writes marker-bounded updates. Later: `obs board watch` for file-watch-triggered refresh.

| Pros | Cons |
|------|------|
| Single command, no external deps | New feature to build (~200 lines) |
| Leverages `doctor --layer sync` drift detection | Duplicates some atlas project-list parsing |
| Can auto-detect all vaults + update across all | No cron capability built-in (needs external scheduler) |
| Extensible to Knowledge_Base vault | |

---

## Idea 3 (RECOMMENDED): Hybrid Deterministic + AI Board

The ADR's intended three-layer architecture: **atlas organizes, obs renders, LLM thinks**.

```
Schedule (launchd):                    On-demand (Claude Code):
  atlas sync --research                   Read _RESEARCH_BOARD.md
  obs board refresh --all                + MOCs + radar + ledger
    → _RESEARCH_BOARD.md  (deterministic)    → _ACTION-BOARD.md (AI-contextual)
    → MediationVerse_Dashboard.md            → leverage ranking, threats, scoop
    → (future) Knowledge_Base dashboard
```

| Pros | Cons |
|------|------|
| Separates concerns (status ≠ strategy) | Two systems to maintain |
| Deterministic layer catches drift automatically | Requires prompt procedure update |
| AI only does high-value thinking | LLM can still hallucinate if sources conflict |
| This is the ADR's stated target architecture | |

---

## Idea 4: Cross-Vault Board (Knowledge_Base + Documents)

Extend board refresh into Knowledge_Base vault (2641 notes, 0 boards) and Documents (3529 notes).

| Pros | Cons |
|------|------|
| Unlocks 2nd largest vault for project tracking | Knowledge_Base not git-backed (pure iCloud) |
| Could surface reference projects that sit dormant | Mixed purposes (reference ≠ action) |
| YAML frontmatter on atomic notes → Dataview-ready | Aggregating cross-vault requires obs DB queries |

---

## Idea 5: GitOps Board Sync (GitHub Actions)

Push `.STATUS` changes → GitHub Actions → auto-refresh → commit result → vault auto-syncs.

| Pros | Cons |
|------|------|
| Serverless, no local daemon | 2-5min latency (GitHub runner + iCloud) |
| Audit trail in git | iCloud sync timing unpredictable |
| Works from any machine | Over-engineered for a local vault |

---

## Idea 6: Kanban Plugin Bridge

Embed kanban-plugin format JSON into board note frontmatter alongside markdown tables.

| Pros | Cons |
|------|------|
| Drag-and-drop (ADHD-friendly, dopamine) | Opaque JSON array format |
| Community standard | Two render targets to maintain |

---

## Idea 7: Watcher Daemon (`obs board watch`)

File-watcher monitoring vault dirs + `.STATUS` files, triggering board refresh on change.

| Pros | Cons |
|------|------|
| Near-real-time updates | Complex to debug |
| No scheduler needed | Background daemon = resource drain |
| Catches all drift immediately | Race conditions with iCloud sync |

---

## Effort × Impact Matrix

| Idea | Effort | Impact | Notes |
|------|--------|--------|-------|
| **1. launchd auto-refresh** | 🟢 ~1hr | 🟢 High | Already built, just needs chaining |
| **2. obs board command** | 🟡 ~0.5d | 🟢 High | Natural evolution of `obs research board` |
| **3. Hybrid architecture** | 🟢 ~2hr prompt | 🟢🟢 Highest | ADR-approved; changes no code, only process |
| **4. Cross-vault board** | 🟡 ~1-2d | 🟡 Medium | New renderer needed |
| **5. GitOps board sync** | 🔴 ~1d | 🟡 Medium | Overkill for local sync |
| **6. Kanban plugin** | 🔴 ~2d | 🟡 Medium | Double maintenance |
| **7. Watcher daemon** | 🔴 ~2-3d | 🟢 High but risky | Background daemon complexity |

**Recommended order:** 3 → 1 → 2 → 4 → 6

---

## Broader Research: Open-Source Landscape

| Tool | Stars | Pattern | Relevance |
|------|-------|---------|-----------|
| **ResearchScope** | 82★ | GitHub Actions daily pipeline → PostgreSQL → static site | Cron pattern; multi-source connectors (arXiv, OpenAlex, S2) |
| **ResearchOS** | 3★ | Local-first Next.js, FSA API, JSON+markdown on disk | File-based storage pattern; AI Helper prompt generation |
| **Sophra** | 5★ | Elasticsearch + Redis + ML, enterprise doc mgmt | Overkill — general-purpose, not research-specific |

**Key takeaway:** None of these solve the specific problem of status drift between code repos and vault boards. Your `obs doctor --layer sync` already detects it. What's missing is the automated remediation.

---

## Implementation Roadmap

### Phase 1 (immediate, ~1hr): Write shell script + launchd plist
- Chain `atlas sync --research` + `obs research board --out`
- Schedule weekly (Monday 09:15, after existing atlas sync)
- Test idempotency

### Phase 2 (short-term, ~0.5d): `obs board refresh` subcommand
- Promote pipeline to first-class command
- Add `--all` flag for multi-vault
- Add `obs board status` for diagnostics

### Phase 3 (medium-term, ~1-2d): Knowledge_Base board
- Simplified dashboard for reference projects
- YAML frontmatter scan (tags, status, next actions)

### Phase 4 (ongoing): Update `_ACTION-BOARD.md` prompt
- Consume `_RESEARCH-BOARD.md` as primary source
- LLM only for leverage ranking, threats, action sequencing
- Never re-generate raw status data
