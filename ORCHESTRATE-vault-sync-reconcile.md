# Vault ↔ DB Sync Reconciliation — Orchestration Plan (rev. Phase 0)

> **Branch:** `feature/vault-sync-reconcile`
> **Base:** `feature/spec-vault-sync-reconcile` (carries the spec; both land on `dev` together at PR time)
> **Worktree:** `~/.git-worktrees/obsidian-cli-ops/feature-vault-sync-reconcile`
> **Spec:** `docs/specs/SPEC-vault-sync-reconcile-2026-06-26.md` (see correction banner re: S3/N1/N2)
> **Version Target:** v4.2.0

## Phase 0 Findings (empirically verified — these revise the spec)

- **PRAGMA + cascade confirmed:** `PRAGMA foreign_keys = ON` on both connection paths
  (`db_manager.py:54,76`); all child FKs to `notes(id)` cascade — `links.source_note_id`
  CASCADE, `links.target_note_id` SET NULL (correct: incoming links break, not delete),
  `graph_metrics`/`note_tags`/`note_embeddings` CASCADE. **⇒ prune = one `DELETE FROM notes`;
  no explicit child deletes** (spec §6 open question closed).
- **S3 is a FALSE POSITIVE — dropped.** `add_note` uses `INSERT OR REPLACE`, which in SQLite
  deletes the conflicting row and **fires `ON DELETE CASCADE`** (verified: post-REPLACE
  `tags=0`). The scan loop REPLACEs (`vault_scanner.py:253`) *then* re-adds current links/tags
  (`:264-269`), so removed tags/links already reconcile. No S3 work needed.
- **NEW N1 (real):** that same cascade **wipes `note_embeddings` on every rescan**, and the
  loop re-`add_note`s every file unconditionally — so one `obs scan` destroys the whole
  embedding cache → full recompute (latency + paid-API cost) next AI op.
- **NEW N2 (root of N1):** `content_hash` is stored but never used to skip unchanged notes
  (`existing_note` at `:247` only feeds the added/updated counter). A content-hash
  short-circuit fixes N1 and makes scans cheap.

## Objective

Close the vault↔DB sync gaps: silent note loss (S4), no prune of deleted/renamed notes
(S1/S2), embedding-cache destruction + redundant rewrites (N1/N2), and time-only staleness
(S5). Opt-in `--prune`; all reconciliation deterministic.

## Phase Overview

| Phase | Increment | Priority | Effort | Status |
|-------|-----------|----------|--------|--------|
| 1 | S4 — record scan errors, stop silent swallow | High | S | ☐ |
| 2 | N1/N2 — content-hash short-circuit, preserve embeddings | High | M | ☐ |
| 3 | S1/S2 — opt-in `--prune` mark-and-sweep (relies on cascade) | High | M | ☐ |
| 4 | S5 — `obs doctor` `sync` layer | Medium | M | ☐ |
| 5 | e2e `TestE2ESyncLifecycle` + doctor dogfood | High | M | ☐ |
| 6 | Docs & discoverability + count reconcile | Required | S | ☐ |

All phases are **sequential** (1–3 share `vault_scanner.py`). TDD throughout; pytest from
`src/python/`. Each phase commits on `feature/vault-sync-reconcile` (no push).

---

## Phase 1: S4 — record scan errors

- [ ] 1.1 (test-first) a note that fails to insert is counted + reported, scan still completes.
- [ ] 1.2 Replace `except Exception: continue` (`vault_scanner.py:271`) → increment `errors`,
      capture `(path, exc_type, msg)`, `log.warning`, continue.
- [ ] 1.3 Stop hardcoding `0` in `complete_scan(...)` (`:283`); pass real error count. Add
      `notes_failed` (+ failing paths) to returned stats. Verify `scan_history` has an error column.

**Files:** `vault_scanner.py`, `db_manager.py`, `tests/test_vault_scanner.py`, `schema/vault_db.sql` (if column missing)

## Phase 2: N1/N2 — content-hash short-circuit + embedding preservation

- [ ] 2.1 (test-first) rescanning an UNCHANGED note (a) does not delete its `note_embeddings`
      row, (b) is counted as skipped/unchanged, (c) leaves links/tags intact.
- [ ] 2.2 In the scan loop, compute the new content_hash and compare with `existing_note`'s
      stored hash; if equal, **skip `add_note`** (and the link/tag re-add) — only refresh
      cheap metadata if needed. This avoids the REPLACE→cascade that nukes embeddings.
- [ ] 2.3 Ensure CHANGED notes still REPLACE (cascade-clear) and re-add — preserves the S3
      self-heal. Add `notes_unchanged` to stats.

**Files:** `vault_scanner.py`, `db_manager.py` (expose stored hash via `get_note_by_path` if not already), `tests/test_vault_scanner.py`, `tests/test_embedding_cache.py`

## Phase 3: S1/S2 — opt-in `--prune` mark-and-sweep

