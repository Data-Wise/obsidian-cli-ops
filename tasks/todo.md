# Task List: Vault Reorganization Path Migration (Issue #86)

## Task 1: Migrate config/example.project_map.json
**Description:** Update project map to use new vault layout: `Engineering/packages/` for R packages, `Research/` for research projects.

**Acceptance criteria:**
- [x] No occurrences of `Software_Engineering` or `Research_Lab` in `config/`.
- [x] Packages map to `Engineering/packages/`, research maps to `Research/`.

**Verification:**
- [x] Inspect `config/example.project_map.json`.

**Dependencies:** None
**Files likely touched:** `config/example.project_map.json`
**Estimated scope:** S (1 file)

---

## Task 2: Migrate board.py fallback path
**Description:** Update `_resolve_board_path` in `src/python/core/board.py` to use `Engineering/_ACTION-BOARD.md` instead of `00_meta/_ACTION-BOARD.md` for both the sub-vault candidate and the vault-root fallback.

**Acceptance criteria:**
- [x] Sub-vault candidate resolves to `Research/Engineering/_ACTION-BOARD.md`.
- [x] Vault-root fallback resolves to `Engineering/_ACTION-BOARD.md`.

**Verification:**
- [x] Run `pytest src/python/tests/test_board.py`.

**Dependencies:** None
**Files likely touched:** `src/python/core/board.py`, `src/python/tests/test_board.py`
**Estimated scope:** S (2 files)

---

## Checkpoint: Final Integration
- [x] All 520 pytest tests pass cleanly.
- [x] No stale `Software_Engineering`, `Research_Lab`, or `00_meta` references in `src/` or `config/`.
