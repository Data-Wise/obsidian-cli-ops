#!/bin/zsh
#
# Obsidian CLI Ops (obs)
# ======================
# CLI tool for managing Obsidian vaults with AI-powered graph analysis.
#
# Version: 3.2.2
# Author: Data-Wise
# Project: obsidian-cli-ops
#
# DEPENDENCIES:
# - python3 with obs core deps provisioned in an ISOLATED env (see requirements.lock):
#     * Homebrew: libexec/venv (formula sets $OBS_PYTHON)
#     * install.sh: ~/.local/share/obs/venv
#   The launcher NEVER assumes ambient python3 has the deps (see _obs_resolve_python).
# - jq (for vault operations)
#
# CONFIGURATION:
# - Database: ~/.config/obs/obsidian_vaults.db
# - Last vault: ~/.config/obs/last_vault
# - iCloud default: ~/Library/Mobile Documents/iCloud~md~obsidian/Documents

# --- Configuration ---
LAST_VAULT_FILE="$HOME/.config/obs/last_vault"
ICLOUD_OBSIDIAN="$HOME/Library/Mobile Documents/iCloud~md~obsidian/Documents"

# --- Python interpreter resolution ---
# obs runs the bundled obs_cli.py against an interpreter that MUST have the core
# deps from requirements.lock provisioned. Resolve, in priority order:
#   1. Explicit $OBS_PYTHON (user override, or the Homebrew formula launcher)
#   2. install.sh-provisioned user venv (~/.local/share/obs/venv) — checked
#      before brew so we can SKIP the `brew --prefix` subprocess (resolution
#      runs once when this file is sourced; keeps shell startup fast).
#   3. Homebrew formula venv (libexec/venv) — probed only when no user venv.
#   4. Last resort: ambient python3 — deps may be MISSING, so warn loudly.
# Resolving to a bare `command -v python3` was the v3.2.0 crash: in the field it
# landed on a dep-less python@3.x and obs died with ModuleNotFoundError: 'rich'.
_obs_resolve_python() {
    # 1. Honor an explicit override if its interpreter actually exists.
    if [[ -n "$OBS_PYTHON" && -x "${OBS_PYTHON%% *}" ]]; then
        echo "$OBS_PYTHON"
        return 0
    fi

    # 2. install.sh-provisioned user venv. Checked before brew so the common
    #    dev-from-source case never pays for the `brew --prefix` subprocess.
    local user_venv="${XDG_DATA_HOME:-$HOME/.local/share}/obs/venv/bin/python"
    if [[ -x "$user_venv" ]]; then
        echo "$user_venv"
        return 0
    fi

    # 3. Homebrew formula venv (libexec/venv) — only reached when no user venv
    #    exists; brew --prefix is a subprocess, so it is intentionally last-ish.
    if command -v brew >/dev/null 2>&1; then
        local brew_prefix brew_venv
        brew_prefix="$(brew --prefix obsidian-cli-ops 2>/dev/null)"
        brew_venv="$brew_prefix/libexec/venv/bin/python"
        if [[ -n "$brew_prefix" && -x "$brew_venv" ]]; then
            echo "$brew_venv"
            return 0
        fi
    fi

    # 4. Last resort: ambient interpreter, which may lack obs's dependencies.
    local ambient
    ambient="$(command -v python3 2>/dev/null)"
    if [[ -n "$ambient" ]]; then
        echo "[obs] WARN: no isolated environment found; falling back to ambient python3 ($ambient)." >&2
        echo "[obs] WARN: obs dependencies may be missing. Provision an isolated env:" >&2
        echo "[obs] WARN:   brew reinstall obsidian-cli-ops   # Homebrew" >&2
        echo "[obs] WARN:   ./install.sh                      # manual install" >&2
        echo "$ambient"
        return 0
    fi

    echo "[obs] ERROR: no python3 interpreter found on PATH." >&2
    return 1
}

OBS_PYTHON="$(_obs_resolve_python)"

_ensure_config_dir() {
    mkdir -p "$HOME/.config/obs"
}

_save_last_vault() {
    local vault_id=$1
    _ensure_config_dir
    echo "$vault_id" > "$LAST_VAULT_FILE"
    _log_verbose "Saved last vault: $vault_id"
}

_get_last_vault() {
    if [[ -f "$LAST_VAULT_FILE" ]]; then
        cat "$LAST_VAULT_FILE"
    fi
}

