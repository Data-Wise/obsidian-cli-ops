#!/usr/bin/env bash
# scripts/validate-counts.sh — assert documented counts match the source of truth.
#
# Reshaped from craft's scripts/validate-counts.sh for obs's Python/ZSH layout:
# obs has no plugin manifest, so the source of truth is CODE (@mcp.tool /
# @mcp.resource in mcp_server.py, ai/providers/*.py), not a directory of files.
# Logic lives in the core module src/python/core/doc_counts.py (single source,
# shared with `obs doctor` and tests/test_doc_counts.py).
#
# Usage:
#   scripts/validate-counts.sh           # report; exit 1 on drift
#   scripts/validate-counts.sh --quiet   # exit code only (hooks/CI)
#   scripts/validate-counts.sh --fix     # auto-correct stated counts, then report
set -uo pipefail

# Anchor to THIS script's checkout (scripts/ is at the repo root), not the
# invoking cwd — so it validates the repo it ships in, even from a worktree.
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# Resolve an interpreter (mirror obs.zsh priority: $OBS_PYTHON → venvs → ambient).
PY="${OBS_PYTHON:-}"
if [ -z "$PY" ]; then
  for c in "$HOME/.local/share/obs/venv/bin/python3" \
           "/opt/homebrew/opt/obsidian-cli-ops/libexec/venv/bin/python3" \
           "$(command -v python3 || true)"; do
    [ -n "$c" ] && [ -x "$c" ] && PY="$c" && break
  done
fi
[ -z "$PY" ] && { echo "validate-counts: no python3 found" >&2; exit 2; }

cd "$ROOT/src/python" || exit 2
exec "$PY" core/doc_counts.py "$@"
