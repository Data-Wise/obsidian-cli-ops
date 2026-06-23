#!/usr/bin/env bash
# scripts/post-install-check.sh — verify a Homebrew-installed obs actually works.
#
# Encodes the project-memory lesson "audit-green ≠ installs clean": `brew audit`
# and `brew style` are static and never run post_install, so they can pass on a
# formula whose db-init crashes. The real gate is exercising the installed app.
# Run after `brew install/upgrade`, or after `brew reinstall --build-from-source`
# (the canonical release gate).
#
# Usage:
#   scripts/post-install-check.sh [expected_version]
#     expected_version  optional — assert `obs version` reports it (e.g. 4.0.0)
set -uo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
EXPECT="${1:-}"
FORMULA="data-wise/tap/obsidian-cli-ops"
ERR=0
ok()   { echo "  ✓ $*"; }
bad()  { echo "  ✗ $*"; ERR=$((ERR+1)); }

echo "post-install-check: ${FORMULA}"

# 1) obs on PATH + version
if ! command -v obs >/dev/null 2>&1; then
  bad "obs not on PATH (is the formula installed + linked?)"
else
  VER="$(obs version 2>/dev/null | grep -oE '[0-9]+\.[0-9]+\.[0-9]+' | head -1)"
  if [ -n "$EXPECT" ] && [ "$VER" != "$EXPECT" ]; then
    bad "obs version = ${VER:-?} (expected ${EXPECT})"
  else
    ok "obs version = ${VER:-?}"
  fi
fi

# 2) obs doctor exits clean — proves post_install db-init succeeded (the real gate)
if command -v obs >/dev/null 2>&1; then
  if obs doctor --layer database --layer docs >/tmp/obs-doctor.$$ 2>&1; then
    ok "obs doctor (database+docs) exits clean — db-init worked"
  else
    bad "obs doctor failed — db-init or doc-counts broken:"; sed 's/^/      /' /tmp/obs-doctor.$$
  fi
  rm -f /tmp/obs-doctor.$$
fi

# 3) installed mcp_server.py tool count == documented (catches a stale-tarball install)
CELLAR="$(brew --prefix "$FORMULA" 2>/dev/null)"
SERVER="$CELLAR/libexec/src/python/mcp_server.py"
[ -f "$SERVER" ] || SERVER="$(find "$CELLAR" -name mcp_server.py 2>/dev/null | head -1)"
if [ -f "$SERVER" ]; then
  INSTALLED=$(grep -c '@mcp.tool' "$SERVER")
  DOCUMENTED=$(grep -c '@mcp.tool' "$ROOT/src/python/mcp_server.py")
  if [ "$INSTALLED" = "$DOCUMENTED" ]; then
    ok "installed MCP tool count = ${INSTALLED} (matches source)"
  else
    bad "installed MCP tools = ${INSTALLED}, source = ${DOCUMENTED} (stale install?)"
  fi
else
  echo "  · skipped installed-server check (Cellar path not found)"
fi

# 4) tap formula url/sha256 resolve
if command -v gh >/dev/null 2>&1; then
  RB="$(gh api repos/Data-Wise/homebrew-tap/contents/Formula/obsidian-cli-ops.rb --jq '.content' 2>/dev/null | base64 -D 2>/dev/null)"
  SHA="$(printf '%s' "$RB" | grep -m1 -oE 'sha256 "[a-f0-9]{64}"')"
  [ -n "$SHA" ] && ok "tap formula has a 64-char sha256" || bad "tap formula sha256 missing/short"
fi

echo ""
if [ "$ERR" -gt 0 ]; then
  echo "✗ post-install-check: ${ERR} problem(s)"; exit 1
fi
echo "✓ post-install-check: all green"
