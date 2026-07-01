# SPEC: Local Pre-Push Hook

> [!warning] ARCHIVED (2026-07-01) — shipped in v4.3.0
> This spec is fully implemented. For **live state and next steps** see [`.STATUS`](../../../.STATUS). Kept for history only.

**Date**: 2026-06-30
**Status**: Draft (v2 — trimmed for speed, no tokens, no workflow friction)

---

## Design Principles

| Principle | Why |
|-----------|-----|
| **Zero tokens, zero network** | Pre-push hooks must work offline. No API keys, no package fetches, no external service calls. |
| **Sub-second or skip** | If a check can't finish in < 1s on a hot cache, it doesn't belong in a pre-push hook. Move to CI. |
| **Warning over blocking** | When uncertain, warn don't block. Pre-push is quality-of-life. Branch-guard + CI are the enforcement layer. |
| **Built-in tools only** | No `brew install`, `npm install`, `pip install` as part of hook setup. Use `git`, `grep`, `awk`, `wc` only. |
| **main/dev already guarded** | Branch-guard.sh + GitHub branch protection block pushes to main/dev. Pre-push hook doesn't duplicate this. |

---

## Layer Split (updated — pre-push trimmed)

| Layer | What it checks | Speed | Token/Network | Blocks |
|-------|---------------|-------|---------------|--------|
| branch-guard.sh | Direct pushes to main/dev | Instant | None | Commit + push (non-bypassable) |
| Pre-push hook | Secrets glance, binary files, oversized files | < 500ms | None | `git push` (bypassable via `--no-verify`) |
| GitHub Actions (CI) | PR metadata, changelog, full lint, tests, links | Slow | CI runner | PR merge (via branch protection) |

---

## What the Hook Checks (and why it's fast)

### 1. Big binary files in push range (WARNING)

Prevent accidental commits of build artifacts or dependencies.

```bash
big=$(git diff "@{push}..HEAD" --diff-filter=A --name-only \
    | grep -iE '\.(exe|dll|so|dylib|zip|tar\.gz|tgz|bin|whl)$' \
    || true)
if [ -n "$big" ]; then
    echo "[pre-push] WARNING: binary files detected — were these intentional?"
    echo "$big" | sed 's/^/  /'
fi
```

**Sub-second?** Yes — `git diff --name-only` is O(diff size).
**Network/tokens?** None.
**Blocks?** No — warning only. CI enforces binary file policy.

### 2. Single file > 5K lines in push range (WARNING)

Catches accidentally committed datasets, generated files, or rendered artifacts.

```bash
oversized=$(git diff "@{push}..HEAD" --stat --diff-filter=A \
    | awk -F'|' '{
        file=$1; gsub(/[[:space:]]*$/,"",file);
        size=$2; gsub(/[^0-9]/,"",size);
        if (size+0 > 5000) print file" ("size" lines)"
    }' || true)
if [ -n "$oversized" ]; then
    echo "[pre-push] WARNING: oversized files detected (>5K lines) — was this intentional?"
    echo "$oversized" | sed 's/^/  /'
fi
```

Threshold 5K lines (not 1K) — avoids warning on legitimate large files (test fixtures, generated docs, example data).

**Sub-second?** Yes — `git diff --stat` is O(diff size).
**Network/tokens?** None.
**Blocks?** No — warning only.

### 3. Secrets glance (WARNING only)

Scan added lines for patterns that look like secrets. Warning only — never blocks.

```bash
secrets=$(git diff "@{push}..HEAD" --diff-filter=A \
    | grep -v '^\s*#' \
    | grep -v '\.env\.example\|test/fixtures/\|mock\|_test\.\|test\.' \
    | grep -iE '(api_key|token|password|secret)\s*=\s*['\''"][^'\''"]+['\''"]' \
    || true)
if [ -n "$secrets" ]; then
    echo "[pre-push] WARNING: possible secrets detected (review before push):"
    echo "$secrets"
fi
```

**Sub-second?** Yes — pipe through grep on a diff that's already loaded in memory.
**Network/tokens?** None.
**Blocks?** No — warning only. CI's secrets scanner (gitleaks or similar) handles authoritative detection.

### 4. Merge commits in feature branch (WARNING only)

```bash
merges=$(git log --oneline --merges "@{push}..HEAD" 2>/dev/null | wc -l | tr -d ' ')
if [ "$merges" -gt 0 ]; then
    echo "[pre-push] WARNING: $merges merge commit(s). Feature branches typically rebase."
fi
```

Graceful fallback if `@{push}` doesn't exist (fresh branch): skip the check silently.

**Sub-second?** Yes — `git log --oneline --merges` on a small range.
**Network/tokens?** None.
**Blocks?** No — warning only.

---

## What the Hook Does NOT Check (moved to CI or excluded)

