# ORCHESTRATE: spec-harden-skills-banner-fix

**Status:** Not started
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

- [ ] **Phase 1: Read and confirm**
  - Read `docs/planning/specs-completed/SPEC-harden-skills.md` in full to see the current banner text and the original 8-item manifest it references
  - Confirm the 8-item manifest list matches what the code review described (cross-check against `git show e915a3f --stat` if useful, but don't re-litigate the whole finding — it's already verified)

- [ ] **Phase 2: Correct the banner**
  - Rewrite the ARCHIVED banner to accurately state: the spec is mostly (6/8 items) implemented, split across this repo (`e915a3f`/PR #73, 2 items: `docs-quality.md`, `lychee.toml`) and the sibling `craft` repo (4 items), with `docs-linter` and `docs-ops` never built
  - Keep the banner concise — one paragraph, matching the style/length of the other 5 archived files' banners (don't turn it into a full changelog)
  - Do not alter the rest of the file's content, only the banner

## Acceptance Criteria

- Banner no longer claims the full manifest shipped via `e915a3f`/PR #73 alone
- Banner accurately reflects the 6/8-done, 2/8-never-built, cross-repo split
- Banner length/style stays consistent with sibling archived files

## Verification

Manual read-check only — this is a docs-only correction with no automated test gate. Re-read the final banner and confirm it matches the code-review finding's facts before committing.

## Blockers

(none yet)
