# ORCHESTRATE: planning-readme-update

**Status:** Not started
**Base:** dev @ 4674317
**Repo:** obsidian-cli-ops

## Scope

Update `docs/planning/README.md`, which still describes the old "2-file consolidation" philosophy (`.STATUS` + `IDEAS.md` as the only live docs; everything else historical) from the v2.1.0-beta era. It predates and doesn't mention `docs/planning/specs-completed/`, the new archive directory created this session for shipped SPEC files.

## Phases

- [ ] **Phase 1: Read current state**
  - Read `docs/planning/README.md` in full
  - Read `docs/planning/PROPOSAL-planning-doc-consolidation.md` (untracked scratch file, already on disk — for context on what changed this session, do not edit or delete it)
  - Confirm what `docs/planning/` actually contains now: `README.md`, archived files with ARCHIVED banners (`IMPLEMENTATION-ROADMAP.md`, `TODOS.md`, `project-hub.md`, `project-plan.md`), `improvement-suggestions-2026-06-22.md` (reconciled triage), `brainstorm-board-sync-2026-06-30.md` (live), `specs-completed/` (new, 4 archived SPEC files), `phases/`, `sessions/`

- [ ] **Phase 2: Update README.md**
  - Correct the "2-file consolidation" framing to reflect current reality: `.STATUS` is still the live source of truth, but the "one other live file" framing needs updating (multiple docs now coexist: archived-with-banners, resolved triage, live brainstorm, and now a `specs-completed/` archive)
  - Add a line describing `specs-completed/`: what it's for (shipped SPEC files moved here per the SPEC-lifecycle rule now in root CLAUDE.md's Git Workflow section — do not duplicate that rule's full text, just reference it), and that files there carry ARCHIVED banners pointing back to `.STATUS`
  - Keep the update proportionate — this is a short index/README, not a full rewrite. Preserve any content that's still accurate.

## Acceptance Criteria

- README.md no longer implies only 2 files are live/current when more exist
- README.md mentions `specs-completed/` and its purpose
- No content invented — every claim traceable to what's actually in `docs/planning/` right now

## Verification

Manual read-check only — this is a docs-only update with no automated test gate. Re-read the final README.md and confirm it accurately describes the current directory contents (cross-check with `ls docs/planning/`) before committing.

## Blockers

(none yet)
