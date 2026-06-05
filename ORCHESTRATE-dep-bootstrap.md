# ORCHESTRATE: Dependency Bootstrapping Fix (v3.2.1)

> **Handoff plan.** Execute this in a session started *inside this worktree*:
> `cd ~/.git-worktrees/obsidian-cli-ops/feature-dep-bootstrap && claude`
> Branch: `feature/dep-bootstrap` (off `dev`). Spec (approved): `docs/specs/SPEC-dependency-bootstrapping-2026-06-04.md`.

## Context

`obs` v3.2.0 **crashes on a clean install** — `ModuleNotFoundError: No module named 'rich'`. The Homebrew launcher runs the bundled `obs_cli.py` against an ambient interpreter, but **nothing provisions the declared `pyproject` deps** into it. The tool is unusable until a user manually `pip install`s. A `python@3.x` minor upgrade re-breaks it. This fix provisions core deps **deterministically and in isolation** so `obs` works on a fresh machine with zero manual steps and survives Python upgrades. Ships as **v3.2.1**, *before* v3.3.0 (every v3.3.0 command inherits this crash until fixed).

## Locked decision (from spec, A + B)

- **A — Homebrew formula venv (canonical):** `virtualenv_install_with_resources` → `libexec/venv`; launcher points `OBS_PYTHON` at `libexec/venv/bin/python`.
- **B — `install.sh` bootstrap (non-Homebrew fallback):** first-run / version-sentinel venv at `~/.local/share/obs/venv`, pip-installs pinned deps.
- **C rejected** (ambient pip = today's failure mode).
- **One source of truth:** generated `requirements.lock` (pinned from `pyproject.toml`).

## Core deps to pin (`pyproject.toml:30-37`)

`python-frontmatter>=1.0.0`, `PyYAML>=6.0`, `networkx>=3.2`, `rich>=13.7.0`, `requests>=2.31.0`, `click>=8.1.0`. (AI extras stay optional — out of scope.)

## Cross-repo scope ⚠️

This fix spans **two repos** — sequence them:

| Repo | File | Change |
|---|---|---|
| `obsidian-cli-ops` (this worktree) | `requirements.lock` (new) | Pin core deps from `pyproject.toml` |
| | `src/obs.zsh:23` | `OBS_PYTHON` resolution: prefer isolated venv, never bare `command -v python3` |
| | `install.sh` | Approach B: create/refresh `~/.local/share/obs/venv`, install `requirements.lock`, set version sentinel |
| | `.github/workflows/ci.yml` | Add **clean-install smoke test** job: install into a fresh env → assert `obs --help` exits 0 |
| `homebrew-tap` (sibling, separate PR) | `Formula/obsidian-cli-ops.rb` | Approach A: `virtualenv_install_with_resources` + `resource` blocks for each pinned dep; launcher env points at `libexec/venv` |

## Build order

1. **`requirements.lock`** — generate pinned versions (resolves the otherwise-untestable "versions are pinned" acceptance criterion). First task by design.
2. **Launcher (`src/obs.zsh:23`)** — `OBS_PYTHON` prefers, in order: explicit `$OBS_PYTHON` → formula `libexec/venv` → `install.sh` user venv → (last resort) `command -v python3` with a clear "deps may be missing" warning.
3. **`install.sh` bootstrap (B)** — provision the user venv from `requirements.lock`; idempotent; re-provision on version-sentinel mismatch.
4. **CI smoke test** — new `ci.yml` job: clean venv → install → `obs --help` exits 0. This would have caught the original regression; it guards all future releases incl. v3.3.0.
5. **Homebrew formula (A)** — in `homebrew-tap` (separate worktree/PR): `virtualenv_install_with_resources`, pinned `resource`s, launcher → `libexec/venv`. `brew install` + `brew audit` must pass.

## Verification (end-to-end)

- [ ] Clean container/VM: `brew install data-wise/tap/obsidian-cli-ops` → `obs --help` and `obs` exit 0, **no** manual pip.
- [ ] Simulate `python@3.x` minor bump (formula path isolated in `libexec/venv`) → `obs` still runs.
- [ ] `install.sh` path on a machine without the deps → `obs --help` exits 0.
- [ ] CI smoke-test job is green on the PR.
- [ ] Existing suite stays green: `cd src/python && pytest` (265 tests) + `npx jest` (30).
- [ ] `brew audit --strict obsidian-cli-ops` passes.

## Release wiring (after merge)

- PR `feature/dep-bootstrap` → `dev`; then `dev` → `main` as **Release: v3.2.1**.
- Bump version across all files (grep old version repo-wide first — `pyproject.toml`, `obs.zsh`, `tests/obs.test.js`, docs). Tag `v3.2.1`, GitHub release.
- Separate PR in `homebrew-tap` for the formula; verify `brew install` post-release.
- Update `.STATUS` + `MEMORY.md` (test count, new install model).

## Guardrails (from project rules)

- New code files are blocked on `dev` — that's why this runs on `feature/dep-bootstrap`.
- Use `execFileSync` not `execSync` (security hook) if any JS touched.
- Cross-repo `git push` while session CWD is on `main`/`dev` can trip branch-guard — keep this session's CWD on the worktree (`feature/dep-bootstrap`); for the tap, use its own worktree/session.
- Exception narrowing: subprocess/venv provisioning crosses an external boundary → broad `except` with graceful fallback OK; keep SQLite paths narrow.

---

**STOP after committing this file.** Implementation begins in a new session opened inside this worktree, not from the planning session.
