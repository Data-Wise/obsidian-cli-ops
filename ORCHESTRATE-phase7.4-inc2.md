# ORCHESTRATE: Phase 7.4 Increment 2 — CI Hardening

## Goal

Make CI trigger on `dev` (not just `main`), upgrade actions, add Python coverage reporting, and remove/update vestigial JS lint steps.

## Pre-flight

```bash
git branch --show-current  # Must be feature/phase7.4-inc2
cd src/python && python3 -m pytest tests/ -q  # Baseline: 186 tests pass
```

## Steps

### Step 1: Rewrite `.github/workflows/ci.yml`

Replace the entire file with an updated workflow:

**Changes:**
1. **Triggers**: Add `push: [dev]` and `pull_request: [dev, main]`
2. **Actions**: `checkout@v4`, `setup-node@v4`, `setup-python@v5`
3. **Python version**: `3.11` (keep — matches CI runner, project supports 3.9+ but CI just needs one)
4. **Python tests**: Run `pytest` directly with `--cov` flags instead of `npm test`
   - `cd src/python && python3 -m pytest tests/ -v --tb=short --cov=. --cov-report=term-missing`
   - This avoids the `npm test` indirection which runs both Jest and pytest
5. **JS tests**: Keep `npx jest` separate (tests/obs.test.js validates ZSH wrapper)
6. **Lint**: Keep `npm run lint` (ESLint validates JS test files and config)
7. **Prettier**: Keep `npx prettier --check` but scope to actual JS files only
8. **Coverage**: Add `pytest-cov` to pip install, report in pytest output

**New workflow structure:**
```yaml
name: CI

on:
  push:
    branches: [main, dev]
  pull_request:
    branches: [main, dev]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v4

    - name: Use Node.js
      uses: actions/setup-node@v4
      with:
        node-version: '18.x'
        cache: 'npm'

    - name: Set up Python
      uses: actions/setup-python@v5
      with:
        python-version: '3.11'

    - name: Install Dependencies
      run: |
        npm ci
        pip install -r src/python/requirements.txt
        pip install pytest-cov

    - name: Install ZSH
      run: sudo apt-get update && sudo apt-get install -y zsh

    - name: Python Tests (with coverage)
      working-directory: src/python
      run: python3 -m pytest tests/ -v --tb=short --cov=. --cov-report=term-missing

    - name: JS Tests
      run: npx jest

    - name: Lint
      run: npm run lint

    - name: Check Formatting
      run: npx prettier --check "**/*.js" "!node_modules/**"
```

**Commit:** `ci: trigger on dev, upgrade actions, add Python coverage`

### Step 2: Add `pytest-cov` to dev dependencies in pyproject.toml

Already present (`pytest-cov>=4.1.0` in `[project.optional-dependencies] dev`). No change needed — just install it in CI via `pip install pytest-cov`.

### Step 3: Verify CI passes

Push to feature branch → open PR to dev → CI should trigger and pass.

**Commit:** (no separate commit, verification only)

## Verification

```bash
# Local: run the same command CI will run
cd src/python && python3 -m pytest tests/ -v --tb=short --cov=. --cov-report=term-missing

# Remote: push and check CI
git push origin feature/phase7.4-inc2
gh pr create --base dev
# Verify CI triggers and passes on the PR
```

## Post-flight

```bash
gh pr create --base dev --title "Phase 7.4 Inc 2: CI hardening"
```
