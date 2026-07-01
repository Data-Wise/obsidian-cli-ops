# ORCHESTRATE: spec-harden-skills-banner-fix

**Status:** Complete
**Base:** dev @ 4674317
**Repo:** obsidian-cli-ops

## Scope

Fix one factual error found in this session's code review: the ARCHIVED banner on `docs/planning/specs-completed/SPEC-harden-skills.md` (lines ~3-4) incorrectly claims the spec's full 8-item manifest was "implemented in commit `e915a3f` (PR #73)."

## Background (from code review)

Verified false on two counts:
1. `e915a3f` is a single obsidian-cli-ops commit and can't span into the sibling `craft` repo, yet several manifest items (`docs-linter`, `docs-ops`, `site-management`, `mermaid-linter`, `navigation`, `check` skills) live in `craft`, not this repo.
2. PR #73's actual diff contains only 2 of the 8 manifest items (`docs-quality.md`, `lychee.toml`).
3. `docs-linter` and `docs-ops` (both "create" items) don't exist in *either* repo — never built.
4. Net: 6/8 manifest items exist somewhere (split across repos), 2/8 were never built. The archival decision itself was reasonable (spec is mostly done), but the banner's specific citation is wrong.

## Phases

- [x] **Phase 1: Read and confirm**
  - Read `docs/planning/specs-completed/SPEC-harden-skills.md` in full to see the current banner text and the original 8-item manifest it references
  - Confirmed the 8-item manifest list matches the code review: `site-management`(edit), `docs-linter`(create), `lychee.toml`(create), `check`(edit), `docs-quality.md`(create), `navigation`(edit), `mermaid-linter`(edit), `docs-ops`(create). Verified via `git show e915a3f --stat`: only `lychee.toml`, `docs-quality.md`, and `SPEC-harden-skills.md` itself were touched by that commit. Verified via filesystem search: `docs-linter`/`docs-ops` SKILL.md don't exist in this repo or in `craft`; `site-management`, `check`, `navigation`, `mermaid-linter` SKILL.md exist only in `craft`.

- [x] **Phase 2: Correct the banner**
  - Rewrote the ARCHIVED banner to state: 6/8 manifest items implemented, split across this repo (`e915a3f`/PR #73, 2 items: `docs-quality.md`, `lychee.toml`) and the sibling `craft` repo (4 items: `site-lifecycle`, `preflight-check`, `nav-sync`, `mermaid-linter`), with `docs-linter` and `docs-ops` never built
  - Banner stayed one paragraph, consistent length with the other archived files in this dir (only 3 siblings exist, not 5 as the original phase text estimated — non-blocking, cosmetic note only)
  - No other content in the file was touched (verified via `git diff` — only the banner two lines changed)

## Acceptance Criteria

- Banner no longer claims the full manifest shipped via `e915a3f`/PR #73 alone
- Banner accurately reflects the 6/8-done, 2/8-never-built, cross-repo split
- Banner length/style stays consistent with sibling archived files

## Verification

Manual read-check only — this is a docs-only correction with no automated test gate. Re-read the final banner and confirm it matches the code-review finding's facts before committing.

## Blockers

(none — completed)
