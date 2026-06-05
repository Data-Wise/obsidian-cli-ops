# SPEC: Robust Python Dependency Provisioning for `obs` (no manual pip)

**Status:** draft
**Created:** 2026-06-04
**Type:** packaging / install reliability
**Trigger:** On 2026-06-04, `obs` crashed at startup with `ModuleNotFoundError: No module named 'rich'`. The Homebrew launcher runs `libexec/python/obs_cli.py` under `OBS_PYTHON=/opt/homebrew/opt/python@3.12/bin/python3.12`, but **nothing installs the declared `pyproject` dependencies into that interpreter**. The CLI was unusable until deps were installed by hand (`pip install rich networkx click pyyaml python-frontmatter requests`).

---

## Sequencing & Relationship

> **This spec ships FIRST — before v3.3.0** (`SPEC-v3.3.0-bridge-temporal-2026-06-04.md`).

- **No functional overlap.** This is a packaging/install fix for *existing core deps*; v3.3.0 adds new commands and **introduces no new dependencies**, staying entirely within the "core deps only" boundary scoped below.
- **Foundation dependency (one-way).** Every v3.3.0 command inherits this startup crash on a clean install — features are unreachable until provisioning works. Fix the install floor before adding feature rooms.
- **Reusable safety net.** The CI smoke test proposed here ("clean install → `obs --help` exits 0") protects v3.3.0 and all future releases.
- **Different files in shared `obs.zsh`.** This spec changes the top-of-file `OBS_PYTHON` resolution; v3.3.0 adds dispatcher cases at the bottom — no collision, but ship separately: this = patch (**v3.2.1**), v3.3.0 = minor. Use distinct feature worktrees (branch guard blocks new code on `dev`).

---

## Overview

`obs` (v3.2.0) declares core deps in `pyproject.toml` (`python-frontmatter`, `PyYAML`, `networkx`, `rich`, `requests`, `click`). The Homebrew install, however, executes the bundled `obs_cli.py` against the **ambient** `python@3.12` site-packages — there is no virtualenv and no install-time dependency step. Consequences:

- A fresh `brew install` yields a hard crash on first run if those packages aren't already globally present.
- A `python@3.12` minor upgrade (which Homebrew resets) silently removes the packages → `obs` breaks again.
- The fix is non-obvious (the error names one missing module at a time).

The tool should provision its dependencies **deterministically and in isolation**, so `obs` works on a clean machine with zero manual steps and survives Python upgrades.

---

## Primary User Story

**As a** user installing obsidian-cli-ops (Homebrew or `install.sh`),
**I want** `obs` to run immediately without any manual `pip install`,
**so that** the tool is reliable across machines and Python upgrades.

### Acceptance Criteria

- [ ] Fresh `brew install obsidian-cli-ops` → `obs --help` and `obs` (vault list) exit 0 with **no** manual dependency steps.
- [ ] Dependencies live in a **dedicated, isolated environment** (a venv owned by the formula), not in shared `python@3.12` site-packages.
- [ ] A `python@3.12` patch/minor upgrade does **not** break `obs`.
- [ ] Dependency versions are **pinned** (lockfile or formula resources) for reproducible installs.
- [ ] `install.sh` (non-Homebrew path) provisions the same isolated env.
- [ ] A CI **smoke test** installs into a clean environment and asserts `obs --help` exits 0 (would have caught this regression).

---

## Approaches

| Option | How | Trade-off |
|--------|-----|-----------|
| **A. Formula venv (recommended)** | Homebrew `virtualenv_install_with_resources` (or a postinstall venv) creating `libexec/venv`; launcher sets `OBS_PYTHON=libexec/venv/bin/python`. | Standard Homebrew Python-app pattern; fully isolated; survives system-Python changes. Requires listing deps as formula `resource`s. |
| **B. Launcher bootstrap** | `obs.zsh` ensures a user venv (`~/.local/share/obs/venv`) and `pip install`s pinned deps on first run / version change. | No formula changes; works for `install.sh` too. First-run latency; needs a version sentinel to re-provision. |
| **C. Pin + document (stopgap)** | Keep ambient python but `pip install` pinned deps at install time and document it. | Fragile — exactly today's failure mode; not recommended as the end state. |

**Recommendation:** **A** for the Homebrew formula (canonical), with **B**'s bootstrap as the fallback used by `install.sh`. Both reference a single pinned dependency manifest.

---

## Out of Scope / Related

- The **interactive shadowing** of the `obs` binary by flow-cli's broken `obs` dispatcher is a *separate* defect tracked in flow-cli: `flow-cli/docs/specs/SPEC-obs-dispatcher-shadowing-2026-06-04.md`. That must also be fixed for `obs` to work from a normal shell, but it is not an obsidian-cli-ops change.
- AI optional-dependencies (Gemini/Anthropic/Ollama) provisioning is unchanged here; this spec covers **core** deps only.

## Implementation Notes

- Single source of truth for the dep set + pins (e.g. a `requirements.lock` generated from `pyproject`).
- The launcher must point `OBS_PYTHON` at the isolated interpreter, never `command -v python3` (which resolved to a dep-less `python@3.14` in the field).
- Add the CI smoke test to the existing test workflow so a future packaging regression fails the build.

## History

- **2026-06-04** — Created after `obs` broke on missing `rich`; deps installed manually into `python@3.12` as a stopgap. This spec proposes a permanent, isolated provisioning fix.
