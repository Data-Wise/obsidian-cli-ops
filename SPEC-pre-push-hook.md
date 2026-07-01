# SPEC: Local Pre-Push Hook

**Date**: 2026-06-30
**Status**: Draft (adversarially reviewed, 7 issues found and fixed)
**Origin**: Pre/Post-Merge Check debate — agreed on two-layer enforcement.

---

## Layer Split

| Layer | What it checks | Where it lives | Blocks | Bypassable? |
|-------|---------------|----------------|--------|-------------|
| Local pre-push hook | Branch name, secrets, file size, merge commits, binary files | `.githooks/pre-push` | `git push` (local) | Yes (`--no-verify` — quality-of-life layer) |
| GitHub Actions | PR title, description, WIP, diff size, changelog | `.github/workflows/pr-metadata.yml` | PR merge (via branch protection) | No (server-side, authoritative) |
| branch-guard.sh | Direct pushes to main/dev | hooks/branch-guard.sh | Commit + push to main/dev | No (local, but non-bypassable by design) |

**Pre-push hook is quality-of-life, not security.** Branch-guard + CI are the enforcement layer. If a dev habitually uses `--no-verify`, CI still catches the issue at PR time.

---

## Fixes Applied (from adversarial review)

| # | Issue | Before | After |
|---|-------|--------|-------|
| 1 | Secrets regex too eager | Inline grep, no comment skip | Use `gitleaks` if available, fallback to anchored regex that skips comments + known patterns |
| 2 | File size check O(n) on all files | `find . -size +1M` | `git diff --stat` on push range only |
| 3 | Stale remote ref | `origin/dev..HEAD` — assumes fetched | `@{push}` range, handles missing upstream gracefully |
| 4 | Hardcoded `origin` | `origin/dev` | Read remote from hook args (`$1`), fallback `@{push}` |
| 5 | Binary check misses staged files | `git diff HEAD` | `git diff --stat @{push}..HEAD` (full push range) |
| 6 | `--no-verify` vulnerability unaddressed | No enforcement statement | Explicit quality-of-life vs enforcement layer table above |
| 7 | No installation automation | Manual `git config` | Add to `install.sh` + README |

---

## Checks — Local Pre-Push Hook

Runs on every `git push`. Fail-fast — first failure stops the push. Uses `REMOTE` from hook args (`$1`), falls back to `@{push}` if no remote specified.

### 0. Guard: Skip if push target isn't the configured remote

Only run checks for pushes to the primary remote (`origin` by default). Skip for pushes to `upstream`, `fork`, or secondary remotes to avoid friction in fork workflows.

### 1. Branch name convention

```
feature/board-sync        ✅ PASS
fix/scan-robustness       ✅ PASS
docs/refcard-rewrite      ✅ PASS
main                      ❌ BLOCKED (branch-guard handles this too — redundant but harmless)
dev                       ❌ BLOCKED (redundant)
dev-tools-config          ⚠️ NOW PASSES (strict prefix match: ^(main|dev)$, not substring)
random                    ⚠️ WARNING (doesn't match feature/*, fix/*, docs/*, chore/*, refactor/*, test/*)
```

Uses strict prefix match: `^(main|dev)$` — no longer triggers on `dev-tools` or `feature/dev-integration`.

### 2. Secrets in diff

Check push range `@{push}..HEAD` for potential secrets.

```bash
# Tier 1: Use gitleaks if installed (brew install gitleaks)
if command -v gitleaks &>/dev/null; then
    gitleaks detect --source . --log-opts "@{push}..HEAD" --no-git
fi

# Tier 2: Fallback inline grep (less accurate but always available)
git diff "@{push}..HEAD" --diff-filter=A \
    | grep -v '^\s*#' \       # skip comments
    | grep -v '\.env\.example\|test/fixtures/\|mock\|_test\.\|test\.' \
    | grep -E '(api_key|token|password|secret)\s*=\s*['\''"][^'\''"]+['\''"]' \
    && exit 1 || true
```

