# ORCHESTRATE: board-research-board-dedup

**Status:** Not started
**Base:** dev @ 3903fb3
**Repo:** obsidian-cli-ops

## Scope

Phase 4 of `docs/planning/PLAN-board-sync-next-steps.md`: two board renderers currently ship
side by side — `src/python/research/research_board.py` (137 lines, atlas-only, no timestamps,
golden-file/idempotency tested, v4.0.0) and `src/python/core/board.py` (535 lines, atlas +
`.STATUS` + vault DB 3-connector merge, richer output, v4.3.0). This is duplicate surface
area a future contributor could trip on. Decide and document what should happen — this is
primarily an investigation + documented decision, not necessarily a code change.

## Phases

- [ ] **Phase 1: Map current usage**
  - Find every call site of `research_board.py` (CLI wiring in `obs_cli.py`/`obs.zsh`, any
    tests, any docs referencing `obs research board`) via
    `grep -rn "research_board\|obs research board" --include="*.py" --include="*.zsh" --include="*.md" .`
  - Find every call site of `core/board.py` the same way (`obs board refresh/status`)
  - Note: `research_board.py`'s renderer is explicitly "no timestamps in block" and
    golden-file/idempotency tested — check whether any existing test in
    `src/python/tests/` depends on that specific no-timestamp property (this matters for
    the decision — a test suite relying on deterministic/idempotent output is a real reason
    to keep the older renderer, not just inertia)

- [ ] **Phase 2: Assess whether they're actually redundant**
  - Compare output format/fields between the two (re-read both files if needed)
  - Determine: does `core/board.py` produce a strict superset of what `research_board.py`
    produces, or do they serve genuinely different purposes (e.g. one for quick idempotent
    checks/CI, one for the rich interactive dashboard)?

- [ ] **Phase 3: Document the decision**
  - Write a short decision note (add a section to this ORCHESTRATE file, or a new short
    doc under `docs/planning/` if that fits better — your call, keep it minimal) stating:
    EITHER "deprecate `research_board.py`, here's why, here's the migration note for
    `obs research board` callers" OR "keep both intentionally, here's the specific reason
    (e.g. idempotency test coverage, or a distinct audience)"
  - Do NOT actually delete or deprecate `research_board.py` in this pass unless the
    decision is unambiguous AND low-risk (e.g. zero external callers, zero test dependency)
    — if there's any real ambiguity, the acceptance criterion is just "a documented decision
    exists," not "code was removed." Leave removal for a follow-up if it requires judgment
    calls beyond what's verifiable here.

## Acceptance Criteria

- A clear, evidence-based written decision exists (in this file or a new doc) — not a vague
  "probably fine either way"
- If code changes were made (e.g. deprecation banner, redirect), they're minimal and don't
  break existing `obs research board` callers without a documented migration path
- No destructive action (deletion) taken without high confidence backed by the call-site/test
  mapping from Phase 1

## Verification

Manual review — this is primarily a documentation/decision task. If any code changed, run:
```bash
grep -rn "research_board" src/python/tests/ 2>/dev/null  # confirm no test breakage if touched
```

## Blockers

(none yet)
