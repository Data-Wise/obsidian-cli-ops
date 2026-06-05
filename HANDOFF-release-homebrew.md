# HANDOFF: local Homebrew release script (`scripts/release-homebrew.sh`)

> **Why this file exists:** the script below is new **code**, which branch-guard
> blocks on `dev`. It was authored from a `dev`-pinned session, so it's delivered
> here as markdown. Open a session **inside this worktree** to materialize it
> (new code is allowed on `feature/release-homebrew`).

Worktree: `~/.git-worktrees/obsidian-cli-ops/feature-release-homebrew` · branch `feature/release-homebrew` (off `dev`).

## What it does

Local, credential-free "automatic" Homebrew release for `obsidian-cli-ops` — mirrors the tap's reusable `update-formula.yml`, but runs on your machine with your own git creds (no `HOMEBREW_TAP_GITHUB_TOKEN` needed):

1. Resolve VERSION (arg, else `VERSION="…"` from `src/obs.zsh`).
2. Download the GitHub source tarball for `v<VERSION>` → compute sha256.
3. Update the tap formula: `url` → `v<VERSION>`, main package `sha256` → computed (first `sha256` only — leaves resource shas alone).
4. (optional) `brew update-python-resources` to fill transitive deps.
5. `brew style` + `brew audit --strict` as a release gate.
6. Show the diff. **Commit/push only with `--commit` / `--push`** (dry by default).

## Materialize it (run in a worktree session)

```bash
# from the worktree root:
mkdir -p scripts
# paste the script below into scripts/release-homebrew.sh, then:
chmod +x scripts/release-homebrew.sh
bash scripts/release-homebrew.sh --help          # smoke check
git add scripts/release-homebrew.sh
git commit -m "feat(release): local Homebrew release script (no cloud PAT)"
# then: gh pr create --base dev
# cleanup: git rm HANDOFF-release-homebrew.md before the PR (working artifact)
```

(Or just tell your worktree-session Claude: "create `scripts/release-homebrew.sh` from HANDOFF-release-homebrew.md, chmod +x, test `--help`, commit".)

## Usage (once installed)

```bash
scripts/release-homebrew.sh                      # dry run for current VERSION
scripts/release-homebrew.sh 3.2.1 --update-resources
scripts/release-homebrew.sh 3.2.1 --commit --push
```

`--tap DIR` overrides the tap path (default: `$OBS_TAP_DIR` → `brew --repository data-wise/tap` → `../homebrew-tap`).

## The script

