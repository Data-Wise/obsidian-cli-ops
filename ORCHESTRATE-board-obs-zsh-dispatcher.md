# ORCHESTRATE: board-obs-zsh-dispatcher

**Status:** Not started
**Base:** dev @ 3903fb3
**Repo:** obsidian-cli-ops

## Scope

Phase 1 of `docs/planning/PLAN-board-sync-next-steps.md`: `obs board refresh`/`status` shipped
in v4.3.0 with full Python CLI support (`core/board.py`, wired into `src/python/obs_cli.py`),
but `src/obs.zsh`'s dispatcher has no `"board")` case — the feature is unreachable via the
`obs` shell entrypoint. Only `python3 src/python/obs_cli.py board refresh` works today.

## Phases

- [ ] **Phase 1: Add `obs_board()` wrapper**
  - Read `src/obs.zsh` in full — find `obs_research()` and `obs_vault()` as the pattern to mirror (same file structure: resolve python interpreter via `_obs_resolve_python`/`_get_python_cli`, pass args through)
  - Add an `obs_board()` function following that exact pattern, passing all args through to `python3 <cli> board "$@"`

- [ ] **Phase 2: Wire the dispatcher case**
  - Find the dispatch `case` statement in `src/obs.zsh` (where `"research") obs_research "$@" ;;` lives)
  - Add `"board") obs_board "$@" ;;`

- [ ] **Phase 3: Add to `obs help`**
  - Find the help text output in `src/obs.zsh` (near the `obs health` help line mentioned in `docs/planning/BRIEF-board-sync-status.md`)
  - Add `obs board refresh|status` with a one-line description, matching the existing help entries' format/column alignment

- [ ] **Phase 4: Verify end-to-end**
  - Run `obs board status` and `obs board refresh --dry-run` from this worktree (use the worktree's own `src/obs.zsh`, not a globally-installed `obs`) — confirm they now route through the shell entrypoint successfully, not falling through to "Unknown command"
  - Run `obs help | grep -i board` to confirm the new help line appears

## Acceptance Criteria

- `obs board status` and `obs board refresh --dry-run` work via the `obs` shell entrypoint (not just the raw python3 path)
- `obs help` lists `board` alongside other subcommands
- No other `src/obs.zsh` behavior changed (diff should be additive only)

## Verification

```bash
grep -n 'obs_board\|"board")' src/obs.zsh   # should show the new wrapper + case
zsh -c 'source src/obs.zsh; obs board status' 2>&1  # or however this repo's obs.zsh is normally invoked for local testing — check README/CLAUDE.md if unsure
obs help 2>&1 | grep -i board
```

If there's no clean way to source/test `obs.zsh` standalone in this worktree, check `CLAUDE.md`/`docs_mkdocs/` for the project's local-dev-testing convention before guessing.

## Blockers

(none yet)