# Defaults
VERBOSE=false
VERSION="3.2.2"

# --- Helper Functions ---

_log() {
    local type=$1
    local msg=$2

    # Check if colors should be disabled
    if [[ -n "$NO_COLOR" ]] || [[ ! -t 1 ]]; then
        # No color output
        case $type in
            "INFO") echo "[INFO] $msg" ;;
            "SUCCESS") echo "[OK] $msg" ;;
            "WARN") echo "[WARN] $msg" ;;
            "ERROR") echo "[ERROR] $msg" ;;
        esac
    else
        # Colored output
        case $type in
            "INFO") echo "\033[0;34m[INFO]\033[0m $msg" ;;
            "SUCCESS") echo "\033[0;32m[OK]\033[0m $msg" ;;
            "WARN") echo "\033[0;33m[WARN]\033[0m $msg" ;;
            "ERROR") echo "\033[0;31m[ERROR]\033[0m $msg" ;;
        esac
    fi
}

_log_verbose() {
    if [[ "$VERBOSE" == "true" ]]; then
        if [[ -n "$NO_COLOR" ]] || [[ ! -t 1 ]]; then
            echo "[VERBOSE] $1"
        else
            echo "\033[0;90m[VERBOSE]\033[0m $1"
        fi
    fi
}

# --- Subcommands ---

obs_help() {
    local show_all=${1:-false}

    echo "Obsidian CLI Ops (obs) v$VERSION"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    echo "📖 Usage: obs [command] [options]"
    echo ""

    if [[ "$show_all" == "true" ]]; then
        echo "🎯 PRIMARY COMMANDS"
        echo "  obs                       List vaults (or show last vault stats)"
        echo "  obs stats [vault]         Show vault statistics"
        echo "  obs discover <path>       Find vaults in directory"
        echo ""

        echo "📊 GRAPH ANALYSIS"
        echo "  obs analyze <vault>       Analyze vault graph metrics"
        echo "  obs health <vault>        Vault health dashboard"
        echo ""

        echo "🤖 AI FEATURES"
        echo "  obs ai status             Show AI provider status"
        echo "  obs ai setup              Interactive AI setup wizard"
        echo "  obs ai test               Test all AI providers"
        echo "  obs ai similar <note>     Find similar notes"
        echo "  obs ai analyze <note>     Analyze note with AI"
        echo "  obs ai duplicates <vault> Find duplicate notes"
        echo "  obs ai suggest-links <note> Suggest new links"
        echo "  obs ai gaps <vault>       Find knowledge gaps"
        echo "  obs ai summarize <vault>  Summarize vault themes"
        echo "  obs ai refactor <vault>   AI-powered reorganization"
        echo "  obs ai merge-suggest <vault> Find merge candidates"
        echo "  obs ai tag-suggest <target>  Suggest tags for notes"
        echo "  obs ai quality <target>      Score note quality"
        echo ""

        echo "🔧 UTILITIES"
        echo "  obs help [--all]          Show help"
        echo "  obs version               Show version"
        echo ""
        echo "📍 DEFAULT ROOT: $ICLOUD_OBSIDIAN"
    else
        echo "🎯 QUICK START"
        echo "  obs                       List your vaults"
        echo "  obs stats <vault>         Show vault statistics"
        echo "  obs discover <path>       Find new vaults"
        echo ""
        echo "💡 TIP: Use 'obs stats <vault>' to see vault details!"
        echo ""
        echo "More commands: obs help --all"
    fi
    echo ""
}

obs_version() {
    echo "obs (Obsidian CLI Ops) version $VERSION"
    echo ""
    echo "A command-line tool for managing Obsidian vaults"
    echo "with AI-powered knowledge graph analysis."
    echo ""
    echo "Repository: https://github.com/Data-Wise/obsidian-cli-ops"
    echo "Documentation: https://data-wise.github.io/obsidian-cli-ops/"
}

# --- Legacy v1.x Commands Removed ---
# The following v1.x commands were removed in Phase 7.1 Part 3 (CLI consolidation):
# - obs_check() → dependency checking (low value)
# - obs_audit() → vault structure audit (OBS_ROOT required)
# - obs_sync() → configuration sync (OBS_ROOT required)
# - obs_install() → plugin installation (OBS_ROOT required)
# - obs_search() → plugin search (low usage)
# - obs_list() → vault listing (replaced by 'obs vaults')

# --- Knowledge Graph Commands (v2.0) ---

