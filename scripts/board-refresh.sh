#!/usr/bin/env zsh
# board-refresh.sh — Refresh the deterministic _ACTION-BOARD.md in the Obsidian vault.
# Called by launchd (com.data-wise.obs-board-refresh) weekly on Monday 09:15.
# Chains: atlas sync -> obs board refresh -> obs doctor drift check.
#
# This script is idempotent: same atlas state -> same board content -> zero diff.

set -euo pipefail

VAULT_NAME="Documents"  # obs DB vault name (Research/ is a sub-vault)
OBS_CLI="/Users/dt/projects/dev-tools/obsidian-cli-ops/src/python/obs_cli.py"
LOG_PREFIX="[board-refresh]"

log()  { echo "$LOG_PREFIX $(date '+%H:%M:%S')  $*"; }
warn() { echo "$LOG_PREFIX WARN  $(date '+%H:%M:%S')  $*" >&2; }
fail() { echo "$LOG_PREFIX ERROR $(date '+%H:%M:%S')  $*" >&2; exit 1; }

_resolve_python() {
    # 1. Explicit override.
    if [[ -n "${OBS_PYTHON:-}" && -x "${OBS_PYTHON%% *}" ]]; then
        echo "$OBS_PYTHON"
        return 0
    fi

    # 2. install.sh-provisioned user venv.
    local user_venv="${XDG_DATA_HOME:-$HOME/.local/share}/obs/venv/bin/python"
    if [[ -x "$user_venv" ]]; then
        echo "$user_venv"
        return 0
    fi

    # 3. Homebrew formula venv.
    if command -v brew >/dev/null 2>&1; then
        local brew_prefix brew_venv
        brew_prefix="$(brew --prefix obsidian-cli-ops 2>/dev/null)"
        brew_venv="$brew_prefix/libexec/venv/bin/python"
        if [[ -n "$brew_prefix" && -x "$brew_venv" ]]; then
            echo "$brew_venv"
            return 0
        fi
    fi

    # 4. Last resort: ambient python3.
    command -v python3
}

OBS_PYTHON="$(_resolve_python)"
if [[ -z "$OBS_PYTHON" ]]; then
    fail "Could not find a usable python3 interpreter"
fi

_obs() { "$OBS_PYTHON" "$OBS_CLI" "$@"; }

log "=== Board Refresh ==="
log "Vault: $VAULT_NAME"

# --- Step 1: Sync atlas registry ---
log "atlas sync --research ..."
if ! atlas sync --research --dry-run 2>&1; then
    warn "atlas sync failed (non-fatal — board data may be stale)"
fi

# --- Step 2: Render deterministic board ---
log "obs board refresh ..."
OUTPUT=$(_obs board refresh --vault "$VAULT_NAME" --dry-run 2>&1) || {
    fail "obs board refresh failed"
}

ACTION=$(echo "$OUTPUT" | awk '{print $1}' | tr -d ':')
log "Board render complete (action=$ACTION)"
echo "$OUTPUT"

# If the board actually changed, run the real write (no --dry-run)
if [[ "$ACTION" == "dry-run" ]]; then
    log "Board changed — writing to vault ..."
    _obs board refresh --vault "$VAULT_NAME" > /dev/null 2>&1 || warn "Write failed"
    log "Board updated in vault"
fi

# --- Step 3: Check for vault/index drift ---
log "obs doctor --layer sync ..."
DRIFT=$(_obs doctor --layer sync 2>&1) || true
echo "$DRIFT"
if echo "$DRIFT" | grep -qiE "(ghost|missing|error)"; then
    log "Drift detected — consider: obs scan --prune"
fi

log "=== Board Refresh Complete ==="
