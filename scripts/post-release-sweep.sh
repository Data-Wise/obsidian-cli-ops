#!/usr/bin/env bash
# scripts/post-release-sweep.sh — catch Tier-2 drift after a release.
#
# Reshaped from craft's post-release-sweep.sh. Tier-1 (canonical version files)
# is already gated by test_version_consistency.py + man-page-version-sync.test.js.
# This sweeps the long tail the version bump doesn't manage:
#   - documented counts (delegates to validate-counts.sh)
#   - stray old-version strings in secondary docs
#   - CHANGELOG ⇄ index.md currency (does the changelog mention the live version?)
#
# Usage:
#   scripts/post-release-sweep.sh           # report (exit 1 on findings)
#   scripts/post-release-sweep.sh --fix     # auto-fix mechanical items (counts)
set -uo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
FIX=0; [ "${1:-}" = "--fix" ] && FIX=1
ERR=0

VERSION="$(grep -m1 -oE 'VERSION="[0-9.]+"' src/obs.zsh | grep -oE '[0-9.]+')"
echo "post-release-sweep: current version ${VERSION}"

# 1) documented counts — delegate to the keystone validator.
echo ""
echo "[1/3] count consistency"
if [ "$FIX" = 1 ]; then
  scripts/validate-counts.sh --fix || ERR=$((ERR+1))
else
  scripts/validate-counts.sh || ERR=$((ERR+1))
fi

# 2) stray previous-version strings in secondary docs (Tier-2, report only).
echo ""
echo "[2/3] stray version strings (excluding history/changelog/specs)"
PREV="$(git tag --list 'v*' --sort=-v:refname | sed -n '2p' | tr -d v)"
if [ -n "$PREV" ] && [ "$PREV" != "$VERSION" ]; then
  HITS="$(grep -rFIn --include='*.md' "$PREV" . 2>/dev/null \
    | grep -vE 'node_modules|CHANGELOG|changelog|/releases/|/specs/|SPEC-|BRAINSTORM|v3\.0\.md|IMPLEMENTATION-ROADMAP|\.git/' || true)"
  if [ -n "$HITS" ]; then
    echo "  ⚠ previous version ${PREV} still referenced (review — may be intentional):"
    printf '%s\n' "$HITS" | sed 's/^/    /' | head -10
  else
    echo "  ✓ no stray ${PREV} references"
  fi
else
  echo "  · no distinct previous tag to compare"
fi

# 3) CHANGELOG currency — the live version should have a changelog section.
echo ""
echo "[3/3] changelog currency"
CL="docs_mkdocs/changelog.md"
if [ -f "$CL" ] && grep -qE "## v?${VERSION}\b" "$CL"; then
  echo "  ✓ changelog has a v${VERSION} section"
else
  echo "  ✗ changelog missing a v${VERSION} section ($CL)"
  ERR=$((ERR+1))
fi

echo ""
if [ "$ERR" -gt 0 ]; then
  echo "✗ post-release-sweep: ${ERR} area(s) need attention"; exit 1
fi
echo "✓ post-release-sweep: clean"
