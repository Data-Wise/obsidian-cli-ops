# Proposal: Planning Doc Consolidation (obsidian-cli-ops)

> [!success] RESOLVED (2026-07-01) — quick wins executed, rest declined by design
> Archived the 3 confirmed-shipped SPEC files (`SPEC-phase2-nexus-port.md`, `SPEC-pre-push-hook.md`,
> plus the superseded `SPEC-merge-nexus-cli-2026-06-19.md`) to `docs/planning/specs-completed/`, and
> `SPEC-harden-skills.md` after verifying its actual PR #73 coverage. Wrote the SPEC-lifecycle rule
> into root `CLAUDE.md`'s Git Workflow section, mirroring the ORCHESTRATE-deletion convention. The
> atlas-SPEC-ingestion and Obsidian-vault-mirror options were correctly declined — no demonstrated need.

> Generated 2026-07-01 via brainstorm. Not committed — untracked scratch file, review then decide what to act on.

---

## What I Found

### 1. Atlas's actual state model (not aspirational)

Read: `/Users/dt/projects/dev-tools/atlas/CLAUDE.md`, `atlas/README.md`, `atlas/src/use-cases/registry/SyncFromStatusUseCase.js`, `atlas/src/use-cases/registry/SyncRegistryUseCase.js`.

- **Data model**: atlas tracks `projects` (registry entries), `sessions`, `captures`, `breadcrumbs` in `~/.atlas/`. Confirmed via README and source tree.
- **`.STATUS` sync mechanism — concrete**: `atlas sync` runs `SyncFromStatusUseCase`, which scans a root path for `.STATUS` files via a `StatusFileParser`, parses the machine-readable header (`priority:`, `status:`, `progress:`, `next:`, `verified:`, and for research projects `kind:`/`target:`), and upserts each into the project registry. This is the **only** ingestion path from spoke projects into atlas. Confirmed by direct source read.
- **Zero SPEC/ORCHESTRATE ingestion**: `grep -rln "SPEC-\|ORCHESTRATE-" atlas/src` returns **no matches**. Atlas does not parse, index, or reference spoke-project SPEC/ORCHESTRATE files in any way.
- **Atlas has its own SPEC files** — `atlas/docs/specs/*.md` (11 files) and `atlas/docs/plans/PHASE-3-research-registry-plan.md`. This is atlas's *own* project-planning convention for atlas's own development, structurally identical to what obsidian-cli-ops does for itself. Atlas does not extend this convention outward to spokes; it doesn't ask spokes to keep SPEC files anywhere atlas can see.
- **`obs research board`**: a downstream *consumer* of `atlas project list --format json` (per `docs/planning/brainstorm-board-sync-2026-06-30.md`, itself primary-source here) — this renders atlas's `.STATUS`-derived registry into a vault board. It does not feed anything back into atlas; it's one-way, deterministic, and already shipped in v4.0.0. This is the **research-vault** board-sync problem, a different concern from obsidian-cli-ops's own dev-planning docs — noted for completeness, out of scope here.

**Conclusion: atlas's contract with spoke projects begins and ends at `.STATUS`.** No aspirational SPEC/ORCHESTRATE ingestion exists or is planned in atlas's own docs.

### 2. obsidian-cli-ops's current planning-doc sprawl

`docs/planning/` (11 items):

| File | State |
|---|---|
| `README.md` | Index/map — describes the "2-file consolidation" philosophy (`.STATUS` + `IDEAS.md` as live; rest historical) |
| `IMPLEMENTATION-ROADMAP.md` | Archived, banner points to `.STATUS` + active SPEC |
| `TODOS.md` | Archived, banner points to `.STATUS` + active SPEC |
| `project-hub.md` | Archived, banner points to `.STATUS` + active SPEC |
| `project-plan.md` | Archived, banner points to `.STATUS` + active SPEC |
| `improvement-suggestions-2026-06-22.md` | Resolved triage (4/5 issues shipped), banner updated 2026-07-01 |
| `brainstorm-board-sync-2026-06-30.md` | Live brainstorm doc, unresolved (research-vault board sync, separate concern) |
| `phases/` (5 files) | Historical phase-completion summaries, no banners needed (correctly scoped as history) |
| `sessions/` (1 file) | Single historical session summary |

**Root-level SPEC files** (5, all git-tracked, clean working tree):

