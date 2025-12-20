#!/bin/zsh
#
# Obsidian Vault Manager (obs)
# ============================
# A system command to manage a Federated Obsidian System.
#
# Author: Gemini CLI Agent
# Project: obsidian-cli-ops
#
# DEPENDENCIES:
# - curl
# - jq
# - unzip
#
# CONFIGURATION:
# Creates/Reads config from ~/.config/obs/config
# Reads Project Mapping from ~/.config/obs/project_map.json

# --- Load Configuration ---
CONFIG_FILE="$HOME/.config/obs/config"
# MAP_FILE removed (R-Dev integration removed in v3.0.0)
LAST_VAULT_FILE="$HOME/.config/obs/last_vault"

# iCloud Obsidian location (default root - Option D)
ICLOUD_OBSIDIAN="$HOME/Library/Mobile Documents/iCloud~md~obsidian/Documents"

_load_config() {
    # Create config dir if it doesn't exist
    mkdir -p "$HOME/.config/obs"

    if [[ -f "$CONFIG_FILE" ]]; then
        source "$CONFIG_FILE"
    fi

    # Set default OBS_ROOT to iCloud if not configured (Option D)
    if [[ -z "$OBS_ROOT" ]]; then
        if [[ -d "$ICLOUD_OBSIDIAN" ]]; then
            OBS_ROOT="$ICLOUD_OBSIDIAN"
            _log_verbose "Using iCloud Obsidian: $OBS_ROOT"
        fi
    fi
}

_save_last_vault() {
    local vault_id=$1
    echo "$vault_id" > "$LAST_VAULT_FILE"
    _log_verbose "Saved last vault: $vault_id"
}

_get_last_vault() {
    if [[ -f "$LAST_VAULT_FILE" ]]; then
        cat "$LAST_VAULT_FILE"
    fi
}

# Defaults
: ${PLUGIN_REGISTRY:="https://raw.githubusercontent.com/obsidianmd/obsidian-releases/master/community-plugins.json"}
VERBOSE=false
VERSION="2.2.0"

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

_check_root() {
    if [[ ! -d "$OBS_ROOT" ]]; then
        _log "ERROR" "Obsidian Root not found at: $OBS_ROOT"
        return 1
    fi
}

_get_plugin_url() {
    local query=$1
    local cache_file="/tmp/obsidian_plugins.json"

    if [[ ! -f "$cache_file" ]] || [[ $(find "$cache_file" -mtime +1 2>/dev/null) ]]; then
        _log "INFO" "Updating Plugin Registry..."
        curl -s "$PLUGIN_REGISTRY" > "$cache_file"
    fi

    local repo=$(jq -r --arg q "$query" '.[] | select(.id == $q) | .repo' "$cache_file")
    
    if [[ -z "$repo" || "$repo" == "null" ]]; then
        repo=$(jq -r --arg q "$query" '.[] | select(.name | ascii_downcase | contains($q | ascii_downcase)) | .repo' "$cache_file" | head -n 1)
    fi

    echo "$repo"
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
        echo "🎯 PRIMARY COMMANDS (Start Here)"
    else
        echo "🎯 QUICK START"
    fi

    echo "  obs                       Open last vault (or show vault picker)"
    echo "  obs switch [name]         Switch vaults (Obsidian-style vault picker)"
    echo "  obs manage                Manage vaults (create/open/remove/rename)"
    echo ""

    if [[ "$show_all" == "true" ]]; then
        echo "⚡ QUICK ACTIONS"
        echo "  obs open <name>           Open specific vault"
        echo "  obs graph [vault]         Show graph visualization"
        echo "  obs stats [vault]         Show statistics"
        echo "  obs search <query>        Search across all vaults"
        echo ""

        echo "🛠️  VAULT MANAGEMENT"
        echo "  obs manage create         Create new vault"
        echo "  obs manage open <path>    Open folder as vault"
        echo "  obs manage remove <name>  Remove vault from database"
        echo "  obs manage rename         Rename vault"
        echo "  obs manage info <name>    Show vault details"
        echo ""

        echo "🤖 AI FEATURES"
        echo "  obs ai status             Show AI provider status"
        echo "  obs ai setup              Interactive AI setup wizard"
        echo "  obs ai test               Test all AI providers"
        echo ""

        echo "📦 R INTEGRATION"
        echo "  obs r link                Link R project to vault folder"
        echo "  obs r unlink              Remove R project mapping"
        echo "  obs r status              Show R project link status"
        echo "  obs r log <file>          Copy artifact to vault"
        echo "  obs r context <term>      Search theory notes"
        echo "  obs r draft <file>        Copy draft to vault"
        echo ""

        echo "🔧 UTILITIES"
        echo "  obs sync [vault]          Sync vault settings"
        echo "  obs install <plugin>      Install community plugin"
        echo "  obs check                 Check dependencies"
        echo "  obs version               Show version"
        echo "  obs help --all            Show all commands"
        echo ""

        echo "📍 DEFAULT ROOT: $ICLOUD_OBSIDIAN"
        echo "📝 CONFIG: $CONFIG_FILE"
    else
        echo "💡 TIP: Just type 'obs' to get started!"
        echo ""
        echo "More commands: obs help --all"
    fi
    echo ""
}

