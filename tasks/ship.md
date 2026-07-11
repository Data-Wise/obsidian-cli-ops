# Shipping & Rollout Plan: Vault Reorganization Paths Migration (Issue #86)

## Pre-Launch Checklist

### Code Quality
- [x] All tests pass (514 pytest cases pass cleanly)
- [x] Code reviewed and approved (see `tasks/review.md`)
- [x] No `TODO` comments or debug prints in the changed files

### Security & Hardening
- [x] No secrets committed
- [x] Standard library / native imports only (no new dependencies added)

### Documentation
- [x] Specification updated (`SPEC-issue-86-vault-reorg-paths.md`)
- [x] Task plan and todo checklists completed in `tasks/`

---

## Staged Rollout Strategy
1. **Local Dev Branch:** Currently committed to the local `dev` branch.
2. **Push to Remote `dev`:** Push changes to `origin/dev` once approved.
3. **Merge to `main`:** Defer merge to `main` and production Homebrew tap bump until the user gives explicit release permission.

---

## Rollback Plan

### Trigger Conditions
- Failure in the `obs board refresh` command on target environment.
- Any regression in vault indexing or stats calculation.

### Rollback Steps
- **Code Rollback:** Since these are atomic commits on `dev`, run:
  ```bash
  git revert HEAD
  ```
- **Verification:** Run `pytest` to verify the codebase returns to the previous state.
- **Time to Rollback:** < 1 minute.