_get_python_cli() {
    # Get path to Python CLI
    # When obs.zsh is in src/, Python CLI is in src/python/
    local script_path="${(%):-%x}"  # Path to current script
    local script_dir="$(cd "$(dirname "$script_path")" && pwd)"
    local python_cli="$script_dir/python/obs_cli.py"

    if [[ ! -f "$python_cli" ]]; then
        _log "ERROR" "Python CLI not found at: $python_cli" >&2
        _log "ERROR" "Script dir: $script_dir" >&2
        return 1
    fi

    echo "$python_cli"
}

obs_discover() {
    local python_cli=$(_get_python_cli) || return 1
    local path=${1:-.}  # Default to current directory

    _log_verbose "Running vault discovery in: $path"

    # Build command
    local cmd=("$python_cli" "discover" "$path")

    # Add verbose flag if enabled
    if [[ "$VERBOSE" == "true" ]]; then
        cmd+=(--verbose)
    fi

    # Add --scan flag if requested
    if [[ "$2" == "--scan" ]]; then
        cmd+=(--scan)
    fi

    $OBS_PYTHON "${cmd[@]}"
}

obs_analyze() {
    local python_cli=$(_get_python_cli) || return 1
    local vault=$1

    if [[ -z "$vault" ]]; then
        _log "ERROR" "Vault name or ID required"
        echo "Usage: obs analyze <vault>"
        echo ""
        echo "Use vault name or ID prefix (see: obs vaults)"
        return 1
    fi

    _log_verbose "Analyzing vault: $vault"

    # Build command
    local cmd=("$python_cli" "analyze" "$vault")

    # Add verbose flag if enabled
    if [[ "$VERBOSE" == "true" ]]; then
        cmd+=(--verbose)
    fi

    $OBS_PYTHON "${cmd[@]}"
}

obs_vaults() {
    local python_cli=$(_get_python_cli) || return 1

    _log_verbose "Listing vaults in database"

    $OBS_PYTHON "$python_cli" vaults
}

obs_stats() {
    local python_cli=$(_get_python_cli) || return 1
    local vault_id=$1

    _log_verbose "Showing statistics"

    if [[ -n "$vault_id" ]]; then
        $OBS_PYTHON "$python_cli" stats --vault "$vault_id"
    else
        $OBS_PYTHON "$python_cli" stats
    fi
}

obs_health() {
    local python_cli=$(_get_python_cli) || return 1
    local vault=$1

    if [[ -z "$vault" ]]; then
        _log "ERROR" "Vault name or ID required"
        echo "Usage: obs health <vault>"
        return 1
    fi

    _log_verbose "Running health check: $vault"

    # Build command
    local cmd=("$python_cli" "health" "$vault")

    # Pass --json flag if present
    shift
    while [[ "$1" == --* ]]; do
        cmd+=("$1")
        shift
    done

    $OBS_PYTHON "${cmd[@]}"
}

# --- AI Commands (v2.0) ---

