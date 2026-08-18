# Brief: Board Sync Current State (2026-07-01)

> [!success] RESOLVED (2026-07-01) — all findings acted on, shipped in v4.3.0
> The dispatcher gap found here was fixed (PR #80), the dedup question was answered (PR #82,
> keep both), and the action-board prompt was verified already correct (PR #81). See
> `PLAN-board-sync-next-steps.md` for the execution plan and `.STATUS` for the release record.

> Companion to `docs/planning/brainstorm-board-sync-2026-06-30.md`. That doc already made
> the architecture calls — this brief verifies what shipped since, and the brainstorm below
> proposes next steps grounded in that.

---

## What Exists Today

### Two board systems, not one

| | `obs research board` (SPEC-obs, v4.0.0) | `obs board refresh/status` (SPEC-board-sync-automation, v4.3.0) |
|---|---|---|
| File | `src/python/research/research_board.py` (137 lines) | `src/python/core/board.py` (535 lines) |
| Data source | Atlas only (`atlas project list --format json`) | Atlas + `.STATUS` files + vault DB (3-connector merge) |
| Output | `_RESEARCH-BOARD.md` (or stdout) | `_ACTION-BOARD.md`-style file, auto-resolves `Research/00_meta/` sub-vault path |
| Renderer | Pure function, **no timestamps in block** (golden-file/idempotency tested) | Includes a `generated:` timestamp line + richer sections (Act-Now ranked table, leverage/risk scoring, TL;DR/threats/ideas placeholders for LLM augmentation) |
| CLI wiring | `obs research board [--out] [--kind] [--dry-run]` — routes through `obs_research()` in `src/obs.zsh` | `python3 src/python/obs_cli.py board refresh|status [--all] [--vault] [--dry-run] [--json]` |
| **ZSH dispatcher entry** | Present (`"research") obs_research "$@"`) | **Missing** — no `"board")` case in `src/obs.zsh`'s dispatch `case` statement. `obs board refresh` is unreachable via the `obs` shell entrypoint; only the raw `python3 src/python/obs_cli.py board refresh` works today. |
| MCP exposure | None | None |

Both write to the same marker convention (`<!-- obs:board:start -->` / `...:end -->`), both merge-preserve surrounding hand-authored content, both write atomically via `os.replace`. `core/board.py`'s `Merger` prefers `atlas`-sourced records over `.STATUS`-sourced ones on conflict.

`core/board.py`'s `_has_drift()` calls into `core.doctor.Doctor.run_check("sync", ...)` to surface ghost-row drift in the `status` output — the one place the two systems (board + doctor) already talk to each other.

### MCP surface

`src/python/mcp_server.py` exposes 42 `@mcp.tool` functions. None call into `core/board.py` or `research/research_board.py`. Relevant read tools that exist but are board-adjacent: `get_hub_notes`, `get_vault_health`, `get_stale_notes`, `course_show`, `manuscript_show`, `manuscript_stats`. No `board_refresh` / `board_status` MCP tool exists — board refresh is CLI-only.

### What shipped since the June 30 brainstorm

Git log for the two board files:
```
89c2165a feat(research board): deterministic atlas->vault renderer + 'obs research board' CLI (SPEC-obs)   [v4.0.0]
5985425b feat(research board): default to research items (manuscripts + programs)
43c90a7b feat: board-sync automation + E2E dogfood expansion                                                [v4.3.0]
e915a3f7 docs: docs audit, skill hardening, board-sync, vault-sync (#73)
```

`43c90a7b` is the direct implementation of **Idea 2** from the June 30 brainstorm ("`obs board refresh` — Native Subcommand"): a first-class `core/board.py` engine with atlas + vault-DB + `.STATUS` connectors, `refresh`/`refresh_all`/`status` methods, and doctor-drift integration — matching the brainstorm's effort estimate (~0.5d) and its call to leverage `doctor --layer sync`. **This is shipped, not still planned.**

### Decisions already locked in by the 2026-06-30 brainstorm (do not re-litigate)

1. **Recommended architecture (Idea 3, "Hybrid Deterministic + AI"): atlas organizes, obs renders, LLM thinks.** Deterministic layer (`obs board refresh`) owns status tables; a separate LLM-augmented pass (`_ACTION-BOARD.md` via the `research--action-board` prompt) owns strategic sections (leverage ranking, threats, sequencing). This is the ADR-stated target architecture — confirmed still true: `core/board.py`'s renderer literally emits `*(LLM augments this section on demand)*` placeholders for TL;DR/ideas/threats/this-week, i.e. the code already encodes the boundary.
2. **Recommended rollout order: 3 → 1 → 2 → 4 → 6.** Idea 3 (process-only, no code) → Idea 1 (launchd auto-refresh chaining) → Idea 2 (native subcommand, now shipped) → Idea 4 (cross-vault board) → Idea 6 (Kanban plugin bridge). Ideas 5 (GitOps) and 7 (watcher daemon) were explicitly deprioritized as over-engineered/risky for a local-only vault.
3. **Idea 1 (launchd auto-refresh chaining `atlas sync --research` → `obs research board --out`) was NOT confirmed shipped** — no launchd plist or `scripts/board-refresh.sh` found in this repo during this session's check. Idea 2 shipped ahead of/instead of Idea 1 being wired into a scheduler.
4. **Idea 4 (cross-vault: Knowledge_Base, Documents) explicitly out of scope for now** — flagged medium effort/medium impact, needs a new renderer; not started.
5. **`_ACTION-BOARD.md` prompt update (Phase 4) is still open** — the brainstorm called for updating `research--action-board.md` to consume `_RESEARCH-BOARD.md`/the new board-refresh output as its primary source rather than re-deriving status tables itself. Not verified as done in this session (prompt file not inspected here — flag for follow-up, don't assume).

---

## Audience Check: Is `obs board` Research-Only or Dev-Tools-Wide?

Both `core/board.py`'s `StatusConnector` and the June 30 doc scope `.STATUS` sources to `~/projects/research` and `~/projects/r-packages/active` only — **not** `~/projects/dev-tools/*`. The board's `AtlasConnector` pulls `kind in (manuscript, program)` — again research-domain kinds, not dev-tools projects. So **the distinction holds**: `obs board` is purpose-built for the research-vault dashboard workflow (manuscripts, programs, R packages), not a dev-tools project tracker. Atlas's `program` kind is the closest dev-tools-adjacent hook, but nothing in the current connector set ingests dev-tools `.STATUS` files (e.g. this repo's own `.STATUS`) into a board.

---

## Quick Wins (< 30 min)

1. **Wire `"board")` into `src/obs.zsh`'s dispatcher** — add a `obs_board()` wrapper (mirrors `obs_research`/`obs_vault`) and a `"board") obs_board "$@" ;;` case. Right now `obs board refresh` silently falls through to "Unknown command" via the shell entrypoint even though the Python CLI fully supports it — a real, user-facing gap, not a hypothetical.
2. **Add `obs board` to `obs help`** — `src/obs.zsh`'s help text (grep showed only `obs health` listed near line 160) doesn't mention `board` or `research board` subcommands at all.

## Medium Effort (1-2 hrs)

- [ ] Implement Idea 1 from the June 30 doc: a `scripts/board-refresh.sh` + launchd plist chaining `atlas sync --research` → `obs board refresh --all` (supersedes the doc's `obs research board --out` sketch — use the newer, richer `obs board refresh` now that it exists). Schedule weekly, mirroring the existing `com.data-wise.atlas-sync` cadence.
- [ ] Verify/update the `research--action-board` prompt (Phase 4 from the June 30 doc) to read the deterministic board output as its primary data source instead of re-deriving status tables — closes the loop the hybrid architecture calls for.
- [ ] Decide whether `research/research_board.py` (the older, timestamp-free renderer) should be deprecated now that `core/board.py` supersedes it with richer connectors — currently both ship and both are independently CLI-wired, which is duplicate surface area a future contributor could trip on.

## Long-term (future sessions)

- [ ] Idea 4 — cross-vault board for Knowledge_Base (2641 notes, 0 boards) and Documents (3529 notes), per the June 30 effort/impact table (medium effort, medium impact, needs a new renderer).
- [ ] Consider an MCP `board_status` (read-only) tool exposing `BoardEngine.status()` so Claude Code / Cowork sessions can check board staleness without shelling out — natural extension given 42 tools already exist and `get_vault_health`/`get_stale_notes` set the precedent for read-only diagnostic tools.
- [ ] Idea 6 (Kanban plugin bridge) — still lowest-priority per the recommended order; revisit only after 1/2/4 land.

## Recommended Next Step

→ Start with #1 (wire `board` into `src/obs.zsh`) because it's a genuine functionality gap discovered in this session — `obs board refresh` was shipped in v4.3.0 with full Python CLI support but is unreachable through the documented `obs` shell entrypoint, meaning the feature the June 30 brainstorm recommended (and that shipped) isn't actually usable the way users invoke every other `obs` command.
