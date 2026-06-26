# Vault ↔ DB Sync Reconciliation — Orchestration Plan

> **Branch:** `feature/vault-sync-reconcile`
> **Base:** `feature/spec-vault-sync-reconcile` (carries the spec; both land on `dev` together at PR time)
> **Worktree:** `~/.git-worktrees/obsidian-cli-ops/feature-vault-sync-reconcile`
> **Spec:** `docs/specs/SPEC-vault-sync-reconcile-2026-06-26.md`
> **Version Target:** v4.2.0

## Objective

`scan_vault` is upsert-only with a path-derived note id and no reconcile phase, so the DB
index silently diverges from disk (ghost rows, rename duplicates, stale tags/links, silent
note loss). Add error recording, an opt-in `--prune` mark-and-sweep + per-note reconcile,
and an `obs doctor` `sync` layer — each independently shippable, each red→green tested.

## Phase Overview

| Phase | Increment | Priority | Effort | Status |
|-------|-----------|----------|--------|--------|
| 0 | Pre-check: FK cascade + foreign_keys pragma | Blocking | S | ☐ |
| 1 | S4 — record scan errors, stop silent swallow | High | S | ☐ |
| 2 | S1+S2 prune (`--prune` mark-and-sweep) + S3 link/tag reconcile | High | M | ☐ |
| 3 | `obs doctor` `sync` layer | Medium | M | ☐ |
| 4 | e2e `TestE2ESyncLifecycle` + doctor dogfood | High | M | ☐ |
| 5 | Docs & discoverability | Required | S | ☐ |

> e2e/dogfood for each behavior land **with** that phase (red→green), not deferred wholesale
> to Phase 4. Phase 4 is the *lifecycle integration* suite + the dogfood doctor tests.

---

## Phase 0: Pre-check (blocking — do before Phase 2)

**Scope:** Determine whether prune can rely on cascade or must delete child rows explicitly.

- [ ] 0.1 Inspect `schema/vault_db.sql`: do `links`, `note_tags`, `graph_metrics`,
      `note_embeddings` FKs to `notes(id)` declare `ON DELETE CASCADE`?
- [ ] 0.2 Check `db_manager.get_connection()` — is `PRAGMA foreign_keys=ON` set per
      connection? (SQLite defaults OFF; cascade is inert without it.)
- [ ] 0.3 Decide: rely on cascade (preferred) vs. explicit child-row deletes in prune.
      Record the decision inline in Phase 2 tasks.

**Key files:** `schema/vault_db.sql`, `src/python/db_manager.py`

---

## Phase 1: S4 — record scan errors (ship first)

**Scope:** Stop the silent swallow; make per-note failures observable. Smallest diff,
unblocks visibility for every other phase. Thematic continuation of #65 / PR #66.

- [ ] 1.1 (test-first) `tests/test_vault_scanner.py`: a note that fails to insert is
      counted as an error and reported, not silently dropped; scan still completes.
- [ ] 1.2 Replace `except Exception: continue` (`vault_scanner.py:271`) with: increment an
      `errors` counter, capture `(path, exc_type, message)`, `log.warning`, continue.
- [ ] 1.3 Stop hardcoding `0` in `complete_scan(...)` (`vault_scanner.py:283`) — pass the
      real error count. Add `notes_failed` (+ short failing-path list) to returned stats.
- [ ] 1.4 Verify `scan_history` schema has an error column the count lands in (add if missing).

**Key files:** `src/python/vault_scanner.py`, `src/python/db_manager.py` (`complete_scan`),
`src/python/tests/test_vault_scanner.py`

---

## Phase 2: S1+S2 prune + S3 reconcile

**Scope:** Opt-in mark-and-sweep + always-on per-note link/tag reconcile.

- [ ] 2.1 (test-first) prune deletes only unseen rows; rename leaves exactly one row;
      empty `seen_paths` skips the sweep (safety guard).
- [ ] 2.2 `scan_vault(..., prune: bool = False)`: collect `seen_paths` during the loop.
- [ ] 2.3 After the loop, if `prune` and `seen_paths`: delete `notes WHERE vault_id=? AND
      path NOT IN (<seen>)` (+ child rows per Phase 0 decision). Report `notes_pruned`.
- [ ] 2.4 Safety guard: `seen_paths == 0` → skip sweep, `log.warning` (bad path, not wipe).
- [ ] 2.5 (test-first) S3: removing a `#tag` / `[[link]]` and rescanning drops it.
- [ ] 2.6 Per-note reconcile (always, independent of prune): before re-adding, delete the
      note's `links WHERE source_note_id=?` and `note_tags WHERE note_id=?`, then re-add.
- [ ] 2.7 CLI: `obs scan <vault> [--prune] [--no-prune]` (argparse + `obs.zsh` wrapper).
- [ ] 2.8 MCP: `rescan_vault` gains optional `prune: bool = False` (default additive).

**Key files:** `src/python/vault_scanner.py`, `src/python/db_manager.py`,
`src/python/obs_cli.py`, `src/obs.zsh`, `src/python/mcp_server.py`

---

## Phase 3: `obs doctor` `sync` layer

**Scope:** Content-based (not time-based) FS-vs-DB visibility. Reuses Phase 2's diff.

- [ ] 3.1 (test-first) `test_doctor.py`: `sync-*` checks against a stubbed vault with known
      ghost/missing counts.
- [ ] 3.2 New per-vault `sync` layer checks: `sync-ghosts` (warn), `sync-missing` (warn),
      `sync-errors` (warn/fail from last `scan_history`), `sync-drift` (info summary line).
