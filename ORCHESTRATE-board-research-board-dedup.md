# ORCHESTRATE: board-research-board-dedup

**Status:** Complete — decision documented, no code removed (keep both, intentionally)
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

- [x] **Phase 1: Map current usage**
  - Find every call site of `research_board.py` (CLI wiring in `obs_cli.py`/`obs.zsh`, any
    tests, any docs referencing `obs research board`) via
    `grep -rn "research_board\|obs research board" --include="*.py" --include="*.zsh" --include="*.md" .`
  - Find every call site of `core/board.py` the same way (`obs board refresh/status`)
  - Note: `research_board.py`'s renderer is explicitly "no timestamps in block" and
    golden-file/idempotency tested — check whether any existing test in
    `src/python/tests/` depends on that specific no-timestamp property (this matters for
    the decision — a test suite relying on deterministic/idempotent output is a real reason
    to keep the older renderer, not just inertia)

- [x] **Phase 2: Assess whether they're actually redundant**
  - Compare output format/fields between the two (re-read both files if needed)
  - Determine: does `core/board.py` produce a strict superset of what `research_board.py`
    produces, or do they serve genuinely different purposes (e.g. one for quick idempotent
    checks/CI, one for the rich interactive dashboard)?

- [x] **Phase 3: Document the decision**
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

## Decision (2026-07-01)

**Keep both, intentionally. No deprecation, no code change.**

### Evidence from Phase 1 (call-site mapping)

- `research_board.py` is wired under **`obs research board`** (`obs_cli.py:1084-1088`,
  dispatch at `obs_cli.py:1987-1988`), documented in `docs_mkdocs/cli-reference.md`,
  `docs_mkdocs/refcard.md`, `docs_mkdocs/tutorials/research-board.md`, and
  `docs_mkdocs/changelog.md` (shipped v4.0.0). Covered by
  `src/python/tests/test_research_board.py`.
- `core/board.py` is wired under a **separate top-level command, `obs board refresh` /
  `obs board status`** (`obs_cli.py:1056-1065`, dispatch at `obs_cli.py:1899-1902`),
  shipped v4.3.0 (SPEC-board-sync-automation). Covered by `src/python/tests/test_board.py`.
- These are two distinct CLI verbs (`obs research board` vs `obs board refresh/status`),
  not two implementations of the same command — a caller of one is structurally unaware of
  the other; there is no ambiguity for end users about which to invoke.

### Evidence from Phase 1 (test dependency on no-timestamp property)

`test_research_board.py::test_render_has_sections_and_no_timestamp` asserts
`"generated" not in out.lower()`, and `test_render_is_deterministic` /
`test_write_is_idempotent` directly test that re-rendering unchanged input produces zero
diff. This is load-bearing, not incidental — the whole point of `research_board.py`
(per its own docstring, "SPEC-obs / ADR-001") is a **pure, timestamp-free, idempotent**
renderer suitable for a scripted pipeline where "did anything change" must be computed
from content diff alone (see `docs/specs/SPEC-board-sync-automation-2026-06-30.md`:
"Same input -> same output -> zero diff -> no file change -> no Obsidian sync trigger").

### Evidence from Phase 2 (output comparison — NOT a superset relationship)

- `core/board.py`'s `BoardEngine._build_block()` (line 509-512) **injects a timestamp
  line** (`> generated: {timestamp} by obs board refresh`) into every render. This makes
  `core/board.py`'s output non-idempotent by construction — two renders of identical
  underlying project state produce a byte-diff every time, which is the exact property
  `research_board.py` was built to avoid.
- `core/board.py`'s renderer (`BoardRenderer.render`) produces a much richer document:
  "Act on now" ranked action table with leverage/risk scoring, TL;DR, future-ideas,
  threats, this-week sections (LLM-augmentable placeholders), a Feeds section with
  Obsidian wikilinks — none of which exist in `research_board.py`'s output (which is just
  the "Manuscripts / Programs / Packages" status tables).
- `core/board.py` merges **three** data sources (atlas + `.STATUS` files + vault DB
  health/drift via `VaultConnector`/`Doctor`) through a `Merger` with atlas-wins conflict
  resolution; `research_board.py` reads **atlas only**.
- Conclusion: `core/board.py` is a superset of *content* (atlas manuscripts/programs data
  is a subset of what it ingests) but is **not** a superset of *behavior* —
  it cannot serve `research_board.py`'s idempotent/diffable use case because of the
  embedded timestamp. They serve genuinely different purposes:
  - `research_board.py` / `obs research board` → deterministic, script-friendly,
    diff-safe renderer for automated pipelines (cron/launchd sync jobs that need to know
    "did content actually change").
  - `core/board.py` / `obs board refresh` → rich, human-facing interactive dashboard
    with staleness tracking (`_staleness_days` parses its own `generated:` line) and
    LLM-augmentable sections — staleness tracking is *only possible* because it embeds
    a timestamp, which is the opposite design goal from `research_board.py`.

### Outcome

No code changes made. Both renderers stay. If a future contributor is confused by the
similar filenames/marker constants (`MARKER_START`/`MARKER_END` are literally identical
strings in both files — `<!-- obs:board:start -->` / `<!-- obs:board:end -->`), that's a
real footgun worth flagging separately: **the two commands would clobber each other's
marker block if pointed at the same vault file**, since both write into an identically
delimited region. This wasn't in scope to fix here (no evidence either command is
currently misconfigured to write to a shared path — `_resolve_board_path` in
`core/board.py` defaults to `_ACTION-BOARD.md` while `research_board.py`'s `--out` is
user-supplied with no default), but it's worth a follow-up doctor check or a shared-marker
namespace change if the two ever do target the same file.

## Blockers

(none — decision is unambiguous, no code change required)
