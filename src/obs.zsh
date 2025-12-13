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
MAP_FILE="$HOME/.config/obs/project_map.json"

_load_config() {
    if [[ -f "$CONFIG_FILE" ]]; then
        source "$CONFIG_FILE"
    else
        echo "\033[0;31m[ERROR]\033[0m Config file not found at $CONFIG_FILE"
        echo "Please create it with OBS_ROOT and VAULTS variables."
        return 1
    fi
}

# Defaults
: ${PLUGIN_REGISTRY:="https://raw.githubusercontent.com/obsidianmd/obsidian-releases/master/community-plugins.json"}
VERBOSE=false
VERSION="2.0.0-beta"

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

_get_r_root() {
    # Climb up directories to find DESCRIPTION or .Rproj
    local d="$PWD"
    _log_verbose "Searching for R project root starting from: $PWD"
    while [[ "$d" != "/" ]]; do
        _log_verbose "Checking directory: $d"
        if [[ -f "$d/DESCRIPTION" ]] || compgen -G "$d/*.Rproj" > /dev/null; then
            _log_verbose "Found R project root: $d"
            echo "$d"
            return 0
        fi
        d=$(dirname "$d")
    done
    _log_verbose "No R project root found"
    return 1
}

_get_mapped_path() {
    # Returns the Obsidian path relative to OBS_ROOT for the current R project
    local r_root=$1
    _log_verbose "Looking up mapping for: $r_root"
    if [[ ! -f "$MAP_FILE" ]]; then
        _log_verbose "Mapping file not found: $MAP_FILE"
        echo ""
        return 1
    fi

    # Use jq to lookup the path. We assume the map keys are absolute paths to R projects
    local obs_path=$(jq -r --arg p "$r_root" '.[$p] // empty' "$MAP_FILE")
    if [[ -n "$obs_path" ]]; then
        _log_verbose "Found mapping: $r_root -> $obs_path"
    else
        _log_verbose "No mapping found for: $r_root"
    fi
    echo "$obs_path"
}

# --- Subcommands ---

