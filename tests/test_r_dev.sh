#!/bin/bash
# Test Suite for obsidian-cli-ops (R-Dev Module)

# --- Setup ---
TEST_DIR="/tmp/obs_test_$$"
MOCK_OBS_ROOT="$TEST_DIR/obs_root"
MOCK_R_PROJ="$TEST_DIR/r_project"
CONFIG_DIR="$TEST_DIR/config"
SRC_SCRIPT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../src" && pwd)/obs.zsh"

GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

setup() {
    mkdir -p "$MOCK_OBS_ROOT/Research_Lab/TestProject/06_Analysis"
    mkdir -p "$MOCK_OBS_ROOT/Research_Lab/TestProject/02_Drafts"
    mkdir -p "$MOCK_OBS_ROOT/Knowledge_Base"
    mkdir -p "$MOCK_R_PROJ"
    mkdir -p "$CONFIG_DIR"
    
    echo "The Sobel test standard error is..." > "$MOCK_OBS_ROOT/Knowledge_Base/sobel.md"
    touch "$MOCK_R_PROJ/DESCRIPTION"
    echo "dummy plot" > "$MOCK_R_PROJ/plot.png"
    mkdir -p "$MOCK_R_PROJ/vignettes"
    echo "draft content" > "$MOCK_R_PROJ/vignettes/intro.Rmd"

    echo "OBS_ROOT=\"$MOCK_OBS_ROOT\"" > "$CONFIG_DIR/config"
    echo "VAULTS=(\"Research_Lab\")" >> "$CONFIG_DIR/config"
    
    export HOME="$TEST_DIR"
    mkdir -p "$TEST_DIR/.config/obs"
    cp "$CONFIG_DIR/config" "$TEST_DIR/.config/obs/config"
    echo "{}" > "$TEST_DIR/.config/obs/project_map.json"
}

teardown() {
    rm -rf "$TEST_DIR"
}

pass() { echo -e "${GREEN}[PASS]${NC} $1"; }
fail() { echo -e "${RED}[FAIL]${NC} $1"; exit 1; }

run_obs() {
    # Helper to run the function in a fresh zsh instance
    zsh -c "source '$SRC_SCRIPT'; obs $*"
}

test_link() {
    cd "$MOCK_R_PROJ" || fail "Could not cd to mock R project"
    
    if ! output=$(run_obs r-dev link "Research_Lab/TestProject" 2>&1); then
        echo "Command failed: $output"
        fail "Link command returned error code"
    fi
    
    if grep -q "Research_Lab/TestProject" "$TEST_DIR/.config/obs/project_map.json"; then
        pass "Project linked successfully"
    else
        echo "Output: $output"
        echo "Map file:"
        cat "$TEST_DIR/.config/obs/project_map.json"
        fail "Link command failed to update mapping"
    fi
}

test_log() {
    cd "$MOCK_R_PROJ"
    
    if ! output=$(run_obs r-dev log plot.png -m "Test plot" 2>&1); then
        echo "Command failed: $output"
        fail "Log command returned error code"
    fi
    
    if ls "$MOCK_OBS_ROOT/Research_Lab/TestProject/06_Analysis/"*_plot.png 1> /dev/null 2>&1; then
        pass "File logged to 06_Analysis"
    else
        fail "Log command failed to copy file"
    fi
}

test_context() {
    output=$(run_obs r-dev context "Sobel")
    
    if [[ "$output" == *"standard error"* ]]; then
        pass "Context fetch retrieved correct content"
    else
        echo "Got: $output"
        fail "Context fetch failed"
    fi
}

test_draft() {
    cd "$MOCK_R_PROJ"
    
    if ! output=$(run_obs r-dev draft vignettes/intro.Rmd 2>&1); then
        echo "Command failed: $output"
        fail "Draft command returned error code"
    fi
    
    if [[ -f "$MOCK_OBS_ROOT/Research_Lab/TestProject/02_Drafts/intro.Rmd" ]]; then
        pass "Draft synced successfully"
    else
        fail "Draft sync failed"
    fi
}

# --- Execution ---

echo "Running Obsidian CLI Ops Tests..."
setup

test_link
test_log
test_context
test_draft

teardown
echo "All tests passed!"
