#!/bin/bash
#
# install.sh — non-Homebrew installer for obsidian-cli-ops (obs)
#
# Three responsibilities:
#   1. Symlink the zsh launcher into ~/.config/zsh/functions.
#   2. Wire the pre-push git hook from .githooks/.
#   3. Provision the core Python deps into an ISOLATED venv
#      (~/.local/share/obs/venv) from requirements.lock — so obs runs with
#      zero manual `pip install` and survives system-python upgrades.
#
# Idempotent: re-running is cheap. The venv is only rebuilt when
# requirements.lock changes (tracked via a content-hash sentinel).
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOCKFILE="$PROJECT_DIR/requirements.lock"
FUNCS_DIR="$HOME/.config/zsh/functions"
DATA_DIR="${XDG_DATA_HOME:-$HOME/.local/share}/obs"
VENV_DIR="$DATA_DIR/venv"
SENTINEL="$DATA_DIR/.deps.sentinel"
MAN_DIR="${XDG_DATA_HOME:-$HOME/.local/share}/man/man1"

log()  { printf '%s\n' "$*"; }
warn() { printf '%s\n' "$*" >&2; }

# Cross-platform SHA-256 of a file (macOS: shasum, Linux/CI: sha256sum).
hash_file() {
    if command -v sha256sum >/dev/null 2>&1; then
        sha256sum "$1" | awk '{print $1}'
    elif command -v shasum >/dev/null 2>&1; then
        shasum -a 256 "$1" | awk '{print $1}'
    else
        cksum "$1" | awk '{print $1}'
    fi
}

# --- 1. Symlink the launcher (original behavior, now dir-safe) ---
mkdir -p "$FUNCS_DIR"
ln -sf "$PROJECT_DIR/src/obs.zsh" "$FUNCS_DIR/obs.zsh"
log "Symlinked obs.zsh to $FUNCS_DIR/obs.zsh"

# --- 1b. Symlink the man page so `man obs` works (Homebrew handles this via
#         the formula's man1 install; this covers the from-source path). ---
if [[ -f "$PROJECT_DIR/man/man1/obs.1" ]]; then
    mkdir -p "$MAN_DIR"
    ln -sf "$PROJECT_DIR/man/man1/obs.1" "$MAN_DIR/obs.1"
    log "Symlinked obs.1 to $MAN_DIR/obs.1"
    case ":${MANPATH:-}:" in
        *":${MAN_DIR%/man1}:"*) ;;
        *) log "  (add ${MAN_DIR%/man1} to MANPATH if 'man obs' is not found)" ;;
    esac
fi

# --- 1c. Wire the pre-push hook via git config ---
if [[ -f "$PROJECT_DIR/.githooks/pre-push" ]]; then
    git config core.hooksPath "$PROJECT_DIR/.githooks"
    log "Wired pre-push hook from .githooks/pre-push (advisory only, never blocks)"
fi

# --- 2. Provision the isolated dependency environment ---
if [[ ! -f "$LOCKFILE" ]]; then
    warn "ERROR: requirements.lock not found at $LOCKFILE"
    exit 1
fi

PYTHON_BOOTSTRAP="$(command -v python3 || true)"
if [[ -z "$PYTHON_BOOTSTRAP" ]]; then
    warn "ERROR: python3 not found on PATH; cannot provision obs dependencies."
    exit 1
fi

LOCK_HASH="$(hash_file "$LOCKFILE")"

if [[ -x "$VENV_DIR/bin/python" && -f "$SENTINEL" && "$(cat "$SENTINEL")" == "$LOCK_HASH" ]]; then
    log "obs dependencies already provisioned (lock unchanged) → $VENV_DIR"
else
    log "Provisioning isolated obs environment at $VENV_DIR ..."
    mkdir -p "$DATA_DIR"
    # Rebuild cleanly to avoid a stale or partially-created venv.
    rm -rf "$VENV_DIR"
    if ! "$PYTHON_BOOTSTRAP" -m venv "$VENV_DIR"; then
        warn "ERROR: failed to create venv at $VENV_DIR"
        exit 1
    fi
    export PYO3_USE_ABI3_FORWARD_COMPATIBILITY=1
    "$VENV_DIR/bin/python" -m pip install --quiet --upgrade pip >/dev/null 2>&1 || true
    if ! "$VENV_DIR/bin/python" -m pip install --quiet -r "$LOCKFILE"; then
        warn "ERROR: failed to install dependencies from $LOCKFILE"
        exit 1
    fi
    printf '%s\n' "$LOCK_HASH" > "$SENTINEL"
    log "✓ Installed core deps into $VENV_DIR"
fi

# --- 3. Configure Claude Desktop MCP if Darwin ---
if [[ "$(uname -s)" == "Darwin" ]]; then
    if [[ -x "$VENV_DIR/bin/python" ]]; then
        "$VENV_DIR/bin/python" "$PROJECT_DIR/scripts/configure_mcp.py" || warn "WARNING: Failed to configure Claude Desktop MCP server automatically."
    else
        "$PYTHON_BOOTSTRAP" "$PROJECT_DIR/scripts/configure_mcp.py" || warn "WARNING: Failed to configure Claude Desktop MCP server automatically."
    fi
fi

log ""
log "obs is ready — the launcher auto-detects $VENV_DIR (no OBS_PYTHON needed)."
log "Reload your shell, or run: source $FUNCS_DIR/obs.zsh"