```bash
#!/usr/bin/env bash
#
# release-homebrew.sh — local "automatic" Homebrew release for obsidian-cli-ops.
#
# Mirrors the tap's reusable .github/workflows/update-formula.yml, but runs on
# YOUR machine using your existing git credentials — no PAT/secret needed.
#
# Pipeline:
#   1. Resolve VERSION (arg, else VERSION="..." from src/obs.zsh).
#   2. Download the GitHub source tarball for tag v<VERSION> and compute sha256.
#   3. Update the tap formula: url -> v<VERSION>, main package sha256 -> computed.
#   4. (optional) `brew update-python-resources` to refresh the transitive deps.
#   5. `brew style` + `brew audit --strict` the formula (release gate).
#   6. Show the diff. Commit/push ONLY with --commit / --push (dry by default).
#
# Usage:
#   scripts/release-homebrew.sh [VERSION] [options]
#
# Options:
#   --tap DIR            Tap repo path (default: $OBS_TAP_DIR, then
#                        `brew --repository data-wise/tap`, then ../homebrew-tap)
#   --update-resources   Run `brew update-python-resources` (fills transitive deps)
#   --install-test       `brew install --build-from-source` + `obs version` smoke
#   --commit             git add + commit the formula in the tap
#   --push               implies --commit; push the tap branch
#   --skip-audit         skip `brew audit` (style still runs)
#   -h | --help          this help
#
# Examples:
#   scripts/release-homebrew.sh                 # dry run for the current VERSION
#   scripts/release-homebrew.sh 3.2.1 --update-resources
#   scripts/release-homebrew.sh 3.2.1 --commit --push
#
set -euo pipefail

REPO="Data-Wise/obsidian-cli-ops"
FORMULA_NAME="obsidian-cli-ops"
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

log()  { printf '\033[0;36m[release-brew]\033[0m %s\n' "$*"; }
ok()   { printf '\033[0;32m[release-brew]\033[0m %s\n' "$*"; }
warn() { printf '\033[0;33m[release-brew]\033[0m %s\n' "$*" >&2; }
die()  { printf '\033[0;31m[release-brew] ERROR:\033[0m %s\n' "$*" >&2; exit 1; }

# --- parse args ---
VERSION=""
TAP_DIR="${OBS_TAP_DIR:-}"
DO_RESOURCES=0 DO_INSTALL=0 DO_COMMIT=0 DO_PUSH=0 SKIP_AUDIT=0
while [[ $# -gt 0 ]]; do
    case "$1" in
        --tap)             TAP_DIR="$2"; shift 2 ;;
        --update-resources) DO_RESOURCES=1; shift ;;
        --install-test)    DO_INSTALL=1; shift ;;
        --commit)          DO_COMMIT=1; shift ;;
        --push)            DO_COMMIT=1; DO_PUSH=1; shift ;;
        --skip-audit)      SKIP_AUDIT=1; shift ;;
        -h|--help)         sed -n '2,33p' "${BASH_SOURCE[0]}"; exit 0 ;;
        -*)                die "unknown option: $1" ;;
        *)                 VERSION="$1"; shift ;;
    esac
done

command -v brew >/dev/null 2>&1 || die "Homebrew (brew) not found on PATH."

# --- 1. resolve VERSION ---
if [[ -z "$VERSION" ]]; then
    VERSION="$(sed -n 's/^VERSION="\([^"]*\)".*/\1/p' "$PROJECT_DIR/src/obs.zsh" | head -1)"
    [[ -n "$VERSION" ]] || die "could not read VERSION from src/obs.zsh; pass it explicitly."
fi
VERSION="${VERSION#v}"   # tolerate a leading v
log "Releasing $FORMULA_NAME v$VERSION to Homebrew"

# --- resolve the tap formula path ---
if [[ -z "$TAP_DIR" ]]; then
    TAP_DIR="$(brew --repository data-wise/tap 2>/dev/null || true)"
    [[ -d "$TAP_DIR" ]] || TAP_DIR="$PROJECT_DIR/../homebrew-tap"
fi
FORMULA="$TAP_DIR/Formula/$FORMULA_NAME.rb"
[[ -f "$FORMULA" ]] || die "formula not found: $FORMULA (set --tap or \$OBS_TAP_DIR)"
log "Tap formula: $FORMULA"

# --- 2. download tarball + sha256 ---
TARBALL_URL="https://github.com/$REPO/archive/refs/tags/v$VERSION.tar.gz"
TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT
log "Fetching $TARBALL_URL"
curl -fsSL "$TARBALL_URL" -o "$TMP/src.tar.gz" \
    || die "could not download tarball — is tag v$VERSION pushed/released yet?"

if command -v sha256sum >/dev/null 2>&1; then
    SHA="$(sha256sum "$TMP/src.tar.gz" | awk '{print $1}')"
else
    SHA="$(shasum -a 256 "$TMP/src.tar.gz" | awk '{print $1}')"
fi
ok "sha256 = $SHA"

# --- 3. update formula (url + main package sha256) ---
# Portable in-place edit (BSD/macOS + GNU): write to temp, move back.
tmp_formula="$TMP/formula.rb"
sed -e "s|/v[0-9][^/\"]*\.tar\.gz|/v$VERSION.tar.gz|" \
    -e "0,/sha256 \"[^\"]*\"/ s|sha256 \"[^\"]*\"|sha256 \"$SHA\"|" \
    "$FORMULA" > "$tmp_formula"
cp "$tmp_formula" "$FORMULA"
ok "formula url -> v$VERSION, package sha256 updated"

# --- 4. optional: refresh transitive python resources ---
if [[ "$DO_RESOURCES" -eq 1 ]]; then
    log "brew update-python-resources (transitive deps)…"
    brew update-python-resources "$FORMULA" \
        || warn "update-python-resources failed; reconcile resources manually."
    warn "Re-check the 6 CORE pins still match requirements.lock after this."
fi

# --- 5. validate (release gate) ---
log "brew style…"
brew style "$FORMULA" || die "brew style failed — fix before releasing."
if [[ "$SKIP_AUDIT" -eq 0 ]]; then
    log "brew audit --strict…"
    brew audit --strict --formula "$FORMULA" || die "brew audit failed (use --skip-audit to override)."
fi
ok "formula passes style$([[ $SKIP_AUDIT -eq 0 ]] && echo ' + audit')"

# --- 6. optional install smoke test ---
if [[ "$DO_INSTALL" -eq 1 ]]; then
    log "brew install --build-from-source (smoke test)…"
    brew install --build-from-source "$FORMULA"
    obs version || warn "'obs version' did not run cleanly post-install."
fi

# --- diff + commit/push ---
if git -C "$TAP_DIR" diff --quiet -- "Formula/$FORMULA_NAME.rb"; then
    ok "formula already up to date for v$VERSION — nothing to do."
    exit 0
fi
log "Formula diff:"; git -C "$TAP_DIR" --no-pager diff -- "Formula/$FORMULA_NAME.rb" || true

if [[ "$DO_COMMIT" -eq 1 ]]; then
    git -C "$TAP_DIR" add "Formula/$FORMULA_NAME.rb"
    git -C "$TAP_DIR" commit -m "$FORMULA_NAME: update to v$VERSION"
    ok "committed in tap ($(git -C "$TAP_DIR" branch --show-current))"
    if [[ "$DO_PUSH" -eq 1 ]]; then
        git -C "$TAP_DIR" push
        ok "pushed tap → remote"
    else
        log "Not pushed. Review, then: git -C \"$TAP_DIR\" push"
    fi
else
    warn "DRY RUN — formula edited locally but NOT committed."
    warn "Re-run with --commit (and --push) to publish, or revert with:"
    warn "  git -C \"$TAP_DIR\" checkout -- Formula/$FORMULA_NAME.rb"
fi
```

## Notes / gotchas

- **Run order at release:** tag `v3.2.1` must be pushed first (the script downloads `archive/refs/tags/v3.2.1.tar.gz`). For v3.2.1 specifically the tap formula already exists on tap branch `feature/obs-v3.2.1-venv` with `sha256 "TODO_FILL_AT_RELEASE"` — this script fills it.
- **`--update-resources` first time:** the v3.2.1 formula still needs its transitive `resource` blocks (markdown-it-py, pygments, certifi, …). Run with `--update-resources` once, then reconcile the 6 core pins back to `requirements.lock`.
- **Idempotent:** re-running when the formula already matches is a no-op.
- **Safe by default:** no `--commit`/`--push` ⇒ it only edits the formula locally and prints the diff.
- Uses `git -C` / `execFile`-style calls; no `execSync`. POSIX-ish bash, `sha256sum`/`shasum` fallback for Linux+macOS.
