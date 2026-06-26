# SPEC: Vault ↔ DB Index Sync Reconciliation

**Status:** Draft
**Created:** 2026-06-26
**Author:** Investigation (debugger session)
**Related:** #65 (silent note drop — one instance of S4), PR #66 (frontmatter-title `NOT NULL` fix), `SPEC-scanner-scan-verb-insert-heading-2026-06-23.md`
**Target:** v4.2.0 (alongside or after 5.1 vault CRUD)

> **⚠️ Phase-0 correction (2026-06-26):** empirical check (`INSERT OR REPLACE` fires
> `ON DELETE CASCADE`, verified) revised this spec. **S3 below is a FALSE POSITIVE** — the
> REPLACE+cascade in `add_note` already reconciles links/tags on rescan, so no S3 work is
> needed. Two real bugs were found instead: **N1** (the cascade wipes `note_embeddings` on
> every rescan) and **N2** (`content_hash` is never used to skip unchanged notes — the root
> of N1 and of redundant rewrites). Implemented scope = **S1/S2/S4/S5 + N1/N2, S3 dropped**.
> Prune relies on the confirmed FK cascade (§6 open question closed). See
> `ORCHESTRATE-vault-sync-reconcile.md` for the authoritative phase plan.

---

## 1. Problem

`VaultScanner.scan_vault` (`src/python/vault_scanner.py:227-286`) is **upsert-only**: it
walks `rglob('*.md')` on disk and `INSERT OR REPLACE`s each file. It never computes the
set difference `DB_notes − disk_notes`, so the index can only grow or update — never
shrink or reconcile. Combined with a **path-derived note id**
(`_generate_id(f"{vault_id}:{path}")`, `db_manager.py:295`), this yields five sync bugs
where the `obs` index silently diverges from the actual vault.

### Symptoms

| # | Symptom | Mechanism | Severity |
|---|---------|-----------|----------|
| **S1** | Deleted notes never disappear | File removed on disk → DB row persists. Still surfaces in `search_notes`, `get_vault_stats` counts, graph metrics (PageRank over a phantom node), and as a valid link target. Grows monotonically. | High |
| **S2** | Rename/move = phantom duplicate | id is path-based. `a.md`→`b.md`: `b.md` inserted as new, `a.md` row orphaned forever. Two rows for one logical note; `[[a]]` resolves to the ghost. | High |
| **S3** | Removed tags/links persist | On modified-note rescan, `add_note` REPLACEs the note row but the scan loop only `add_link`/`add_note_tag` (INSERT OR IGNORE, `vault_scanner.py:264-269`) — it never clears the note's prior links/tags first. Delete a `#tag` or `[[link]]`, rescan → still indexed. | Medium |
| **S4** | Silent per-note data loss | `except Exception: continue` (`vault_scanner.py:271`) drops any note that fails to parse/insert; `complete_scan(..., 0)` hardcodes the error count to 0 (`:283`). Scan reports success while N notes are missing. #65's `NOT NULL` crash was one instance swallowed here. | High |
| **S5** | Staleness is time-based, not content-based | `check_index_staleness` (`vault_manager.py:515`) only knows "last scan >24h ago" — never "disk has 12 files the DB doesn't." | Medium |

### Root cause

A single architectural gap — **the scan has no reconcile/sweep phase**. The fix is a
mark-and-sweep: snapshot the set of disk paths seen during the scan, then sweep the DB
for rows not in that set. One sweep closes S1 and S2 together; a per-note link/tag
reconcile closes S3; recording scan errors closes S4; the sweep's diff feeds S5.

---

## 2. Goals / Non-goals

**Goals**
- Make `obs scan` able to bring the DB index into exact agreement with disk.
- Stop silent note loss; make scan errors first-class and observable.
- Give `obs doctor` content-based (not just time-based) sync visibility.
- Cover the full create/update/**delete**/**rename** lifecycle in e2e + dogfood tests.

**Non-goals**
- Filesystem watching / live incremental sync (future; this is scan-triggered).
- Changing the path-derived id scheme (rename is handled by sweep, not id stability).
- AI involvement — all reconciliation is deterministic.

---

## 3. Design

### 3.1 Mark-and-sweep prune (S1, S2) — **opt-in**

Decision: **opt-in via `obs scan --prune`** (default stays additive in v4.2.0). Rationale:
a mis-pointed vault path (e.g. iCloud not yet materialized, wrong mount) would otherwise
delete rows for files that exist but aren't currently visible. Promote to default with a
`--no-prune` escape in a later major once confidence is established.

- `scan_vault(..., prune: bool = False)`.
- During the scan, collect `seen_paths: set[str]` of every relative path successfully processed.
- After the loop, when `prune` is true:
  `DELETE FROM notes WHERE vault_id=? AND path NOT IN (<seen_paths>)`.
- Cascade: deleting a note must also remove its `links` (as source), `note_tags`,
  `graph_metrics`, and `note_embeddings` rows (verify FK `ON DELETE CASCADE` in
  `schema/vault_db.sql`; if absent, delete explicitly or add the cascade).
- **Safety guard:** if `len(seen_paths) == 0` (vault appears empty — likely a bad path,
  not a genuinely empty vault), **skip the sweep** and emit a warning rather than wiping
  the index. Genuine empty-vault is rare and a no-op prune is the safe failure mode.