- [ ] 3.3 Wire into the `DoctorResult` registry + `--layer sync` filtering.

**Key files:** `src/python/core/doctor.py`, `src/python/tests/test_doctor.py`

---

## Phase 4: e2e lifecycle + dogfood

**Scope:** The full create/update/delete/rename lifecycle the existing e2e never exercises.

- [ ] 4.1 `TestE2ESyncLifecycle` (`tests/e2e/test_e2e_mcp.py`):
      `test_delete_on_disk_then_rescan_prunes`, `test_rename_on_disk_no_duplicate`,
      `test_remove_tag_then_rescan_reconciles`,
      `test_unparseable_note_counts_as_error_not_silent`,
      `test_prune_skipped_when_vault_appears_empty`.
- [ ] 4.2 Dogfood: `test_doctor_sync_clean_on_fresh_scan`,
      `test_doctor_sync_detects_injected_ghost` (detector vs ground truth).
- [ ] 4.3 Confirm e2e gating convention (`E2E=1`) is respected; no CI-default breakage.

**Key files:** `src/python/tests/e2e/test_e2e_mcp.py`

---

## Phase 5: Documentation & Discoverability (REQUIRED — final phase)

- [ ] CLI reference — document `obs scan --prune/--no-prune` (`docs_mkdocs/cli-reference.md`, `docs/user/cli-reference.md`, `man/man1/obs.1`)
- [ ] Doctor docs — new `sync` layer + checks (`docs_mkdocs/` doctor page, `MCP_README.md` for `rescan_vault prune`)
- [ ] Tutorial/troubleshooting — "my deleted notes still show up" → `obs scan --prune` (`.claude/rules/troubleshooting.md`)
- [ ] CHANGELOG `docs_mkdocs/changelog.md` `[Unreleased]`
- [ ] Counts: `./scripts/validate-counts.sh` ✓ (new tests bump unit-test floor — reconcile, watch the decade boundary)
- [ ] `.STATUS` next/verified updated
- [ ] N/A: website nav (no new top-level page); skills catalog (no new skill/command family)

---

## Friction Prevention

- **Context first:** read this ORCHESTRATE file + the spec BEFORE any code.
- **Verify location:** confirm CWD is the worktree (`~/.git-worktrees/obsidian-cli-ops/feature-vault-sync-reconcile`), not the main repo. Run `git worktree list` + `pwd`.
- **Phase 0 is blocking:** do not write the prune DELETE until the cascade/pragma question is resolved — a wrong answer orphans child rows (a new sync bug).
- **TDD:** every behavioral change is test-first (red→green). Run pytest from `src/python/`.
- **No autonomous starts:** STOP and confirm after each phase.
- **Count-floor gotcha:** adding tests can cross a decade boundary (360→370); run `validate-counts.sh --fix` in Phase 5, don't hand-edit count strings.
- **Branch hygiene:** delete this ORCHESTRATE file before merging the feature to `dev`.

## Acceptance Criteria

- [ ] S1: a note deleted on disk is gone from the index after `obs scan --prune`.
- [ ] S2: renaming a note on disk yields exactly one DB row after `--prune` (no ghost).
- [ ] S3: removing a tag/link and rescanning drops it from the index.
- [ ] S4: a note that fails to index is counted + reported; `scan_history` error count > 0.
- [ ] S5: `obs doctor --layer sync` reports content-based drift (`disk=N db=M`).
- [ ] `--prune` is opt-in; default scan stays additive; empty-vault guard prevents wipes.
- [ ] Full suite green (`cd src/python && python3 -m pytest tests/`); e2e green under `E2E=1`.
- [ ] Documentation & Discoverability phase complete.

## Commit Strategy

- Phase 0: `chore(sync): confirm FK cascade + foreign_keys pragma` (or schema fix `fix(db):`)
- Phase 1: `fix(scan): record per-note scan errors instead of silent swallow (S4)`
- Phase 2: `feat(scan): opt-in --prune reconcile + per-note link/tag reconcile (S1/S2/S3)`
- Phase 3: `feat(doctor): sync layer — ghosts/missing/errors/drift`
- Phase 4: `test(e2e): vault sync lifecycle + doctor sync dogfood`
- Phase 5: `docs(sync): --prune, doctor sync layer, troubleshooting, changelog`

## Verification

After each phase:

```bash
cd src/python && python3 -m pytest tests/ -q          # unit + integration
E2E=1 python3 -m pytest tests/e2e/ -q                 # e2e (Phase 4)
python3 core/doc_counts.py                            # count alignment (Phase 5)
```

## Session Instructions

### Context

You are in the **obsidian-cli-ops worktree** for the vault-sync-reconcile feature. The spec
(`docs/specs/SPEC-vault-sync-reconcile-2026-06-26.md`) has the full design + the S1–S5 table.

### How to Start

```bash
cd ~/.git-worktrees/obsidian-cli-ops/feature-vault-sync-reconcile
claude
```

On session start, paste:

> Read `ORCHESTRATE-vault-sync-reconcile.md` and the spec at
> `docs/specs/SPEC-vault-sync-reconcile-2026-06-26.md`. Do Phase 0 (the blocking
> cascade/pragma pre-check) and report before starting Phase 1.

### Phase-by-Phase

1. Read the current state of each file listed in the phase.
2. Implement per the spec design, test-first.
3. Run verification after each phase.
4. Commit in logical groups (see Commit Strategy).
5. STOP and confirm before the next phase.
