# Task List: Vault Reorganization Paths Migration (Issue #86)

## Task 1: Update Example Project Map Config
**Description:** Update `config/example.project_map.json` to repoint mappings from the retired `Research_Lab/` directory to `Engineering/packages/` or `Research/`.

**Acceptance criteria:**
- [x] No references to `Research_Lab` or `Software_Engineering` remain in `config/example.project_map.json`.
- [x] RMediation and CausalMed packages map under `Engineering/packages/`.
- [x] Sequential Mediation maps under `Research/`.

**Verification:**
- [x] Manual check: Inspect content of `config/example.project_map.json`.

**Dependencies:** None

**Files likely touched:**
- `config/example.project_map.json`

**Estimated scope:** XS (1 file)

---

## Task 2: Repoint Board Path Fallback Logic
**Description:** Update `src/python/core/board.py` fallback path resolution to fall back to `Engineering/_ACTION-BOARD.md` instead of `00_meta/_ACTION-BOARD.md` when no explicit directory is found.

**Acceptance criteria:**
- [x] Fallback path resolved returns `vault_root / "Engineering" / "_ACTION-BOARD.md"`.
- [x] The logic still checks for `Research/00_meta/_ACTION-BOARD.md` as an active option first.

**Verification:**
- [x] Python unit tests pass (after updating test assertions).

**Dependencies:** None

**Files likely touched:**
- `src/python/core/board.py`

**Estimated scope:** S (1 file)

---

## Task 3: Update Pytest Board Tests
**Description:** Update unit test assertions in `src/python/tests/test_board.py` that check the fallback paths to assert they match `Engineering/_ACTION-BOARD.md`.

**Acceptance criteria:**
- [x] Unit tests assert `resolved == tmp_path / "Engineering" / "_ACTION-BOARD.md"`.

**Verification:**
- [x] Running tests passes: `pytest src/python/tests/test_board.py`

**Dependencies:** Task 2

**Files likely touched:**
- `src/python/tests/test_board.py`

**Estimated scope:** S (1 file)

---

## Checkpoint: Final Integration
- [x] All unit tests pass cleanly: `pytest`
- [x] Dry-run command executes successfully: `obs board refresh --dry-run`