obs_help() {
    echo "Obsidian CLI Ops (obs)"
    echo "----------------------"
    echo "Usage: obs [--verbose|-v] <command> [options]"
    echo ""
    echo "Global Flags:"
    echo "  --verbose, -v    Enable verbose logging"
    echo ""
    echo "Core Commands:"
    echo "  check     Check dependencies"
    echo "  list      Show configured vaults and R project mappings"
    echo "  sync      Sync Core Config (Theme, Hotkeys) from Root to Sub-vaults"
    echo "  install   Install a Community Plugin"
    echo "  search    Search for a plugin ID"
    echo "  audit     Check for misplaced files in Root"
    echo ""
    echo "R-Dev Integration (obs r-dev):"
    echo "  r-dev link <obs_folder>   Link current R project to an Obsidian folder"
    echo "  r-dev unlink              Remove current R project mapping"
    echo "  r-dev status              Show current R project link status"
    echo "  r-dev log <file> [-m msg] Copy artifact to Obsidian 06_Analysis"
    echo "  r-dev context <term>      Fetch theory notes from Knowledge_Base"
    echo "  r-dev draft <file>        Copy vignette/Rmd to Obsidian 02_Drafts"
    echo ""
    echo "Knowledge Graph (v2.0):"
    echo "  discover [path]           Discover and scan Obsidian vaults"
    echo "  analyze <vault_id>        Analyze vault graph and calculate metrics"
    echo "  vaults                    List all vaults in database"
    echo "  stats [vault_id]          Show database or vault statistics"
    echo ""
    echo "AI Integration (v2.0):"
    echo "  ai setup                  Interactive AI setup wizard"
    echo "  ai setup --quick          Quick start (auto-detect and install)"
    echo "  ai config                 Show current AI configuration"
    echo ""
    echo "Config loaded from: $CONFIG_FILE"
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

# --- R-Dev Subcommands ---

obs_r_dev() {
    local subcmd=$1
    shift

    # 1. LINK
    if [[ "$subcmd" == "link" ]]; then
        local obs_folder=$1
        local r_root=$(_get_r_root)
        if [[ -z "$r_root" ]]; then _log "ERROR" "Not inside an R Project (no DESCRIPTION/.Rproj)."; return 1; fi
        if [[ ! -d "$OBS_ROOT/$obs_folder" ]]; then _log "ERROR" "Obsidian folder not found: $OBS_ROOT/$obs_folder"; return 1; fi

        # Init map file if needed
        if [[ ! -f "$MAP_FILE" ]]; then echo "{}" > "$MAP_FILE"; fi

        # Update JSON
        local temp=$(mktemp)
        jq --arg k "$r_root" --arg v "$obs_folder" '.[$k] = $v' "$MAP_FILE" > "$temp" && mv "$temp" "$MAP_FILE"
        _log "SUCCESS" "Linked '$r_root' -> '$obs_folder'"
        return 0
    fi

    # 1b. UNLINK
    if [[ "$subcmd" == "unlink" ]]; then
        local r_root=$(_get_r_root)
        if [[ -z "$r_root" ]]; then _log "ERROR" "Not inside an R Project (no DESCRIPTION/.Rproj)."; return 1; fi

        if [[ ! -f "$MAP_FILE" ]]; then
            _log "WARN" "No mapping file exists."
            return 0
        fi

        # Check if mapping exists
        local current_mapping=$(_get_mapped_path "$r_root")
        if [[ -z "$current_mapping" ]]; then
            _log "WARN" "Project is not linked."
            return 0
        fi

        # Remove from JSON
        local temp=$(mktemp)
        jq --arg k "$r_root" 'del(.[$k])' "$MAP_FILE" > "$temp" && mv "$temp" "$MAP_FILE"
        _log "SUCCESS" "Unlinked '$r_root' from '$current_mapping'"
        return 0
    fi

    # 1c. STATUS
    if [[ "$subcmd" == "status" ]]; then
        local r_root=$(_get_r_root)
        if [[ -z "$r_root" ]]; then
            _log "ERROR" "Not inside an R Project (no DESCRIPTION/.Rproj)."
            return 1
        fi

        _log "INFO" "R Project Status"
        echo ""
        echo "R Project Root: $r_root"

        if [[ ! -f "$MAP_FILE" ]]; then
            echo "Mapping Status: ✗ Not linked (no mapping file)"
            echo ""
            echo "To link this project, run:"
            echo "  obs r-dev link <obsidian_folder>"
            return 1
        fi

        local current_mapping=$(_get_mapped_path "$r_root")
        if [[ -z "$current_mapping" ]]; then
            echo "Mapping Status: ✗ Not linked"
            echo ""
            echo "To link this project, run:"
            echo "  obs r-dev link <obsidian_folder>"
            return 1
        else
            echo "Mapping Status: ✓ Linked"
            echo "Obsidian Folder: $current_mapping"
            echo "Full Path: $OBS_ROOT/$current_mapping"

            if [[ -d "$OBS_ROOT/$current_mapping" ]]; then
                echo "Folder Exists: ✓ Yes"
            else
                echo "Folder Exists: ✗ No (will be created on first use)"
            fi
        fi
        echo ""
        return 0
    fi

    # 2. CONTEXT (Theory Fetch)
    if [[ "$subcmd" == "context" ]]; then
        local term=$1
        _log "INFO" "Searching Knowledge_Base for '$term'..."
        # Uses grep to find files, then head to show snippet. 
        # Future: Use intelligent semantic search if available.
        grep -r "$term" "$OBS_ROOT/Knowledge_Base" | head -n 5
        return 0
    fi

    # Auto-detect context for LOG and DRAFT
    local r_root=$(_get_r_root)
    if [[ -z "$r_root" ]]; then _log "ERROR" "Must be in an R Project."; return 1; fi
    local obs_rel_path=$(_get_mapped_path "$r_root")
    if [[ -z "$obs_rel_path" ]]; then _log "ERROR" "Project not linked. Run 'obs r-dev link <folder>' first."; return 1; fi
    local target_base="$OBS_ROOT/$obs_rel_path"

    # 3. LOG (Artifacts)
    if [[ "$subcmd" == "log" ]]; then
        local file=$1
        shift
        local msg="Logged artifact"
        while getopts "m:" opt; do case $opt in m) msg="$OPTARG";; esac; done

        if [[ ! -f "$file" ]]; then _log "ERROR" "File not found: $file"; return 1; fi
        
        local dest_dir="$target_base/06_Analysis"
        mkdir -p "$dest_dir"
        
        local timestamp=$(date "+%Y%m%d_%H%M%S")
        local ext="${file##*.}"
        local new_name="${timestamp}_${file}"
        
        cp "$file" "$dest_dir/$new_name"
        _log "SUCCESS" "Logged to $dest_dir/$new_name"
        # Optional: Append to a daily log md file?
        return 0
    fi

    # 4. DRAFT (Manuscripts/Vignettes)
    if [[ "$subcmd" == "draft" ]]; then
        local file=$1
        if [[ ! -f "$file" ]]; then _log "ERROR" "File not found: $file"; return 1; fi
        
        local dest_dir="$target_base/02_Drafts"
        mkdir -p "$dest_dir"
        
        cp "$file" "$dest_dir/"
        _log "SUCCESS" "Copied draft to $dest_dir/"
        return 0
    fi
    
    _log "ERROR" "Unknown r-dev command: $subcmd"
    echo "Usage: obs r-dev {link|unlink|status|log|context|draft}"
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

    python3 "${cmd[@]}"
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

    python3 "${cmd[@]}"
}

