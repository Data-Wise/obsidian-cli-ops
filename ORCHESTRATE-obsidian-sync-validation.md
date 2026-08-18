# Obsidian-Sync Validation — Orchestration Plan

> **Branch:** `feature/obsidian-sync-validation`
> **Base:** `dev`
> **Worktree:** `~/.git-worktrees/obsidian-cli-ops/feature-obsidian-sync-validation`
> **Spec:** `docs/specs/SPEC-obsidian-sync-2026-07-11.md`

## Objective

Standardize `.flow/obsidian-sync.yml` across all Obsidian-backed repos: validate via `obs doctor --layer flow`, create via `obs flow init`, and hook into session entry points.

## Phase Overview

| Phase | Increment | Priority | Effort | Status |
|-------|-----------|----------|--------|--------|
| 1 | JSON Schema + doctor validation | P0 | S | ✅ Done |
| 2 | `obs flow init` command | P1 | M | 📋 Next |
| 3 | `savant:restore` hook | P2 | S | 📋 After Phase 2 |
| 4 | `craft:recap` hook | P2 | S | 📋 After Phase 3 |
| 5 | Verify + commit | P0 | S | 📋 Final |

## Phase 1: JSON Schema + Doctor Validation ✅

**Scope:** Schema file + `_check_obsidian_sync()` in doctor.py

- [x] 1.1 Create `schema/obsidian-sync.schema.json`
- [x] 1.2 Add `_check_obsidian_sync()` to `src/python/core/doctor.py`
- [x] 1.3 Add 10 test cases to `src/python/tests/test_doctor.py`
- [x] 1.4 Wire `--layer flow` into `src/python/obs_cli.py`
- [x] 1.5 Verify on live vaults

**Key files:** `schema/obsidian-sync.schema.json`, `src/python/core/doctor.py`, `src/python/tests/test_doctor.py`

## Phase 2: `obs flow init` Command

**Scope:** Interactive wizard to create `.flow/obsidian-sync.yml`

- [x] 2.1 Create `src/python/core/flow_init.py` — `init_flow_config()` logic
- [x] 2.2 Create `src/python/tests/test_flow_init.py` — unit + integration tests
- [x] 2.3 Wire `flow init` subcommand into `src/python/obs_cli.py`
- [x] 2.4 Add non-interactive mode: `--vault-root`, `--pairs`, `--json` flags
- [x] 2.5 Test against existing configs (pmed-modern, mediation-noncollapsibility)

**Key files:** `src/python/core/flow_init.py` (NEW), `src/python/obs_cli.py`, `src/python/tests/test_flow_init.py` (NEW)

**Design notes:**
- Defaults to `.` (current dir)
- Creates `.flow/` if missing
- Suggests defaults from repo structure (glob for `.md` files, infer vault paths)
- Validates against JSON Schema before writing
- Refuses to overwrite existing config (use `--force` to override)

## Phase 3: `savant:restore` Hook

**Scope:** Research session restore checks staleness

- [ ] 3.1 Add subprocess call to `obs doctor --layer flow --vault <id> --json`
- [ ] 3.2 Handle `flow-sync-missing` → warn + suggest `obs flow init`
- [ ] 3.3 Handle `flow-sync-stale` → warn + suggest `obs flow init`
- [ ] 3.4 Verify no interactive prompts in non-TTY context

**Key files:** Session restore hook (external to this repo)

**Design notes:**
- Subprocess call adds ~100ms to restore
- Warn only, never block

## Phase 4: `craft:recap` Hook

**Scope:** Dev-tools recap checks staleness before push

- [x] 4.1 Add subprocess call to `obs doctor --layer flow --json`
- [x] 4.2 Handle `flow-sync-missing` → warn + suggest init
- [x] 4.3 Handle `flow-sync-stale` → warn + suggest init
- [x] 4.4 Verify no interactive prompts

**Key files:** `craft/skills/workflow/adhd-workflow/SKILL.md`

**Design notes:**
- Catches stale configs before push
- Subprocess call adds ~100ms to recap

## Phase 5: Verify + Commit

- [ ] 5.1 Run `pytest src/python/tests/test_doctor.py` — all pass
- [ ] 5.2 Run `pytest src/python/tests/test_flow_init.py` — all pass
- [ ] 5.3 Run `obs doctor --layer flow` on live vaults
- [ ] 5.4 Commit with conventional commit: `feat: add obs flow init and session hooks`
- [ ] 5.5 Update `.STATUS`

## Friction Prevention

- Context first: verify CWD and branch before any changes
- Test per phase: run pytest after each phase
- No autonomous starts: wait for user confirmation before each phase
- Schema validation: always validate against JSON Schema before writing

## Acceptance Criteria

- [ ] `schema/obsidian-sync.schema.json` validates existing configs
- [ ] `obs doctor --layer flow` runs 6 checks per vault
- [ ] `obs flow init` creates valid config interactively
- [ ] `obs flow init` works non-interactively with flags
- [ ] `savant:restore` warns about missing/stale configs
- [ ] `craft:recap` warns about missing/stale configs
- [ ] All existing pytest tests still pass
- [ ] New tests for `obs flow init` pass

## Commit Strategy

Conventional commits per phase:
- Phase 1: `feat: add obsidian-sync schema and doctor validation`
- Phase 2: `feat: add obs flow init command`
- Phase 3: `feat: add savant:restore hook for flow sync`
- Phase 4: `feat: add craft:recap hook for flow sync`
- Phase 5: `chore: verify and commit obsidian-sync validation`

## Verification

```bash
pytest src/python/tests/test_doctor.py -v
pytest src/python/tests/test_flow_init.py -v
obs doctor --layer flow
```

## Session Instructions

```bash
cd ~/.git-worktrees/obsidian-cli-ops/feature-obsidian-sync-validation
```

> "Read `ORCHESTRATE-obsidian-sync-validation.md` and start Phase 2."
