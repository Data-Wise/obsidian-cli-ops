# Plan: Board Sync Next Steps (2026-07-01)

> [!success] RESOLVED (2026-07-01) — Phases 1-4 complete, shipped in v4.3.0
> Phase 1 (dispatcher wiring, PR #80), Phase 2 (launchd automation, found already shipped
> pre-session in e915a3f7), Phase 3 (action-board prompt, verified already correct, PR #81),
> Phase 4 (dedup decision, keep both, PR #82) — all done. Held-for-later items (Idea 4
> cross-vault board, Idea 6 Kanban bridge, MCP `board_status` tool) remain open for a future
> session. See `.STATUS` for the release record.

> Derived from `BRIEF-board-sync-status.md` (this session) and `brainstorm-board-sync-2026-06-30.md`
> (architecture decisions, not re-litigated here). Plan only — no execution yet.

---

## Sequencing rationale

The June 30 brainstorm's recommended rollout order was **3 → 1 → 2 → 4 → 6**. Idea 3
(process/architecture, no code) is done by definition — it's the design the code already
follows. Idea 2 (native `obs board refresh` subcommand) shipped in v4.3.0, ahead of Idea 1.
This plan resumes at the point actually reached: **fix the gap the shipped feature has, then
pick up Idea 1 where the June 30 doc left it, then close the remaining hybrid-architecture
loop (Phase 4 prompt update), then reassess Ideas 4/6.**

## Phase 1 — Close the shipped-but-unreachable gap (quick win, do first)

- [ ] **1.1** Add `obs_board()` wrapper to `src/obs.zsh`, mirroring the existing `obs_research()`/`obs_vault()` pattern
- [ ] **1.2** Add `"board") obs_board "$@" ;;` to the dispatcher `case` statement
- [ ] **1.3** Add `obs board refresh|status` to `obs help` output (currently absent near the `obs health` help line)
- [ ] **1.4** Verify: `obs board status` and `obs board refresh --dry-run` work via the shell entrypoint (not just `python3 src/python/obs_cli.py board ...`)

**Acceptance:** `obs board refresh --all` is reachable through `obs`, matching every other subcommand's invocation pattern. `obs help` lists it.

## Phase 2 — Resume Idea 1 (launchd auto-refresh chaining)

- [ ] **2.1** Write `scripts/board-refresh.sh` chaining `atlas sync --research` → `obs board refresh --all` (supersedes the June 30 doc's `obs research board --out` sketch — use the newer `core/board.py`-backed command now that it exists)
- [ ] **2.2** Add a launchd plist (`com.data-wise.obs-board-refresh` or similar), weekly cadence, mirroring `com.data-wise.atlas-sync`'s existing pattern
- [ ] **2.3** Confirm no conflict/race with the existing `com.data-wise.mediationverse-status-sync` job (per user's research-session-defaults rule — that job already touches `.STATUS`-derived dashboards)

**Acceptance:** board refresh runs unattended on the same cadence atlas-sync does, without manual invocation.

## Phase 3 — Close the hybrid-architecture loop (Phase 4 from June 30 doc, still open)

- [ ] **3.1** Locate and read the `research--action-board` prompt file (not inspected this session — confirm it exists and its current data-sourcing logic)
- [ ] **3.2** Update it to consume `core/board.py`'s deterministic output as primary source, rather than re-deriving status tables itself
- [ ] **3.3** Verify the LLM-augmented sections (`*(LLM augments this section on demand)*` placeholders in `core/board.py`'s renderer) still get filled correctly after the prompt change

**Acceptance:** the hybrid architecture (atlas organizes → obs renders deterministically → LLM augments strategically) is fully wired end-to-end, not just code-shaped for it.

## Phase 4 — Reduce duplicate surface area

- [ ] **4.1** Decide: deprecate `research/research_board.py` (older, atlas-only, no timestamps) now that `core/board.py` supersedes it with richer connectors? Or keep both intentionally (e.g. if the no-timestamp idempotent variant serves a golden-file-testing use case the newer one doesn't)?
- [ ] **4.2** If deprecating: banner + redirect `obs research board` to call into `core/board.py`, or formally document why both remain

**Acceptance:** a documented decision exists either way — not silent duplicate surface area.

## Held for later (explicitly out of scope this plan)

- **Idea 4** (cross-vault board: Knowledge_Base 2641 notes / Documents 3529 notes, 0 boards today) — medium effort/impact, needs a new renderer. Revisit after Phases 1-3.
- **Idea 6** (Kanban plugin bridge) — lowest priority per June 30's order, only after 1/2/4.
- **MCP `board_status` read-only tool** — natural extension (precedent: `get_vault_health`, `get_stale_notes`) but not urgent; consider alongside Phase 4's dedup decision.

## Verification (repo-wide, run before considering any phase done)

```bash
obs board status                                    # Phase 1
obs board refresh --dry-run
obs help | grep -i board                             # Phase 1.3
launchctl list | grep board-refresh                  # Phase 2 (after loading plist)
grep -rn "core.board\|research_board" src/python/     # Phase 4 (confirm call sites before touching)
```

## Recommended entry point

→ **Phase 1** — smallest, highest-confidence, closes a real user-facing gap on a feature that already shipped. Phases 2-4 build on it but are independently schedulable.
