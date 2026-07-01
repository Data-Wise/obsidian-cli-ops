# ORCHESTRATE: planning-readme-update

**Status:** Complete
**Base:** dev @ 4674317
**Repo:** obsidian-cli-ops

## Scope

Update `docs/planning/README.md`, which still describes the old "2-file consolidation" philosophy (`.STATUS` + `IDEAS.md` as the only live docs; everything else historical) from the v2.1.0-beta era. It predates and doesn't mention `docs/planning/specs-completed/`, the new archive directory created this session for shipped SPEC files.

## Phases

- [x] **Phase 1: Read current state**
  - Read `docs/planning/README.md` in full
  - `docs/planning/PROPOSAL-planning-doc-consolidation.md` is not present on disk (not a blocker — not needed for the actual edit; proceeding on the directory listing + file contents directly)
  - Confirmed what `docs/planning/` actually contains now: `README.md`, archived files with ARCHIVED banners (`IMPLEMENTATION-ROADMAP.md`, `TODOS.md`, `project-hub.md`, `project-plan.md`), `improvement-suggestions-2026-06-22.md` (reconciled triage, RESOLVED banner), `brainstorm-board-sync-2026-06-30.md` (live), `specs-completed/` (4 archived SPEC files, each with ARCHIVED banner pointing to `.STATUS`), `phases/`, `sessions/`

- [x] **Phase 2: Update README.md**
  - Corrected the "2-file consolidation" framing: `.STATUS` (+ `IDEAS.md`) are called out as live at root; directory now groups content as Archived (banner), Resolved triage, Shipped SPEC files, Phase summaries, Session summaries
  - Added a `specs-completed/` entry describing purpose (shipped `SPEC-*.md` moved here per the SPEC-lifecycle rule in root CLAUDE.md's Git Workflow section, referenced not duplicated) and that files carry ARCHIVED banners back to `.STATUS`
  - Kept proportionate — restructured existing sections/table rather than a full rewrite; removed the stale "Philosophy: Keep It Simple" and "Current Status (Quick Summary)" sections since they described the old 2-file/v2.1.0-beta framing no longer accurate (superseded by `.STATUS`)
  - Removed the stale claim that `SPEC-merge-nexus-cli-v2-2026-06-21.md` is "the active plan" — that work shipped in v4.0.0 per `.STATUS`/specs-completed banners; the file still exists untouched at repo root (out of scope for this task) but README no longer calls it active

## Acceptance Criteria

- [x] README.md no longer implies only 2 files are live/current when more exist
- [x] README.md mentions `specs-completed/` and its purpose
- [x] No content invented — every claim cross-checked against `ls docs/planning/` and `specs-completed/` banner contents

## Verification

Manual read-check only — this is a docs-only update with no automated test gate. Re-read the final README.md and confirm it accurately describes the current directory contents (cross-check with `ls docs/planning/`) before committing.

## Blockers

(none yet)
