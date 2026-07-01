# SPEC: Local Pre-Push Hook

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

### 1. Big binary files in push range (BLOCK)

Prevent accidental commits of build artifacts or dependencies.

```bash
big=$(git diff "@{push}..HEAD" --diff-filter=A --name-only \
    | grep -iE '\.(exe|dll|so|dylib|zip|tar\.gz|tgz|bin|whl)$' \
    || true)
if [ -n "$big" ]; then
    echo "[pre-push] BLOCKED: prohibited binary files in push:"
    echo "$big"
    exit 1
fi
```

**Sub-second?** Yes — `git diff --name-only` is O(diff size).
**Network/tokens?** None.

### 2. Single file > 5MB in push range (BLOCK)

Catches accidentally committed datasets, node_modules, rendered artifacts.

```bash
git diff "@{push}..HEAD" --stat --diff-filter=A \
    | awk -F'|' '{diff=$2; if (diff+0 > 5000) print $0}'
```

Threshold 5MB (not 1MB) — avoids blocking legitimate large files like test fixtures, bundled SVGs, or example data.

**Sub-second?** Yes — `git diff --stat` is O(diff size) and returns aggregated sizes instantly.
**Network/tokens?** None.

### 3. Secrets glance (WARNING only)

Scan added lines for patterns that look like secrets. **Warning only** — never blocks on a pattern match because the inline grep is not accurate enough for blocking decisions.

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

# Pre-push hook — fast, local, zero-token validation.
# Runs on every git push before push reaches remote.
#
# Design: sub-second checks only, warning over blocking, built-in tools.
# Enforcement: branch-guard.sh + GitHub branch protection are authoritative.
#
# Install: git config core.hooksPath .githooks
# Skip:    git push --no-verify

REMOTE="${1:-origin}"
BRANCH=$(git symbolic-ref HEAD 2>/dev/null | sed 's/refs\/heads\///')
RANGE="${3:-@{push}..HEAD}"

# Guard: skip for pushes to secondary remotes (upstream, fork)
if [ "$REMOTE" != "origin" ]; then
    exit 0
fi

# Guard: skip for pushes to main/dev (branch-guard handles this)
if echo "$BRANCH" | grep -qiE '^(main|dev)$'; then
    exit 0
fi

# Check if @{push} exists (fresh branch with no upstream)
if ! git rev-parse "@{push}" &>/dev/null; then
    exit 0  # no upstream yet — nothing to compare against
fi

echo "[pre-push] $BRANCH → $REMOTE"

# 1. Binary files (block)
bad_binaries=$(git diff "$RANGE" --diff-filter=A --name-only \
    | grep -iE '\.(exe|dll|so|dylib|zip|tar\.gz|tgz|bin|whl)$' \
    || true)
if [ -n "$bad_binaries" ]; then
    echo "[pre-push] BLOCKED: prohibited binary types in push range:"
    echo "$bad_binaries" | sed 's/^/  /'
    exit 1
fi
echo "[pre-push] Binary files: PASS"

# 2. Oversized files (block)
oversized=$(git diff "$RANGE" --stat --diff-filter=A \
    | awk -F'|' '{
        file=$1; gsub(/[[:space:]]*$/,"",file);
        size=$2; gsub(/[^0-9]/,"",size);
        if (size+0 > 5000) print file" ("size" lines)"
    }' || true)
if [ -n "$oversized" ]; then
    echo "[pre-push] BLOCKED: oversized files (>5K lines) in push range:"
    echo "$oversized" | sed 's/^/  /'
    exit 1
fi
echo "[pre-push] File size: PASS"

# 3. Secrets glance (warning only)
secrets=$(git diff "$RANGE" --diff-filter=A \
    | grep -v '^\s*#' \
    | grep -v '\.env\.example\|test/fixtures/\|mock\|_test\.\|test\.' \
    | grep -iE '(api_key|token|password|secret)\s*=\s*['\''"][^'\''"]+['\''"]' \
    || true)
if [ -n "$secrets" ]; then
    echo "[pre-push] WARNING: possible secrets detected (review before push):"
    echo "$secrets" | sed 's/^/  /'
else
    echo "[pre-push] Secrets: PASS"
fi

# 4. Merge commits (warning only)
merges=$(git log --oneline --merges "$RANGE" 2>/dev/null | wc -l | tr -d ' ')
if [ "$merges" -gt 0 ]; then
    echo "[pre-push] WARNING: $merges merge commit(s). Feature branches typically rebase."
fi
echo "[pre-push] Merge commits: PASS"

echo "[pre-push] All checks PASS"
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
| Push to `feature/valid` | `git push origin feature/valid` | Exit 0, "All checks PASS" |
| Push to `main` or `dev` | `git push origin main` | Exit 0, skipped silently (branch-guard handles this) |
| Push to secondary remote | `git push upstream feature/x` | Exit 0, skipped silently |
| Fresh branch, no upstream | `git push -u origin feature/new` | Exit 0, skipped gracefully |
| Binary file added | `git add file.exe`, commit, push | Exit 1, "BLOCKED" |
| Large file added | Create 6K-line file, commit, push | Exit 1, "BLOCKED" |
| Secret in push range | `git add config.py` with `TOKEN=abc`, commit, push | Warning only, exit 0 |
| `--no-verify` | `git push --no-verify origin feature/x` | Exit 0, no output |