obs_version() {
    echo "obs (Obsidian CLI Ops) version $VERSION"
    echo ""
    echo "A command-line tool for managing federated Obsidian vaults"
    echo "with R development integration."
    echo ""
    echo "Repository: https://github.com/Data-Wise/obsidian-cli-ops"
    echo "Documentation: https://data-wise.github.io/obsidian-cli-ops/"
}

# ... [Previous commands: check, audit, sync, install, search remain unchanged] ...
obs_check() {
    _log "INFO" "Checking dependencies..."
    local missing=0
    for dep in curl jq unzip; do
        if ! command -v $dep &> /dev/null; then
            _log "ERROR" "$dep is missing."
            ((missing++))
        else
            _log "SUCCESS" "$dep is installed."
        fi
    done
    if [[ $missing -gt 0 ]]; then _log "WARN" "Install missing deps (brew install jq)"; return 1; fi
}

obs_audit() {
    _check_root || return 1
    _log "INFO" "Auditing Vault Structure..."
    local misplaced_count=0
    local allowed_items=(".obsidian" "99_Archive" "README.md" "GEMINI.md" "obs.zsh.tmp" "config.tmp" "${VAULTS[@]}")
    for item in "$OBS_ROOT"/*; do
        local name=$(basename "$item")
        local is_allowed=false
        for allowed in "${allowed_items[@]}"; do
            if [[ "$name" == "$allowed" ]]; then is_allowed=true; break; fi
        done
        if ! $is_allowed; then _log "WARN" "Misplaced: $name"; ((misplaced_count++)); fi
    done
    if [[ $misplaced_count -eq 0 ]]; then _log "SUCCESS" "Vault structure clean."; else _log "WARN" "Found $misplaced_count misplaced items."; fi
}

obs_sync() {
    _check_root || return 1
    local dry_run=true
    if [[ "$1" == "--force" ]]; then dry_run=false; fi
    _log "INFO" "Syncing Configuration..."
    local source_dir="$OBS_ROOT/.obsidian"
    local items=("appearance.json" "hotkeys.json" "themes" "snippets")
    for vault in "${VAULTS[@]}"; do
        local target_dir="$OBS_ROOT/$vault/.obsidian"
        if [[ ! -d "$target_dir" ]]; then if ! $dry_run; then mkdir -p "$target_dir"; fi; fi
        for item in "${items[@]}"; do
            local src="$source_dir/$item"
            local dest="$target_dir/$item"
            if [[ -e "$src" ]]; then
                if $dry_run; then echo "  Would sync: $item -> $vault"; else rm -rf "$dest"; cp -R "$src" "$dest"; _log "SUCCESS" "Synced $item to $vault"; fi
            fi
        done
    done
}

obs_install() {
    _check_root || return 1
    local query=$1; local flag=$2; local val=$3
    if [[ -z "$query" ]]; then obs_help; return 1; fi
    local repo=$(_get_plugin_url "$query")
    if [[ -z "$repo" || "$repo" == "null" ]]; then _log "ERROR" "Plugin not found: $query"; return 1; fi
    _log "INFO" "Found Plugin: $repo"
    local targets=()
    if [[ "$flag" == "--all" ]]; then targets=("${VAULTS[@]}"); elif [[ "$flag" == "--vault" ]]; then targets=("$val"); else _log "ERROR" "Usage: obs install <name> --all | --vault <name>"; return 1; fi
    local release_url="https://api.github.com/repos/$repo/releases/latest"
    local assets=$(curl -s "$release_url" | jq -r '.assets[] | .browser_download_url')
    if [[ -z "$assets" ]]; then _log "ERROR" "No assets found."; return 1; fi
    local tmp_dir=$(mktemp -d); _log "INFO" "Downloading..."
    for url in ${(f)assets}; do if [[ "$url" =~ (main.js|manifest.json|styles.css) ]]; then curl -s -L -o "$tmp_dir/$(basename $url)" "$url"; fi; done
    local id=$(jq -r '.id' "$tmp_dir/manifest.json")
    if [[ -z "$id" || "$id" == "null" ]]; then _log "ERROR" "Invalid manifest."; return 1; fi
    for vault in "${targets[@]}"; do
        local dest="$OBS_ROOT/$vault/.obsidian/plugins/$id"
        rm -rf "$dest"; mkdir -p "$dest"; cp "$tmp_dir/"* "$dest/"
        _log "SUCCESS" "Installed $id to $vault"
    done
    rm -rf "$tmp_dir"
}

obs_search() {
    local query=$1
    local cache_file="/tmp/obsidian_plugins.json"
    if [[ ! -f "$cache_file" ]]; then curl -s "$PLUGIN_REGISTRY" > "$cache_file"; fi
    jq -r --arg q "$query" '.[] | select(.name | ascii_downcase | contains($q | ascii_downcase)) | "\(.name) (ID: \(.id))"' "$cache_file" | head -n 10
}

obs_list() {
    _check_root || return 1
    _log "INFO" "Configured Vaults"
    echo ""
    echo "Root: $OBS_ROOT"
    echo ""
    echo "Sub-vaults:"
    for vault in "${VAULTS[@]}"; do
        local vault_path="$OBS_ROOT/$vault"
        if [[ -d "$vault_path" ]]; then
            echo "  ✓ $vault"
        else
            echo "  ✗ $vault (missing)"
        fi
    done
    echo ""
    if [[ -f "$MAP_FILE" ]]; then
        local count=$(jq 'length' "$MAP_FILE")
        _log "INFO" "R Project Mappings: $count"
        if [[ $count -gt 0 ]]; then
            echo ""
            jq -r 'to_entries[] | "  \(.key | split("/") | .[-1]) → \(.value)"' "$MAP_FILE"
        fi
    else
        _log "INFO" "R Project Mappings: 0 (no mapping file)"
    fi
}

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

    /opt/homebrew/bin/python3 "${cmd[@]}"
}

obs_analyze() {
    local python_cli=$(_get_python_cli) || return 1
    local vault_id=$1

    if [[ -z "$vault_id" ]]; then
        _log "ERROR" "Vault ID required"
        echo "Usage: obs analyze <vault_id>"
        echo ""
        echo "Get vault IDs with: obs vaults"
        return 1
    fi

    _log_verbose "Analyzing vault: $vault_id"

    # Build command
    local cmd=("$python_cli" "analyze" "$vault_id")

    # Add verbose flag if enabled
    if [[ "$VERBOSE" == "true" ]]; then
        cmd+=(--verbose)
    fi

    /opt/homebrew/bin/python3 "${cmd[@]}"
}

obs_vaults() {
    local python_cli=$(_get_python_cli) || return 1

    _log_verbose "Listing vaults in database"

    /opt/homebrew/bin/python3 "$python_cli" vaults
}

obs_stats() {
    local python_cli=$(_get_python_cli) || return 1
    local vault_id=$1

    _log_verbose "Showing statistics"

    if [[ -n "$vault_id" ]]; then
        /opt/homebrew/bin/python3 "$python_cli" stats --vault "$vault_id"
    else
        /opt/homebrew/bin/python3 "$python_cli" stats
    fi
}

# --- AI Commands (v2.0) ---

obs_ai() {
    local python_cli=$(_get_python_cli) || return 1
    local subcmd=$1
    shift

    case "$subcmd" in
        status)
            _log_verbose "Showing AI provider status"
            /opt/homebrew/bin/python3 "$python_cli" "ai" "status"
            ;;

        setup)
            _log_verbose "Running AI setup wizard"
            /opt/homebrew/bin/python3 "$python_cli" "ai" "setup"
            ;;

        test)
            _log_verbose "Testing AI providers"
            local cmd=("$python_cli" "ai" "test")

            # Add --provider flag if specified
            if [[ "$1" == "--provider" ]]; then
                cmd+=(--provider "$2")
            fi

            /opt/homebrew/bin/python3 "${cmd[@]}"
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
            return 1
            ;;
    esac
}

# --- Option D Commands ---
# NOTE: These commands currently call TUI which has been removed.
# They will be reimplemented for CLI-only operation in Phase 7.1.3 (CLI consolidation).
# For now, they will fail with "unknown command: tui" error.

obs_switch() {
    # Vault switcher (like Obsidian's "Open another vault")
    local vault_name=$1
    local python_cli=$(_get_python_cli) || return 1

    if [[ -n "$vault_name" ]]; then
        # Direct switch to named vault
        _log "INFO" "Switching to vault: $vault_name"
        /opt/homebrew/bin/python3 "$python_cli" tui --vault-name "$vault_name"
        _save_last_vault "$vault_name"
    else
        # Show vault picker
        _log_verbose "Opening vault switcher"
        /opt/homebrew/bin/python3 "$python_cli" tui --screen vaults
    fi
}

obs_open() {
    # Open specific vault (like "Open" in Obsidian)
    local vault_name=$1
    local python_cli=$(_get_python_cli) || return 1

    if [[ -z "$vault_name" ]]; then
        _log "ERROR" "Vault name required"
        echo "Usage: obs open <vault_name>"
        echo ""
        echo "Get vault names with: obs switch"
        return 1
    fi

    _log_verbose "Opening vault: $vault_name"
    /opt/homebrew/bin/python3 "$python_cli" tui --vault-name "$vault_name"
    _save_last_vault "$vault_name"
}

obs_manage() {
    # Manage vaults (like Obsidian's "Manage Vaults" menu)
    local subcmd=$1
    shift
    local python_cli=$(_get_python_cli) || return 1

    case "$subcmd" in
        create)
            _log "INFO" "Creating new vault..."
            # Future: Interactive vault creation
            _log "ERROR" "Not yet implemented. Use: obs discover <path> --scan"
            return 1
            ;;

        open)
            local path=$1
            if [[ -z "$path" ]]; then
                _log "ERROR" "Path required"
                echo "Usage: obs manage open <path>"
                return 1
            fi
            _log "INFO" "Opening folder as vault: $path"
            /opt/homebrew/bin/python3 "$python_cli" discover "$path" --scan
            ;;

        remove)
            local vault_id=$1
            if [[ -z "$vault_id" ]]; then
                _log "ERROR" "Vault ID required"
                echo "Usage: obs manage remove <vault_id>"
                return 1
            fi
            _log "INFO" "Removing vault: $vault_id"
            # Future: Implement vault removal in Python CLI
            _log "ERROR" "Not yet implemented"
            return 1
            ;;

        rename)
            _log "ERROR" "Not yet implemented"
            return 1
            ;;

        info)
            local vault_id=$1
            if [[ -z "$vault_id" ]]; then
                _log "ERROR" "Vault ID required"
                echo "Usage: obs manage info <vault_id>"
                return 1
            fi
            /opt/homebrew/bin/python3 "$python_cli" stats --vault "$vault_id"
            ;;

        ""|help)
            echo "Manage Vaults"
            echo "━━━━━━━━━━━━━"
            echo ""
            echo "Usage: obs manage <subcommand>"
            echo ""
            echo "Subcommands:"
            echo "  create              Create new vault"
            echo "  open <path>         Open folder as vault"
            echo "  remove <vault_id>   Remove vault from database"
            echo "  rename              Rename vault"
            echo "  info <vault_id>     Show vault details"
            echo ""
            ;;

        *)
            _log "ERROR" "Unknown manage subcommand: $subcmd"
            echo "Run 'obs manage' for help"
            return 1
            ;;
    esac
}

obs_graph() {
    # Show graph visualization
    local vault_id=$1
    local python_cli=$(_get_python_cli) || return 1

    if [[ -n "$vault_id" ]]; then
        # Specific vault
        /opt/homebrew/bin/python3 "$python_cli" tui --vault-id "$vault_id" --screen graph
    else
        # Current vault or prompt
        _log_verbose "Opening graph view"
        /opt/homebrew/bin/python3 "$python_cli" tui --screen graph
    fi
}

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

    # Load config first for iCloud detection
    _load_config

    # OPTION D: Default behavior (no command)
    if [[ -z "$cmd" ]]; then
        local last_vault=$(_get_last_vault)
        local python_cli=$(_get_python_cli) || return 1

        if [[ -n "$last_vault" ]]; then
            # Open last-used vault (like Obsidian app)
            _log_verbose "Opening last vault: $last_vault"
            /opt/homebrew/bin/python3 "$python_cli" tui --vault-id "$last_vault"
        else
            # Show vault picker (like first launch)
            _log_verbose "No last vault, showing vault picker"
            /opt/homebrew/bin/python3 "$python_cli" tui --screen vaults
        fi
        return $?
    fi

    # Commands that don't need extra processing
    case "$cmd" in
        "help")
            if [[ "$1" == "--all" ]]; then
                obs_help true
            else
                obs_help false
            fi
            return 0
            ;;
        "version")
            obs_version
            return 0
            ;;
        "check")
            obs_check "$@"
            return $?
            ;;

        # Option D: New primary commands
        "switch")
            obs_switch "$@"
            return $?
            ;;
        "manage")
            obs_manage "$@"
            return $?
            ;;
        "open")
            obs_open "$@"
            return $?
            ;;
        "graph")
            obs_graph "$@"
            return $?
            ;;

        # V2.0 commands (kept for compatibility)
        "discover")
            obs_discover "$@"
            return $?
            ;;
        "analyze")
            obs_analyze "$@"
            return $?
            ;;
        "vaults")
            obs_vaults "$@"
            return $?
            ;;
        "stats")
            obs_stats "$@"
            return $?
            ;;

        # AI commands
        "ai")
            obs_ai "$@"
            return $?
            ;;

        # V1.x commands (require OBS_ROOT config)
        "list"|"sync"|"install"|"search"|"audit")
            if [[ -z "$OBS_ROOT" ]]; then
                _log "ERROR" "OBS_ROOT not configured"
                echo "This command requires v1.x configuration."
                echo "See: obs help --all"
                return 1
            fi

            case "$cmd" in
                "list") obs_list "$@" ;;
                "sync") obs_sync "$@" ;;
                "install") obs_install "$@" ;;
                "search") obs_search "$@" ;;
                "audit") obs_audit "$@" ;;
            esac
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
