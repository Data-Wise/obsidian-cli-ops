#!/usr/bin/env bash
# scripts/verify-caveats.sh — assert the Homebrew tap caveats are current.
#
# Reshaped from craft's verify-surfaces.sh assertion idea. The release pipeline's
# formula auto-bump only updates url+sha256; the caveats block is hand-written and
# drifted stale in v4.0.0 (generic, wrong tool count). This is the guard: it reads
# the published tap formula and fails if the caveats disagree with reality.
#
# Run AFTER the formula auto-bump (the tap is a separate repo). Needs `gh` auth.
#
# Usage:
#   scripts/verify-caveats.sh           # report; exit 1 on stale caveats
#   scripts/verify-caveats.sh --quiet   # exit code only
set -uo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
QUIET=0; [ "${1:-}" = "--quiet" ] && QUIET=1
TAP_REPO="Data-Wise/homebrew-tap"
FORMULA="Formula/obsidian-cli-ops.rb"

say() { [ "$QUIET" = 1 ] || echo "$@"; }

# Source of truth: live MCP tool count.
TOOLS=$(grep -c '@mcp.tool' "$ROOT/src/python/mcp_server.py")

# Fetch the published formula text.
if ! command -v gh >/dev/null 2>&1; then
  say "verify-caveats: gh not available — skipping (cannot read tap)"; exit 0
fi
CONTENT="$(gh api "repos/${TAP_REPO}/contents/${FORMULA}" --jq '.content' 2>/dev/null | base64 -D 2>/dev/null)"
if [ -z "$CONTENT" ]; then
  say "verify-caveats: could not read ${TAP_REPO}/${FORMULA} — skipping"; exit 0
fi

# Extract just the caveats heredoc.
CAVEATS="$(printf '%s\n' "$CONTENT" | awk '/def caveats/{f=1} f{print} /^    EOS/{if(f)exit}')"

ERR=0
# 1) tool count must appear as "<N> tools" in the MCP/Desktop line.
if ! printf '%s' "$CAVEATS" | grep -qE "\\b${TOOLS} tools\\b"; then
  say "✗ caveats do not mention the current MCP tool count (${TOOLS} tools)"
  ERR=$((ERR+1))
fi
# 2) absorbed command namespaces should be advertised.
for token in "obs config" "obs research"; do
  if ! printf '%s' "$CAVEATS" | grep -qF "$token"; then
    say "✗ caveats do not mention \`${token}\`"
    ERR=$((ERR+1))
  fi
done
# 3) the MCP key migration note (nexus -> obsidian-ops) should be present.
if ! printf '%s' "$CAVEATS" | grep -qE "obsidian-ops"; then
  say "✗ caveats do not mention the obsidian-ops MCP server key"
  ERR=$((ERR+1))
fi

if [ "$ERR" -gt 0 ]; then
  say ""
  say "Homebrew caveats are stale. Edit the caveats in:"
  say "  \$(brew --repository ${TAP_REPO})/${FORMULA}  (or the dev clone)"
  say "then commit + push the tap, and re-run."
  exit 1
fi
say "✓ caveats current (mentions ${TOOLS} tools, obs config/research, obsidian-ops)"
exit 0
