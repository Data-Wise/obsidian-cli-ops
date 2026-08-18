# Obsidian-Sync Validation — Todo

## Phase 1: JSON Schema + Doctor Validation ✅
- [x] Create `schema/obsidian-sync.schema.json`
- [x] Add `_check_obsidian_sync()` to `src/python/core/doctor.py`
- [x] Add 10 test cases to `src/python/tests/test_doctor.py`
- [x] Wire `--layer flow` into `src/python/obs_cli.py`
- [x] Verify on live vaults

## Phase 2: `obs flow init` Command
- [x] Create `src/python/core/flow_init.py`
- [x] Create `src/python/tests/test_flow_init.py`
- [x] Wire `flow init` subcommand into `src/python/obs_cli.py`
- [x] Add non-interactive mode flags
- [x] Test against existing configs

## Phase 3: `savant:restore` Hook
- [ ] Add subprocess call to `obs doctor --layer flow --vault <id> --json`
- [ ] Handle `flow-sync-missing` warning
- [ ] Handle `flow-sync-stale` warning
- [ ] Verify no interactive prompts

## Phase 4: `craft:recap` Hook
- [x] Add subprocess call to `obs doctor --layer flow --json`
- [x] Handle `flow-sync-missing` warning
- [x] Handle `flow-sync-stale` warning
- [x] Verify no interactive prompts

## Phase 5: Verify + Commit
- [x] Run pytest for all new tests
- [x] Run `obs doctor --layer flow` on live vaults
- [ ] Commit with conventional commit
- [ ] Update `.STATUS`
