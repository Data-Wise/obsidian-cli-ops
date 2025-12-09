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

# --- Load Configuration ---
CONFIG_FILE="$HOME/.config/obs/config"

if [[ -f "$CONFIG_FILE" ]]; then
    source "$CONFIG_FILE"
else
    echo "\033[0;31m[ERROR]\033[0m Config file not found at $CONFIG_FILE"
    echo "Please create it with OBS_ROOT and VAULTS variables."
    return 1
fi

# Defaults
: ${PLUGIN_REGISTRY:="https://raw.githubusercontent.com/obsidianmd/obsidian-releases/master/community-plugins.json"}

# --- Helper Functions ---

_log() {
    local type=$1
    local msg=$2
    case $type in
        "INFO") echo "\033[0;34m[INFO]\033[0m $msg" ;;
        "SUCCESS") echo "\033[0;32m[OK]\033[0m $msg" ;;
        "WARN") echo "\033[0;33m[WARN]\033[0m $msg" ;;
        "ERROR") echo "\033[0;31m[ERROR]\033[0m $msg" ;;
    esac
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
    echo "Obsidian CLI Ops (obs)"
    echo "----------------------"
    echo "Usage: obs <command> [options]"
    echo ""
    echo "Commands:"
    echo "  check     Check dependencies"
    echo "  sync      Sync Core Config (Theme, Hotkeys) from Root to Sub-vaults"
    echo "  install   Install a Community Plugin"
    echo "  search    Search for a plugin ID"
    echo "  audit     Check for misplaced files in Root"
    echo ""
    echo "Config loaded from: $CONFIG_FILE"
}

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
    
    if [[ $missing -gt 0 ]]; then
        _log "WARN" "Please install missing dependencies (try 'brew install jq')."
        return 1
    fi
}

obs_audit() {
    _check_root || return 1
    _log "INFO" "Auditing Vault Structure..."
    local misplaced_count=0
    
    # Allowed items: .obsidian, Configured Vaults, Archives, Documentation
    local allowed_items=(".obsidian" "99_Archive" "README.md" "GEMINI.md" "obs.zsh.tmp" "config.tmp" "${VAULTS[@]}")
    
    for item in "$OBS_ROOT"/*; do
        local name=$(basename "$item")
        local is_allowed=false
        
        for allowed in "${allowed_items[@]}"; do
            if [[ "$name" == "$allowed" ]]; then is_allowed=true; break; fi
        done

        if ! $is_allowed; then
            _log "WARN" "Misplaced item: $name"
            ((misplaced_count++))
        fi
    done
    
    if [[ $misplaced_count -eq 0 ]]; then
        _log "SUCCESS" "Vault structure is clean."
    else
        _log "WARN" "Found $misplaced_count misplaced items."
    fi
}

obs_sync() {
    _check_root || return 1
    local dry_run=true
    if [[ "$1" == "--force" ]]; then dry_run=false; fi

    _log "INFO" "Syncing Configuration from Root..."
    if $dry_run; then echo "(DRY RUN)"; fi

    local source_dir="$OBS_ROOT/.obsidian"
    local items=("appearance.json" "hotkeys.json" "themes" "snippets")

    for vault in "${VAULTS[@]}"; do
        local target_dir="$OBS_ROOT/$vault/.obsidian"
        if [[ ! -d "$target_dir" ]]; then
            if ! $dry_run; then mkdir -p "$target_dir"; fi
        fi

        for item in "${items[@]}"; do
            local src="$source_dir/$item"
            local dest="$target_dir/$item"

            if [[ -e "$src" ]]; then
                if $dry_run; then
                    echo "  Would sync: $item -> $vault"
                else
                    rm -rf "$dest"
                    cp -R "$src" "$dest"
                    _log "SUCCESS" "Synced $item to $vault"
                fi
            fi
        done
    done
}

obs_install() {
    _check_root || return 1
    local query=$1
    local flag=$2
    local val=$3

    if [[ -z "$query" ]]; then obs_help; return 1; fi

    local repo=$(_get_plugin_url "$query")
    if [[ -z "$repo" || "$repo" == "null" ]]; then
        _log "ERROR" "Plugin not found: $query"
        return 1
    fi

    _log "INFO" "Found Plugin: $repo"

    local targets=()
    if [[ "$flag" == "--all" ]]; then
        targets=("${VAULTS[@]}")
    elif [[ "$flag" == "--vault" ]]; then
        targets=("$val")
    else
        _log "ERROR" "Usage: obs install <name> --all | --vault <name>"
        return 1
    fi

    local release_url="https://api.github.com/repos/$repo/releases/latest"
    local assets=$(curl -s "$release_url" | jq -r '.assets[] | .browser_download_url')
    
    if [[ -z "$assets" ]]; then _log "ERROR" "No assets found."; return 1; fi

    local tmp_dir=$(mktemp -d)
    _log "INFO" "Downloading..."
    
    for url in ${(f)assets}; do
        if [[ "$url" =~ (main.js|manifest.json|styles.css) ]]; then
            curl -s -L -o "$tmp_dir/$(basename $url)" "$url"
        fi
    done

    local id=$(jq -r '.id' "$tmp_dir/manifest.json")
    if [[ -z "$id" || "$id" == "null" ]]; then _log "ERROR" "Invalid manifest."; return 1; fi

    for vault in "${targets[@]}"; do
        local dest="$OBS_ROOT/$vault/.obsidian/plugins/$id"
        rm -rf "$dest"
        mkdir -p "$dest"
        cp "$tmp_dir/"* "$dest/"
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

# --- Dispatch ---
obs() {
    local cmd=$1
    shift
    case "$cmd" in
        "check") obs_check "$@" ;;
        "sync") obs_sync "$@" ;;
        "install") obs_install "$@" ;;
        "search") obs_search "$@" ;;
        "audit") obs_audit "$@" ;;
        "help"|"") obs_help ;;
        *) _log "ERROR" "Unknown command"; obs_help ;;
    esac
}