obs_ai() {
    local python_cli=$(_get_python_cli) || return 1
    local subcmd=$1
    shift

    case "$subcmd" in
        status)
            _log_verbose "Showing AI provider status"
            $OBS_PYTHON "$python_cli" "ai" "status"
            ;;

        setup)
            _log_verbose "Running AI setup wizard"
            $OBS_PYTHON "$python_cli" "ai" "setup"
            ;;

        test)
            _log_verbose "Testing AI providers"
            local cmd=("$python_cli" "ai" "test")

            # Add --provider flag if specified
            if [[ "$1" == "--provider" ]]; then
                cmd+=(--provider "$2")
            fi

            $OBS_PYTHON "${cmd[@]}"
            ;;

        similar)
            local note_id=$1
            if [[ -z "$note_id" ]]; then
                _log "ERROR" "Note ID required"
                echo "Usage: obs ai similar <note_id>"
                return 1
            fi
            _log_verbose "Finding similar notes"
            $OBS_PYTHON "$python_cli" "ai" "similar" "$note_id"
            ;;

        analyze)
            local note_id=$1
            if [[ -z "$note_id" ]]; then
                _log "ERROR" "Note ID required"
                echo "Usage: obs ai analyze <note_id>"
                return 1
            fi
            _log_verbose "Analyzing note with AI"
            $OBS_PYTHON "$python_cli" "ai" "analyze" "$note_id"
            ;;

        duplicates)
            local vault_id=$1
            if [[ -z "$vault_id" ]]; then
                _log "ERROR" "Vault ID required"
                echo "Usage: obs ai duplicates <vault_id>"
                return 1
            fi
            _log_verbose "Finding duplicate notes"
            $OBS_PYTHON "$python_cli" "ai" "duplicates" "$vault_id"
            ;;

        suggest-links)
            local note_id=$1
            if [[ -z "$note_id" ]]; then
                _log "ERROR" "Note ID required"
                echo "Usage: obs ai suggest-links <note_id>"
                return 1
            fi
            shift
            _log_verbose "Suggesting links for note"
            local cmd=("$python_cli" "ai" "suggest-links" "$note_id")
            while [[ "$1" == --* ]]; do
                cmd+=("$1" "$2")
                shift 2
            done
            [[ "$VERBOSE" == "true" ]] && cmd+=(--verbose)
            $OBS_PYTHON "${cmd[@]}"
            ;;

        gaps)
            local vault_id=$1
            if [[ -z "$vault_id" ]]; then
                _log "ERROR" "Vault ID required"
                echo "Usage: obs ai gaps <vault_id>"
                return 1
            fi
            shift
            _log_verbose "Finding knowledge gaps"
            local cmd=("$python_cli" "ai" "gaps" "$vault_id")
            while [[ "$1" == --* ]]; do
                cmd+=("$1" "$2")
                shift 2
            done
            [[ "$VERBOSE" == "true" ]] && cmd+=(--verbose)
            $OBS_PYTHON "${cmd[@]}"
            ;;

        summarize)
            local vault_id=$1
            if [[ -z "$vault_id" ]]; then
                _log "ERROR" "Vault ID required"
                echo "Usage: obs ai summarize <vault_id>"
                return 1
            fi
            shift
            _log_verbose "Summarizing vault"
            local cmd=("$python_cli" "ai" "summarize" "$vault_id")
            while [[ "$1" == --* ]]; do
                cmd+=("$1" "$2")
                shift 2
            done
            [[ "$VERBOSE" == "true" ]] && cmd+=(--verbose)
            $OBS_PYTHON "${cmd[@]}"
            ;;

        refactor)
            local vault_id=$1
            if [[ -z "$vault_id" ]]; then
                _log "ERROR" "Vault name or ID required"
                echo "Usage: obs ai refactor <vault>"
                return 1
            fi
            shift
            _log_verbose "Analyzing vault for refactoring"
            local cmd=("$python_cli" "ai" "refactor" "$vault_id")
            while [[ "$1" == --* ]]; do
                if [[ "$1" == "--dry-run" ]]; then
                    cmd+=("$1")
                    shift
                else
                    cmd+=("$1" "$2")
                    shift 2
                fi
            done
            [[ "$VERBOSE" == "true" ]] && cmd+=(--verbose)
            $OBS_PYTHON "${cmd[@]}"
            ;;

        merge-suggest)
            local vault_id=$1
            if [[ -z "$vault_id" ]]; then
                _log "ERROR" "Vault name or ID required"
                echo "Usage: obs ai merge-suggest <vault> [--threshold N] [--json]"
                return 1
            fi
            shift
            _log_verbose "Finding merge candidates"
            # --json/--verbose are GLOBAL argparse flags: they must precede the
            # subcommand or obs_cli.py rejects them as unrecognized. Route them
            # to gflags (before "ai"); keep value flags with the subcommand.
            local gflags=()
            [[ "$VERBOSE" == "true" ]] && gflags+=(--verbose)
            local subargs=()
            while [[ "$1" == --* ]]; do
                case "$1" in
                    --json) gflags+=(--json); shift ;;
                    --verbose|-v) gflags+=(--verbose); shift ;;
                    --threshold|--provider) subargs+=("$1" "$2"); shift 2 ;;
                    *) subargs+=("$1"); shift ;;
                esac
            done
            $OBS_PYTHON "$python_cli" "${gflags[@]}" "ai" "merge-suggest" "$vault_id" "${subargs[@]}"
            ;;

        tag-suggest)
            local target=$1
            if [[ -z "$target" ]]; then
                _log "ERROR" "Vault name/ID or note ID required"
                echo "Usage: obs ai tag-suggest <vault|note_id> [--apply] [--min-confidence N]"
                return 1
            fi
            shift
            _log_verbose "Suggesting tags"
            # --json/--verbose are GLOBAL flags (must precede the subcommand);
            # --apply is a subcommand boolean, --min-confidence/--provider take values.
            local gflags=()
            [[ "$VERBOSE" == "true" ]] && gflags+=(--verbose)
            local subargs=()
            while [[ "$1" == --* ]]; do
                case "$1" in
                    --json) gflags+=(--json); shift ;;
                    --verbose|-v) gflags+=(--verbose); shift ;;
                    --min-confidence|--provider) subargs+=("$1" "$2"); shift 2 ;;
                    *) subargs+=("$1"); shift ;;
                esac
            done
            $OBS_PYTHON "$python_cli" "${gflags[@]}" "ai" "tag-suggest" "$target" "${subargs[@]}"
            ;;

        quality)
            local target=$1
            if [[ -z "$target" ]]; then
                _log "ERROR" "Vault name/ID or note ID required"
                echo "Usage: obs ai quality <vault|note_id> [--json]"
                return 1
            fi
            shift
            _log_verbose "Scoring note quality"
            # --json/--verbose are GLOBAL flags and must precede the subcommand.
            local gflags=()
            [[ "$VERBOSE" == "true" ]] && gflags+=(--verbose)
            local subargs=()
            while [[ "$1" == --* ]]; do
                case "$1" in
                    --json) gflags+=(--json); shift ;;
                    --verbose|-v) gflags+=(--verbose); shift ;;
                    *) subargs+=("$1"); shift ;;
                esac
            done
            $OBS_PYTHON "$python_cli" "${gflags[@]}" "ai" "quality" "$target" "${subargs[@]}"
            ;;

        *)
            _log "ERROR" "Unknown ai subcommand: $subcmd"
            echo "Usage: obs ai <subcommand>"
            echo ""
            echo "Subcommands:"
            echo "  status              - Show AI provider status"
            echo "  setup               - Interactive AI setup wizard"
            echo "  test                - Test all AI providers"
            echo "  test --provider X   - Test specific provider"
            echo "  similar <note_id>   - Find similar notes"
            echo "  analyze <note_id>   - Analyze note with AI"
            echo "  duplicates <vault>  - Find duplicate notes"
            echo "  suggest-links <note>- Suggest new links"
            echo "  gaps <vault>        - Find knowledge gaps"
            echo "  summarize <vault>   - Summarize vault themes"
            echo "  refactor <vault>    - AI-powered reorganization"
            echo "  merge-suggest <vault> - Find merge candidates"
            echo "  tag-suggest <target>  - Suggest tags for notes"
            echo "  quality <target>      - Score note quality"
            return 1
            ;;
    esac
}

