# ORCHESTRATE: board-action-board-prompt

**Status:** Complete — no code/prompt change needed (already correct)
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

- [x] **Phase 1: Locate the prompt**
  - Repo-local grep (`grep -rln "action-board" . --include="*.md"`) found only doc
    *references* to the prompt (SPEC, brainstorm, mkdocs docs) — never the prompt file
    itself. The prompt does not live in this repo.
  - Traced the path via `docs/planning/.../research-automation-and-tasks.md` in the
    Research vault, which names the canonical location as
    `_PromptLibrary/research/research--action-board.md`. That subpath does **not** exist
    under the Research vault. A full `$HOME` find (by-name, so it also matches
    non-materialized iCloud stubs) located the actual file one vault over:
    `/Users/dt/Library/Mobile Documents/iCloud~md~obsidian/Documents/Knowledge_Base/_PromptLibrary/research/research--action-board.md`.
    Confirmed no other copy exists on disk.

- [x] **Phase 2: Read and assess**
  - Read the prompt in full (v3.0, dated 2026-06-30, `status: active`).
  - It already treats `00_meta/_ACTION-BOARD.md` (the `obs board refresh` deterministic
    output) as **PRIMARY source** for status/progress/next columns, explicitly instructs
    "Keep every table and row exactly as-is," and its OUTPUT TEMPLATE marks
    `## 📊 Status at a glance` as "DO NOT MODIFY — copied verbatim from the deterministic
    board." It rewrites only the LLM-thinking sections: TL;DR, Act on now (re-rank only,
    same columns), Future ideas, Threats/scoop-watch, This week.
  - Cross-checked against `core/board.py::BoardRenderer.render()` (lines 258-286): the
    renderer emits placeholder headings `## TL;DR`, `## 💡 Future ideas & new proposals`,
    `## 🔴 Threats / scoop-watch`, `## ⏭️ This week (sequenced)` each with an
    `*(LLM augments this section on demand ...)*` stub, plus the deterministic
    `## 🎯 Act on now` table and `## 📊 Status at a glance`. These headings match the
    prompt's section list verbatim. Line 266 of `board.py` even names the prompt
    directly: `"...augment thinking on demand via \`research--action-board\` prompt."`
  - Conclusion: this is not a stale prompt — it's the **already-updated v3.0** that
    implements exactly the hybrid architecture (atlas organizes → obs renders
    deterministically → LLM augments strategically) the brainstorm called for. The
    "not verified as done" flag from the prior session was a verification gap, not an
    actual gap in the prompt.

- [x] **Phase 3: Update (only if genuinely needed)**
  - No update needed. The prompt already correctly consumes `_ACTION-BOARD.md` as
    primary source and only fills LLM-augmented placeholder sections. No cosmetic or
    substantive change made — leaving the file untouched per the phase's own guidance.

## Acceptance Criteria

- [x] Clear documented finding: (a) the prompt already correctly consumes deterministic
  board output — no change needed. See Phase 2 above for the specific evidence
  (prompt v3.0 text + `core/board.py` renderer cross-check).
- N/A — prompt file was located (Phase 1), so the "couldn't be located" outcome doesn't apply.

## Verification

Manual read-check performed: read `research--action-board.md` in full at
`/Users/dt/Library/Mobile Documents/iCloud~md~obsidian/Documents/Knowledge_Base/_PromptLibrary/research/research--action-board.md`
and cross-referenced its SOURCES/PROCEDURE/OUTPUT TEMPLATE sections against
`src/python/core/board.py`'s `BoardRenderer.render()` output format. They match. No
Phase 3 change was made, so no re-read-after-edit step was required.

## Blockers

(none — prompt located, assessed, and found already correct; no unresolved decisions)

## Note

The prompt file lives in the **Knowledge_Base** Obsidian vault, not the Research vault
that most of its own SOURCES section prefixes reference
(`/Users/dt/Library/.../Documents/Research/`). This is a pre-existing vault-organization
quirk (the prompt is filed under Knowledge_Base's `_PromptLibrary` but reads from
Research), not something this task's scope covers changing.
