# ORCHESTRATE: docs-count-completeness

**Status:** Not started
**Base:** dev @ 4674317
**Repo:** obsidian-cli-ops

## Scope

Fix four doc-gap findings from this session's code review + docs gap analysis, all confined to command-count accuracy and doc completeness in `cli-reference.md` / `refcard.md`. Do not touch `.claude/planning/`, `SPEC-*`, or any Python source.

## Phases

- [ ] **Phase 1: Fix command count 62 → 63**
  - Verify current count: `cd src/python && python3 -c "from core.doc_counts import _count_obs_commands; print(_count_obs_commands())"` (expect 63)
  - Update the hardcoded "62" prose string to "63" in:
    - `docs_mkdocs/cli-reference.md` (line ~4, "62 `obs` commands")
    - `docs_mkdocs/refcard.md` (line ~218, "Commands: 62")
    - `CLAUDE.md` (line ~69)
    - `.STATUS` (verified: line, "13 commands, 62 total" → confirm whether this needs updating — it's a historical record of the PR #75 shipment, not a live count; if historical, add a note instead of just renumbering, don't silently rewrite history)
  - Root cause note (for context, not action): `obs research learn` (commit 2f9839d) landed after "62 total" was set in PR #75 (7038cbd) — the actual count is 63 as of today.

- [ ] **Phase 2: Add `obs db init` to refcard.md**
  - Read `docs_mkdocs/cli-reference.md` for how `obs db init` is documented (search for "db init")
  - Add an equivalent row/section to `docs_mkdocs/refcard.md`'s Core Commands table (there is currently no Database section at all)

- [ ] **Phase 3: Complete MCP Tool Groups section in cli-reference.md**
  - `docs_mkdocs/cli-reference.md` lines ~1085-1098 list only 5 of the 10 MCP tool groups (Vault, Search, Graph, Health, Notes, AI) while claiming "42 MCP tools"
  - Cross-reference `docs_mkdocs/refcard.md` lines ~171-182 for the full 10-group table (includes Bridge, Temporal, Diagnostics, and the rest of Research: `get_bridge_status`, `get_trends`, `get_stale_notes`, `get_daily_digest`, `diagnose`, `zotero_recent`, `zotero_cite`, `manuscript_export`, etc.)
  - Bring cli-reference.md's MCP Tool Groups section up to full parity with refcard.md's group list

- [ ] **Phase 4: Fix stale `(v3.3.0)` label**
  - `docs_mkdocs/refcard.md` — section header reads `## Claude / MCP Tools (v3.3.0)`, rest of doc is v4.3.0-current
  - Update the label to reflect current version (or remove the version suffix if the section isn't meant to be version-pinned — check how other section headers in the same file handle this)

## Acceptance Criteria

- `_count_obs_commands()` output matches all prose references to command count (no stray "62" left in cli-reference.md/refcard.md/CLAUDE.md, unless intentionally preserved as historical record in `.STATUS` with a clarifying note)
- `refcard.md` has a Database section covering `obs db init`
- `cli-reference.md`'s MCP Tool Groups section lists all 10 groups matching refcard.md
- No stale `(v3.3.0)` label remains in refcard.md

## Verification

```bash
cd src/python && python3 -c "from core.doc_counts import _count_obs_commands; print(_count_obs_commands())"
pytest src/python/tests/test_doc_counts.py -v
grep -rn "62 \`obs\`\|Commands: 62" ../docs_mkdocs/  # should return nothing (or only the intentional historical .STATUS note)
```

## Blockers

(none yet)