- [ ] 3.1 (test-first) prune deletes only unseen rows; rename → exactly one row; empty
      `seen_paths` → sweep skipped (safety guard); cascade removes child rows.
- [ ] 3.2 `scan_vault(..., prune=False)`: collect `seen_paths` during the loop.
- [ ] 3.3 After loop, if `prune and seen_paths`: `DELETE FROM notes WHERE vault_id=? AND path
      NOT IN (<seen>)` (cascade handles children). Report `notes_pruned`.
- [ ] 3.4 Safety guard: empty `seen_paths` → skip + `log.warning` (bad path, not wipe).
- [ ] 3.5 CLI `obs scan <vault> [--prune] [--no-prune]` (argparse + `obs.zsh`).
- [ ] 3.6 MCP `rescan_vault` gains `prune: bool = False` (default additive).

**Files:** `vault_scanner.py`, `db_manager.py`, `obs_cli.py`, `src/obs.zsh`, `mcp_server.py`, tests

## Phase 4: S5 — `obs doctor` `sync` layer

- [ ] 4.1 (test-first) `sync-*` checks vs a stubbed vault with known ghost/missing counts.
- [ ] 4.2 Per-vault `sync` layer: `sync-ghosts` (warn, S1/S2), `sync-missing` (warn, S4),
      `sync-errors` (warn/fail from last `scan_history`), `sync-drift` (info summary).
- [ ] 4.3 Wire into the `DoctorResult` registry + `--layer sync`.

**Files:** `core/doctor.py`, `tests/test_doctor.py`

## Phase 5: e2e + dogfood

- [ ] 5.1 `TestE2ESyncLifecycle` (`tests/e2e/test_e2e_mcp.py`): delete→prune, rename→no-dup,
      unparseable→error-not-silent, empty-vault→no-wipe, **unchanged→embeddings-survive (N1)**.
- [ ] 5.2 Dogfood: `test_doctor_sync_clean_on_fresh_scan`, `test_doctor_sync_detects_injected_ghost`.
- [ ] 5.3 Respect `E2E=1` gating; no CI-default breakage.

**Files:** `tests/e2e/test_e2e_mcp.py`

## Phase 6: Docs & discoverability

- [ ] CLI ref: `obs scan --prune/--no-prune` (`docs_mkdocs/cli-reference.md`, `docs/user/cli-reference.md`, `man/man1/obs.1`)
- [ ] Doctor docs: `sync` layer; `MCP_README.md` `rescan_vault prune`
- [ ] Troubleshooting: "deleted notes still show up" → `--prune`; "AI re-embeds everything" → fixed by N2 (`.claude/rules/troubleshooting.md`)
- [ ] CHANGELOG `docs_mkdocs/changelog.md` `[Unreleased]`; `.STATUS`
- [ ] `scripts/validate-counts.sh --fix` (new tests cross the unit-test floor — reconcile)

## Acceptance Criteria

- [ ] S1: note deleted on disk gone from index after `obs scan --prune`.
- [ ] S2: rename → exactly one DB row after `--prune` (no ghost).
- [ ] S4: failed note counted + reported; `scan_history` error count > 0.
- [ ] N1: rescanning an unchanged note preserves its `note_embeddings` row.
- [ ] N2: unchanged notes are skipped (not re-REPLACEd); `notes_unchanged` reported.
- [ ] S5: `obs doctor --layer sync` reports content-based drift.
- [ ] `--prune` opt-in; default additive; empty-vault guard prevents wipes.
- [ ] Full suite green (`cd src/python && python3 -m pytest tests/`); e2e green under `E2E=1`.
- [ ] Docs phase complete; `validate-counts.sh` ✓.

## Friction Prevention

- TDD, test-first, red→green; run pytest from `src/python/`.
- Phases 1–3 edit `vault_scanner.py` — strictly sequential, no parallel edits.
- Prune relies on cascade (Phase 0 confirmed) — do NOT add redundant child deletes.
- Count-floor gotcha: new tests may cross a decade; `validate-counts.sh --fix`, don't hand-edit.
- Delete this ORCHESTRATE file before merging to `dev`.

## Commit Strategy

- P1 `fix(scan): record per-note scan errors instead of silent swallow (S4)`
- P2 `fix(scan): content-hash short-circuit preserves embedding cache (N1/N2)`
- P3 `feat(scan): opt-in --prune reconcile of deleted/renamed notes (S1/S2)`
- P4 `feat(doctor): sync layer — ghosts/missing/errors/drift (S5)`
- P5 `test(e2e): vault sync lifecycle + doctor sync dogfood`
- P6 `docs(sync): --prune, doctor sync layer, troubleshooting, changelog`

## Verification

```bash
cd src/python && python3 -m pytest tests/ -q
E2E=1 python3 -m pytest tests/e2e/ -q          # Phase 5
python3 core/doc_counts.py                     # Phase 6
```