| Check | Why excluded | Where it lives |
|-------|-------------|----------------|
| Branch name convention | Too restrictive. Legit branch names (`test-flaky`, `wip/ideas`) would be blocked. branch-guard.sh already blocks main/dev. | ✂️ Removed |
| Commit message format | PR title is the contract. Per-commit format is noisy with fixup!/squash commits | CI: `pr-metadata.yml` |
| Full markdownlint | Pre-push should be sub-second. md lint takes 2-5s on full project | `docs-linter` skill / CI |
| gitleaks | Requires external tool install, slow first run | CI (dedicated secrets scan workflow) |
| Signed-off-by | No DCO requirement for this project | ✂️ Removed |

---

## Implementation

### File: `.githooks/pre-push`

```bash
#!/usr/bin/env bash
set -euo pipefail

# Pre-push hook — fast, local, zero-token, purely advisory.
# Runs on every git push. All checks are WARNING only — never blocks.
# Enforcement: GitHub Actions + branch protection are authoritative.
#
# Install: git config core.hooksPath .githooks
# Skip:    git push --no-verify

REMOTE="${1:-origin}"
BRANCH=$(git symbolic-ref HEAD 2>/dev/null | sed 's/refs\/heads\///')
RANGE="${3:-@{push}..HEAD}"

# Guard: skip for secondary remotes (upstream, fork)
[ "$REMOTE" != "origin" ] && exit 0

# Guard: skip for main/dev pushes (branch-guard + GitHub protection cover these)
echo "$BRANCH" | grep -qiE '^(main|dev)$' && exit 0

# Guard: skip if no upstream yet (fresh branch)
git rev-parse "@{push}" &>/dev/null || exit 0

warnings=0

# 1. Binary files
big=$(git diff "$RANGE" --diff-filter=A --name-only \
    | grep -iE '\.(exe|dll|so|dylib|zip|tar\.gz|tgz|bin|whl)$' \
    || true)
if [ -n "$big" ]; then
    echo "[pre-push] WARNING: binary files — were these intentional?"
    echo "$big" | sed 's/^/  /'
    warnings=$((warnings + 1))
fi

# 2. Oversized files
oversized=$(git diff "$RANGE" --stat --diff-filter=A \
    | awk -F'|' '{
        file=$1; gsub(/[[:space:]]*$/,"",file);
        size=$2; gsub(/[^0-9]/,"",size);
        if (size+0 > 5000) print file" ("size" lines)"
    }' || true)
if [ -n "$oversized" ]; then
    echo "[pre-push] WARNING: oversized files (>5K lines) — intentional?"
    echo "$oversized" | sed 's/^/  /'
    warnings=$((warnings + 1))
fi

# 3. Secrets glance
secrets=$(git diff "$RANGE" --diff-filter=A \
    | grep -v '^\s*#' \
    | grep -v '\.env\.example\|test/fixtures/\|mock\|_test\.\|test\.' \
    | grep -iE '(api_key|token|password|secret)\s*=\s*['\''"][^'\''"]+['\''"]' \
    || true)
if [ -n "$secrets" ]; then
    echo "[pre-push] WARNING: possible secrets detected — review before push"
    echo "$secrets" | sed 's/^/  /'
    warnings=$((warnings + 1))
fi

# 4. Merge commits
merges=$(git log --oneline --merges "$RANGE" 2>/dev/null | wc -l | tr -d ' ')
if [ "$merges" -gt 0 ]; then
    echo "[pre-push] WARNING: $merges merge commit(s). Feature branches typically rebase."
    warnings=$((warnings + 1))
fi

if [ "$warnings" -eq 0 ]; then
    echo "[pre-push] Clean"
fi
echo "[pre-push] Done ($warnings warnings, 0 blocked)"
```

---

## Installation

### install.sh addition

```bash
if [ -d .git ]; then
    mkdir -p .githooks
    cp scripts/pre-push.sh .githooks/pre-push
    chmod +x .githooks/pre-push
    git config core.hooksPath .githooks
    echo "Pre-push hook installed"
fi
```

---

## Testing

| Test | Command | Expected |
|------|---------|----------|
| Push to `feature/valid` | `git push origin feature/valid` | Exit 0, "Clean" |
| Push to `main` or `dev` | `git push origin main` | Exit 0, skipped silently |
| Push to secondary remote | `git push upstream feature/x` | Exit 0, skipped silently |
| Fresh branch, no upstream | `git push -u origin feature/new` | Exit 0, skipped gracefully |
| Binary file added | `git add file.exe`, commit, push | Exit 0, warning only |
| Large file added | Create 6K-line file, commit, push | Exit 0, warning only |
| Secret in push range | `git add config.py` with `TOKEN=abc`, commit, push | Exit 0, warning only |
| `--no-verify` | `git push --no-verify origin feature/x` | Exit 0, no output |