# --- Option D Commands Removed ---
# The following commands were removed in Phase 7.1 Part 3 (CLI consolidation):
# - obs_switch() → replaced by 'obs' (default command shows vault list)
# - obs_open() → replaced by 'obs stats <vault_id>'
# - obs_manage() → functionality split into 'obs discover' and 'obs stats'
# - obs_graph() → replaced by 'obs analyze <vault_id>'

# --- Dispatch ---
obs() {
    # Parse global flags first
    while [[ "$1" == --* ]]; do
        case "$1" in
            --verbose|-v)
                VERBOSE=true
                _log_verbose "Verbose mode enabled"
                shift
                ;;
            *)
                shift
                ;;
        esac
    done

    local cmd=$1
    if [[ -n "$cmd" ]]; then
        shift
    fi

    # Default behavior (no command): Show vault list
    if [[ -z "$cmd" ]]; then
        obs_vaults
        return $?
    fi

    # Route to command handlers
    case "$cmd" in
        "help")
            [[ "$1" == "--all" ]] && obs_help true || obs_help false
            ;;
        "version")
            obs_version
            ;;
        "discover")
            obs_discover "$@"
            ;;
        "analyze")
            obs_analyze "$@"
            ;;
        "vaults")
            obs_vaults "$@"
            ;;
        "stats")
            obs_stats "$@"
            ;;
        "health")
            obs_health "$@"
            ;;
        "ai")
            obs_ai "$@"
            ;;
        *)
            _log "ERROR" "Unknown command: $cmd"
            echo ""
            obs_help false
            return 1
            ;;
    esac
}

# --- Execution Guard ---
# Execute the main function if the script is run directly.
# Check zsh_eval_context for Zsh and BASH_SOURCE for Bash.
if [[ "${zsh_eval_context[-1]}" == "toplevel" || "${BASH_SOURCE[0]}" == "${0}" ]]; then
    obs "$@"
fi
