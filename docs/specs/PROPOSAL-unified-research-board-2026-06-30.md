---
title: Unified Research Board — ADHD-friendly consolidation
created: 2026-06-30
status: proposal
---

# Unified Research Board — ADHD-friendly consolidation

## Problem

4 boards, 4 formats, no single front door:

| Board | Scope | Editable? | Failure mode |
|---|---|---|---|
| `_ACTION-BOARD.md` | manuscript-level, all repos | marker-bounded, `.STATUS` `next:` pulled **verbatim** | wall-of-text — narrative dumps, not scannable |
| `_RESEARCH-BOARD.md` | ? (overlaps ACTION-BOARD) | marker-bounded, auto-gen | unclear how it differs from ACTION-BOARD |
| `MediationVerse_Dashboard.md` | package-level only (7 pkgs) | AUTO-SYNC block, weekly cron | scope confusion — manuscript decisions get incorrectly routed here |
| `RESEARCH_HUB.md` | hand-curated hub | free-edit | drifts stale (caught 2 wrong entries this session) |

Root cause of this session's audit misses: no single place answers "what's actionable across all 11 repos right now" — I had to cross-check 4 files plus `.STATUS` directly, and still missed 2 manuscripts on the first pass.

## Quick Wins (< 30 min)

1. **Pick ONE canonical file** — recommend `_ACTION-BOARD.md` (already has the AUTO-SYNC infra + LLM-augment placeholders). Stub the other 3 with one line each: `> [!info] Superseded — see [[_ACTION-BOARD]]` and a backlink. Don't delete (link rot).
2. **Collapse raw `.STATUS` dumps into a collapsible callout** — Obsidian supports `> [!note]- Raw status (click to expand)`. Wrap each project's verbatim `next:` text so the board defaults to closed/scannable, full detail one click away.
3. **Add a single "RIGHT NOW" line at the top** — the one highest-priority actionable item across all repos, hand-written, refreshed each session. Matches the Me/You/External × AUTO/WAITING/YOUR-CALL/BLOCKED classification already in [[feedback-brief-format-task-classification]].

## Medium Effort (1-2 hrs)

- [ ] **Truncate the sync source, not just the display** — modify whichever script feeds `_ACTION-BOARD.md`'s `obs board refresh` (and `mediationverse-status-sync.py` for packages) to pull only the first 1-2 lines of `.STATUS` `next:` + a link to the full file, instead of the full narrative. Fixes the wall-of-text at the source so every consumer benefits, not just this one board.
- [ ] **Merge package + manuscript state into the one file** — add a second AUTO-SYNC block to `_ACTION-BOARD.md` for the package table currently only in `MediationVerse_Dashboard.md`. One board, two auto-synced sections (packages | manuscripts), same LLM-augment sections around them.
- [ ] **Fix + redirect `RESEARCH_HUB.md`** — correct the stale Active-Manuscripts table and Topic-Backlog miscategorization already flagged this session, then replace its own tables with a pointer to the unified board so it can't drift again.

## Long-term (future sessions)

- [ ] **Board-drift check as a routine** — a scheduled trigger (weekly, alongside the existing `mediationverse-status-sync` launchd job) that diffs `.STATUS` files against every board and flags mismatches — would have caught the pmed/pmed-modern naming collision and the 11-day-stale `incr_pmed` status automatically instead of requiring a manual full audit.
- [ ] **Lifecycle-column view** — a Dataview-driven kanban (Idea → Identification → Estimation → Asymptotics → Simulation → Application → Writing → Review → Revision → Submission, per [[research-session-defaults]]) auto-populated from `.STATUS`, replacing static markdown tables entirely. Bigger lift — needs the Dataview plugin and a query per column.

## Recommended Next Step

→ **Start with Quick Win #1 + #2** (canonical file + collapsible raw dumps) — reversible, touches no sync tooling, and directly fixes the ADHD pain point (wall of text, 4 places to check) in one sitting. The medium-effort truncate-at-source item is the natural follow-up once the single-file shape is confirmed to work.