- Report pruned count in scan stats: `notes_pruned`.

### 3.2 Per-note link/tag reconcile (S3)

On every note upsert (not just prune), clear the note's prior derived rows before
re-adding, so removed tags/links don't linger:
- Before re-adding: `DELETE FROM links WHERE source_note_id=?` and
  `DELETE FROM note_tags WHERE note_id=?` for the note being rescanned.
- Then re-add from current content. Idempotent and content-faithful.
- Keep this independent of `--prune` — it's about *modified* notes, always correct.

### 3.3 Record scan errors (S4) — **do this first**

- Replace `except Exception: continue` with: increment an `errors` counter, capture
  `(path, exception_type, message)`, and `log.warning` it. Do **not** abort the scan.
- Stop hardcoding `0` in `complete_scan(...)`; pass the real error count.
- Surface in scan stats: `notes_failed` + a short list of failing paths.
- This is the highest-leverage change: it makes every other sync bug *observable*, and
  it's the smallest diff. Land it first (natural extension of the #65/PR #66 theme).

### 3.4 `obs doctor` — new `sync` layer (per registered vault)

Each check does a cheap `rglob` + `SELECT path` + set diff:

| Check id | Verdict | Catches | Remediation hint |
|----------|---------|---------|------------------|
| `sync-ghosts` | warn | S1/S2 — DB rows whose `path` is gone from disk | `obs scan <vault> --prune` |
| `sync-missing` | warn | S4 — `*.md` on disk absent from DB | `obs scan <vault>` (re-scan; check logs for errors) |
| `sync-errors` | warn/fail | last `scan_history` row recorded errors (post-S4) | inspect failing paths in scan log |
| `sync-drift` | info | summary line: `disk=N db=M (X ghost, Y missing)` | — |

Fits the existing `DoctorResult` registry and `--layer` filtering. Deterministic, no AI.

### 3.5 CLI / ZSH surface

- `obs scan <vault> [--prune] [--no-prune]` (argparse + `obs.zsh` wrapper, three-layer rule).
- MCP `rescan_vault` tool gains an optional `prune: bool = False` parameter (default
  additive, matching CLI default).

---

## 4. Tests (red → green per fix)

### 4.1 e2e — new `TestE2ESyncLifecycle` in `tests/e2e/test_e2e_mcp.py`

Real temp vault, real scan; all currently **fail** (proving the bug before the fix):
- `test_delete_on_disk_then_rescan_prunes` — scan→N, `rm` a file, rescan `--prune`→N-1, note gone from `search`/`list`. (S1)
- `test_rename_on_disk_no_duplicate` — scan, `mv a.md b.md`, rescan `--prune`→exactly one row, no `a.md` ghost. (S2)
- `test_remove_tag_then_rescan_reconciles` — note with `#x`, scan, strip `#x`, rescan→tag absent. (S3)
- `test_unparseable_note_counts_as_error_not_silent` — plant a note that trips the swallow, rescan→`scan_history` error count > 0 and failure reported. (S4)
- `test_prune_skipped_when_vault_appears_empty` — point at an empty/bad dir → index **not** wiped, warning emitted. (3.1 safety guard)

### 4.2 dogfood — real `obs` against a fixture vault

The integration the v4.0.0 `last_scan` crash slipped through (unit stubs missed it):
- `test_doctor_sync_clean_on_fresh_scan` — fresh scan → `obs doctor --layer sync --json` clean, `ghosts=0 missing=0`.
- `test_doctor_sync_detects_injected_ghost` — scan, delete a file on disk **without** rescanning → `obs doctor --layer sync` flags exactly 1 ghost (detector vs ground truth).

### 4.3 unit

- `vault_scanner`: `seen_paths` collection; prune deletes only unseen rows; empty-set guard.
- `db_manager`: cascade delete removes links/tags/metrics/embeddings for a pruned note.
- `doctor`: `sync-*` checks against a stubbed vault with known ghost/missing counts.

---

## 5. Sequencing

1. **S4 (record errors, stop silent swallow)** — smallest, makes everything else visible. Ships first; thematically continues #65/PR #66.
2. **Mark-and-sweep `--prune` (S1+S2)** + **link/tag reconcile (S3)**.
3. **`obs doctor` `sync` layer** — reuses the disk/DB diff from step 2.
4. **e2e + dogfood** land alongside each fix (red→green).

Each step is independently shippable and independently testable.

---

## 6. Open questions

- **Cascade**: does `schema/vault_db.sql` already declare `ON DELETE CASCADE` on
  `links`/`note_tags`/`graph_metrics`/`note_embeddings` FKs, and is
  `PRAGMA foreign_keys=ON` set per connection? If not, prune must delete child rows
  explicitly (or the schema needs the cascade + pragma). **Verify before implementing.**
- **Rename detection vs prune**: sweep treats rename as delete-old + add-new (correct
  index, but loses the old note's `graph_metrics`/embeddings). Acceptable for v4.2.0;
  content-hash-based rename *detection* (preserve metrics across a move) is a future
  enhancement.
- **`--prune` default flip**: which release promotes prune to default-on?
