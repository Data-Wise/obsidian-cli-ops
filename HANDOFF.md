# HANDOFF: Implementing v3.2.1 (dependency bootstrapping)

> Read this first, then `ORCHESTRATE-dep-bootstrap.md` + `docs/specs/SPEC-dependency-bootstrapping-2026-06-04.md` (approved, Approach A+B).
> You are in worktree `feature/dep-bootstrap` — new code files are allowed here.

## Kickoff

```
Read ORCHESTRATE-dep-bootstrap.md and the approved dep-bootstrapping spec.
Implement v3.2.1 per locked Approach A+B. Start.
```

## Work graph

```
Phase 1 (SEQUENTIAL — blocks all)   requirements.lock   ← source of truth; do first
Phase 2 (PARALLEL — 3 distinct files, no shared state)
   ├─ src/obs.zsh:23   OBS_PYTHON resolution
   ├─ install.sh       Approach-B user-venv bootstrap (~/.local/share/obs/venv)
   └─ .github/workflows/ci.yml   clean-install smoke test (obs --help exits 0)
Phase 3 (CROSS-REPO — own worktree/session)
   └─ homebrew-tap/Formula/obsidian-cli-ops.rb   Approach-A formula venv
```

## Option A — orchestrator (lowest effort)

```
/craft:orchestrate
```
Picks up the existing ORCHESTRATE file, fans out subagents per phase, monitors them.

## Option B — manual parallel dispatch

1. **Lockfile inline (don't delegate):** generate `requirements.lock` pinning the 6 core deps from `pyproject.toml:30-37` (python-frontmatter, PyYAML, networkx, rich, requests, click) to exact versions.
2. **Then dispatch all 3 Phase-2 agents in ONE message** (concurrent). Each `general-purpose`, each told to read `CLAUDE.md` + spec and **edit only its one file**:
   - **launcher:** `src/obs.zsh:23` → `OBS_PYTHON` order: explicit `$OBS_PYTHON` → formula `libexec/venv/bin/python` → user venv → bare `python3` (+ stderr "deps may be missing" warning).
   - **install.sh:** provision `~/.local/share/obs/venv` from `requirements.lock`; idempotent; re-provision on version-sentinel mismatch.
   - **ci.yml:** add job — clean env install → assert `obs --help` exits 0.
3. **You synthesize** (don't delegate): review the 3 diffs together.

## Verify (end-to-end)

```bash
cd src/python && pytest      # 265 green
npx jest                      # 30 green
# clean-env: brew install ... → obs --help exits 0, no manual pip
# brew audit --strict obsidian-cli-ops
```

## Cautions

- **Parallel agents are conflict-free ONLY because each edits a distinct file** — enforce "edit only `<file>`" per agent.
- **Lockfile is not parallelized** — it's the blocker every unit reads; do it first, inline.
- **Phase 3 is cross-repo** — run the `homebrew-tap` formula in the tap's OWN worktree/session (its own `CLAUDE.md` + branch-guard). Cross-repo `git push` from a `dev`/`main` CWD trips branch-guard.
- **Before the PR to `dev`: delete `ORCHESTRATE-dep-bootstrap.md` and `HANDOFF.md`** — feature-branch working artifacts, not for merge.

## Release wiring (after merge)

PR `feature/dep-bootstrap` → `dev`; bump version everywhere (grep old version repo-wide first); `dev` → `main` as Release v3.2.1; tag + GitHub release; separate `homebrew-tap` PR; verify `brew install` post-release; update `.STATUS` + `MEMORY.md`.

---
**Next after v3.2.1 ships:** v3.3.0 spec is `reviewed` (0 open questions) — approve and implement bridge + temporal.
