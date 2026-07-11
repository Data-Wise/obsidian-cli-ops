# Implementation Plan: Vault Reorganization Paths Migration (Issue #86)

## Overview
Realign all default path configuration and board resolution settings in the `obsidian-cli-ops` codebase to support the consolidated `Engineering/` and `Research/` folders, deprecating root-level references to `Software_Engineering/`, `Research_Lab/`, and `00_meta/`.

## Architecture Decisions
* **Board Path Fallback:** `src/python/core/board.py` will fall back to `Engineering/_ACTION-BOARD.md` (relative to the vault root) when no explicit board path is specified and `Research/00_meta/_ACTION-BOARD.md` is not present, matching the retirement of the root-level `00_meta/` folder.
* **Project Map Repointing:** Example mappings inside `config/example.project_map.json` will route packages to `Engineering/packages/` and research projects to `Research/`.

## Task List

### Phase 1: Configuration Updates
* **Task 1:** Update `config/example.project_map.json` references.

### Checkpoint: Configuration
* **Task 1 Verification:** Inspect the JSON file and verify no old path names remain.

### Phase 2: Python Code & Unit Tests
* **Task 2:** Update `src/python/core/board.py` fallback path logic.
* **Task 3:** Update `src/python/tests/test_board.py` unit tests.

### Checkpoint: Complete Integration
* **Phase 2 Verification:** Ensure all unit tests run and pass using `pytest`. Run `obs board refresh --dry-run` to verify dry-run output path resolution.

## Risks and Mitigations
| Risk | Impact | Mitigation |
|---|---|---|
| Modifying board path resolution logic breaks existing board sync setups using specific configs | Low | Ensure explicit `board_rel_path` passed to the command continues to take absolute precedence over fallbacks. |

## Open Questions
None.