### 3. File size limits

Use `git diff --stat` on push range only — O(diff size), not O(repo size).

```bash
git diff "@{push}..HEAD" --stat --diff-filter=A \
    | awk -F'|' '{print $2}' \
    | grep -Eo '[0-9]+' \
    | sort -rn \
    | head -1
```

- Any single file added > 1MB → BLOCKED
- Total diff additions > 10MB → BLOCKED

### 4. Merge commits (warning only)

Check push range for merge commits. Non-blocking.

```bash
# Local log check — no remote fetch needed
merges=$(git log --oneline --merges "@{push}..HEAD" 2>/dev/null | wc -l | tr -d ' ')
if [ "$merges" -gt 0 ]; then
    echo "[pre-push] WARNING: $merges merge commit(s) in branch. Feature branches should rebase, not merge from dev."
    echo "  Fix: git rebase dev"
fi
```

Graceful if `@{push}` doesn't exist yet (fresh branch): use `HEAD~1..HEAD` as fallback.

### 5. Binary files

Check push range for prohibited binary types. Allow common asset types.

```bash
bad_binaries=$(git diff "@{push}..HEAD" --diff-filter=A --name-only \
    | grep -iE '\.(exe|dll|so|dylib|zip|tar\.gz|tgz|bin)$' \
    || true)
```

Allow: `.png`, `.jpg`, `.svg`, `.ico`, `.pdf`, `.woff`, `.woff2`, `.mp4`

---

## GitHub Actions (already created)

File: `.github/workflows/pr-metadata.yml`

- PR title matches conventional commits (`feat:`, `fix:`, `docs:`, `chore:`, `refactor:`, `test:`, `style:`, `perf:`, `ci:`, `build:`, `revert:`)
- PR description non-empty
- No WIP/Draft markers
- Diff size ≤ 2000 lines
- Changelog entry if `feat:` or `fix:` type

---

## Installation

### install.sh addition

```bash
# Install pre-push hook
mkdir -p .githooks
cp scripts/pre-push.sh .githooks/pre-push
chmod +x .githooks/pre-push
git config core.hooksPath .githooks
```

### README addition

```
## Local Hooks

This repo includes a pre-push hook that validates branch names, secrets, and
file sizes before pushing. Installed automatically by `install.sh`.

To skip (temporarily): `git push --no-verify`
To install manually: `git config core.hooksPath .githooks`
```

---

## Testing

| Test | Command | Expected |
|------|---------|----------|
| Push to `main` | `git push origin main` | Exit 1, "BLOCKED" |
| Push to `dev` | `git push origin dev` | Exit 1, "BLOCKED" |
| Push to `feature/valid` | `git push origin feature/valid` | Exit 0 |
| Push to `feature/dev-tools` | `git push origin feature/dev-tools` | Exit 0 (no false positive) |
| Secret in push range | Add `API_KEY=abc` to a file, commit, push | Exit 1, "BLOCKED" |
| Secret in commented line | Add `# TOKEN=abc` and commit | Exit 0 (comment skipped) |
| Binary file added | `git add file.exe`, commit, push | Exit 1, "BLOCKED" |
| Large file added | Create 2MB file, commit, push | Exit 1, "BLOCKED" |
| Fresh branch, no upstream | `git push -u origin feature/new` | Exit 0 (graceful fallback) |
| Push to secondary remote | `git push upstream feature/x` | Exit 0 (skipped — not primary remote) |
| `--no-verify` | `git push --no-verify origin feature/x` | Exit 0, no hook output |

---

## Open Questions (for grilling)

1. Should the pre-push hook also validate **commit message format** (conventional commits per commit)?
2. Should it check that **every commit** in the push range has a `Signed-off-by` line?
3. Should we auto-install `gitleaks` via install.sh, or keep it as optional tier-1?
4. Should the pre-push hook also run **markdownlint** on changed `.md` files before push?
5. Should the hook fail on merge commits (blocking) instead of just warning?
