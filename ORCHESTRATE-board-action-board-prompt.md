# ORCHESTRATE: board-action-board-prompt

**Status:** Not started
**Base:** dev @ 3903fb3
**Repo:** obsidian-cli-ops

## Scope

Phase 3 of `docs/planning/PLAN-board-sync-next-steps.md`: the 2026-06-30 brainstorm
(`docs/planning/brainstorm-board-sync-2026-06-30.md`) called for updating the
`research--action-board` prompt to consume the deterministic board output (`core/board.py`)
as its primary data source, instead of re-deriving status tables itself — this closes the
hybrid-architecture loop (atlas organizes → obs renders deterministically → LLM augments
strategically). This was flagged as "not verified as done" in this session's research —
the prompt file was never actually inspected.

## Phases

- [ ] **Phase 1: Locate the prompt**
  - Search for `research--action-board` or `action-board` across the repo and any Claude
    Code plugin/skill directories this project might reference (check `.claude/`, any
    `commands/` or `skills/` dirs, and the savant/research plugin paths mentioned in the
    session's system context if relevant — but start with a repo-local grep first:
    `grep -rln "action-board" . --include="*.md" 2>/dev/null`)
  - If the prompt genuinely doesn't exist in this repo (it may live in a sibling plugin
    repo like `savant` or `craft`), STOP here, do not guess a path or invent one — write
    a blocker note in this file stating where you looked and that it wasn't found, and
    do not modify anything.

- [ ] **Phase 2: Read and assess**
  - If found, read the prompt file in full
  - Determine its current data-sourcing logic: does it re-derive status tables from raw
    `.STATUS`/atlas data itself, or does it already reference `core/board.py`'s output?
  - Read `core/board.py`'s renderer output format (the `_ACTION-BOARD.md`-style file,
    including the `*(LLM augments this section on demand)*` placeholders) to understand
    what "consuming it as primary source" should mean concretely

- [ ] **Phase 3: Update (only if genuinely needed)**
  - If the prompt does NOT yet consume the deterministic board output, update it to read
    from the board-refresh output first, filling only the LLM-augmented sections
    (TL;DR, ideas, threats, this-week) rather than regenerating the whole table
  - If it already does this correctly, leave it alone and just document that in this file
    — do not make cosmetic changes to a file that's already correct

## Acceptance Criteria

- Clear documented finding: either (a) the prompt already correctly consumes deterministic
  board output — no change needed, or (b) it was updated to do so, with the specific change
  described
- If the prompt file couldn't be located at all, that's an acceptable outcome too — documented
  as a blocker, not guessed around

## Verification

Manual read-check only — this is a prompt/doc-logic change with no automated test gate
(prompts aren't unit-tested in this repo). If Phase 3 makes a change, re-read the final
prompt and confirm it references the board-refresh output correctly before committing.

## Blockers

(none yet)