obs_vaults() {
    local python_cli=$(_get_python_cli) || return 1

    _log_verbose "Listing vaults in database"

    python3 "$python_cli" vaults
}

obs_stats() {
    local python_cli=$(_get_python_cli) || return 1
    local vault_id=$1

    _log_verbose "Showing statistics"

    if [[ -n "$vault_id" ]]; then
        python3 "$python_cli" stats --vault "$vault_id"
    else
        python3 "$python_cli" stats
    fi
}

# --- AI Commands (v2.0) ---

obs_ai() {
    local python_cli=$(_get_python_cli) || return 1
    local subcmd=$1
    shift

    case "$subcmd" in
        setup)
            _log_verbose "Running AI setup wizard"
            local cmd=("$python_cli" "ai" "setup")

            # Add --quick flag if requested
            if [[ "$1" == "--quick" ]]; then
                cmd+=(--quick)
            fi

            python3 "${cmd[@]}"
            ;;

        config)
            _log_verbose "Showing AI configuration"
            python3 "$python_cli" "ai" "config"
            ;;

        *)
            _log "ERROR" "Unknown ai subcommand: $subcmd"
            echo "Usage: obs ai <subcommand>"
            echo ""
            echo "Subcommands:"
            echo "  setup        - Interactive AI setup wizard"
            echo "  setup --quick - Quick start (auto-detect and install)"
            echo "  config        - Show current AI configuration"
            return 1
            ;;
    esac
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

    # Commands that don't need config
    case "$cmd" in
        "help"|"")
            obs_help
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
        "ai")
            obs_ai "$@"
            return $?
            ;;
    esac

    # Load config for all other commands
    _load_config || return 1

    case "$cmd" in
        "list") obs_list "$@" ;;
        "sync") obs_sync "$@" ;;
        "install") obs_install "$@" ;;
        "search") obs_search "$@" ;;
        "audit") obs_audit "$@" ;;
        "r-dev") obs_r_dev "$@" ;;
        *) _log "ERROR" "Unknown command: $cmd"; obs_help ;;
    esac
}

# --- Execution Guard ---
# Execute the main function if the script is run directly.
# Check zsh_eval_context for Zsh and BASH_SOURCE for Bash.
if [[ "${zsh_eval_context[-1]}" == "toplevel" || "${BASH_SOURCE[0]}" == "${0}" ]]; then
    obs "$@"
fi