| File | Own status field | `.STATUS` cross-check |
|---|---|---|
| `SPEC-merge-nexus-cli-2026-06-19.md` | Draft/RFC | Explicitly superseded by v2 in its own text |
| `SPEC-merge-nexus-cli-v2-2026-06-21.md` | RATIFIED Phase 0 | Phase 1 (v4.0.0) + Phase 2 (v4.3.0, 62 commands) both shipped per `.STATUS`; `.STATUS next:` still lists "port plugin skills" + "port vault template ops" — **partially open**, don't archive yet |
| `SPEC-phase2-nexus-port.md` | Approved (brainstorm consensus) | `.STATUS verified:` confirms v4.3.0 shipped 2026-06-30 with Phase 2 (13 commands, 62 total) — **complete, stale, not archived** |
| `SPEC-pre-push-hook.md` | Draft v2 | `.STATUS verified:` explicitly names "pre-push hook" as shipped in the same v4.3.0 line — **complete, stale, not archived** |
| `SPEC-harden-skills.md` | Planned, dated 2026-06-30 | Commit `e915a3f` ("docs audit, skill hardening, board-sync, vault-sync", PR #73) landed 2026-06-30/07-01 — **likely complete, needs a status-field check against PR #73's actual scope before archiving** |

**Genuine duplication found**: none of the *live* docs duplicate `.STATUS` — the archived files correctly point back to it. The real drift is procedural, not content-level: **completed SPEC files aren't being archived/removed from root after their work ships**, unlike ORCHESTRATE files, which the project's own convention (global CLAUDE.md) already deletes after merge. SPEC files have no equivalent lifecycle rule.

### 3. Obsidian vault presence — none found

Searched `Knowledge_Base/dev-tools/` (contains only an unrelated `claude-code/` subfolder) and `Documents/~/projects/dev-tools/` (empty) plus a vault-wide filename and content grep for `obsidian-cli-ops`/`obs-cli`. **Zero matches anywhere in the vault.** obsidian-cli-ops has no vault-mirrored planning presence today — everything lives in git. (Contrast with the *research* projects, which do have vault dashboards — `MediationVerse_Dashboard.md`, `_RESEARCH-BOARD.md` — but that's the research-vault-sync system, a separate pipeline documented in `brainstorm-board-sync-2026-06-30.md`, not something obsidian-cli-ops itself has ever used for its own planning.)

---

## Proposal

### Should `docs/planning/` be pruned/consolidated further?

**No further pruning of content** — the 2026-06-22 consolidation already did the real work (9 files → 2 live + historical archive), and the archived files carry correct banners pointing to `.STATUS`. The structure is sound. What's missing is a **lifecycle rule for root-level SPEC files**, which sit outside `docs/planning/` entirely and have drifted.

### Should atlas ingest anything beyond `.STATUS`?

**No.** Atlas's own convention for itself (`docs/specs/`) is not something it asks of spokes, and there's no ingestion code for it. Building a SPEC-ingestion feature into atlas would be scope creep against atlas's demonstrated single-purpose design (ecosystem status registry, not a planning-doc aggregator). `.STATUS` already carries a `next:` field that's the right level of granularity for atlas's cross-project dashboard use case; SPEC files are project-internal execution detail atlas has no use for.

### Is there value in an Obsidian vault mirror for obsidian-cli-ops's own planning?

**No.** Two independent findings support this: (a) none exists today, and it hasn't been missed — `.STATUS` + git already serves this role and is checked into version control, which a vault copy would not be; (b) the vault-mirror pattern that *does* exist (research projects → `MediationVerse_Dashboard.md` etc.) solves a different problem — cross-project dashboards for the researcher's daily vault workflow, not dev-tool release planning. Introducing a vault mirror for obsidian-cli-ops would be a second source of truth with no consumer.

---

## Quick Wins (< 30 min)

1. **Archive `SPEC-phase2-nexus-port.md` and `SPEC-pre-push-hook.md`** — both are confirmed shipped in v4.3.0 per `.STATUS verified:`. Move to `docs/planning/specs-completed/` (mirrors atlas's own `docs/specs/` naming) or add an ARCHIVED banner in place, matching the existing pattern used in `IMPLEMENTATION-ROADMAP.md`/`TODOS.md`.
2. **Delete `SPEC-merge-nexus-cli-2026-06-19.md`** — its own text says it's superseded by v2; keeping both at root is pure duplication with zero live value. (Or archive alongside the others if history is wanted — but this one adds nothing v2 doesn't already restate.)
3. **Verify `SPEC-harden-skills.md` against PR #73's actual merged scope** — one grep/diff check to confirm whether "Planned" should now read "Complete," then archive or leave as-is.

## Medium Effort (1-2 hrs)

- [ ] **Write a one-paragraph SPEC lifecycle rule** into `docs/planning/README.md` (or this project's `CLAUDE.md` Git Workflow section) alongside the existing ORCHESTRATE-deletion convention: *"SPEC files move to `docs/planning/specs-completed/` (not deleted) once their work ships and `.STATUS verified:` confirms it — check at the same time ORCHESTRATE files are deleted, i.e., at merge-to-dev cleanup."* This closes the gap the advisor and this research both surfaced: ORCHESTRATE has a documented lifecycle, SPEC does not.
- [ ] **Re-verify `SPEC-merge-nexus-cli-v2-2026-06-21.md`** once "port plugin skills" and "port vault template ops" (the two remaining `.STATUS next:` items) ship — only archive then, since it's the one SPEC still tracking genuinely open work.

## Long-term (future sessions)

- [ ] **None recommended for atlas integration** — the research found no gap to fill; atlas's `.STATUS`-only contract is correctly scoped and shouldn't be extended for obsidian-cli-ops's benefit.
- [ ] If the SPEC-lifecycle rule proves useful here, consider proposing it as a craft-wide convention (alongside the existing ORCHESTRATE-deletion rule) rather than a one-off local fix — but that's a cross-project decision, not something to act on unilaterally from this repo.

## Recommended Next Step

→ Start with #1 (archive the two confirmed-shipped SPEC files) because it's the only finding backed by hard evidence (`.STATUS verified:` field) with zero ambiguity, takes minutes, and immediately removes the stale-root clutter that prompted this research in the first place.
