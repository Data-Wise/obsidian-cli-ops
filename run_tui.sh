#!/bin/bash
#
# This script robustly starts the TUI application by ensuring it runs
# from the project's root directory, with the correct Python path.

# Get the directory where the script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

# Set the Python path to the src/python directory
export PYTHONPATH="$SCRIPT_DIR/src/python"

# Run the TUI application using the absolute path
python3 "$SCRIPT_DIR/src/python/tui/app.py"
