# Installation

## Prerequisites

*   **ZSH**: The shell environment.
*   **Homebrew**: For installing dependencies.
*   **Dependencies**: `curl`, `jq`, `unzip` (installed automatically).

## Quick Install

1.  **Clone the Repository**:
    ```bash
    git clone https://github.com/Data-Wise/obsidian-cli-ops.git ~/projects/dev-tools/obsidian-cli-ops
    ```

2.  **Run the Installer**:
    ```bash
    ~/projects/dev-tools/obsidian-cli-ops/install.sh
    ```

3.  **Load the Function**:
    Add this to your `~/.zshrc`:
    ```zsh
    autoload -Uz obs
    ```

4.  **Restart Shell**:
    ```bash
    source ~/.zshrc
    ```

5.  **Initialize Database**:
    ```bash
    python3 src/python/obs_cli.py db init
    ```

6.  **Start Using (Zero Configuration!)**:
    ```bash
    obs
    ```

    **That's it!** The tool auto-detects your iCloud Obsidian vaults at:
    ```
    ~/Library/Mobile Documents/iCloud~md~obsidian/Documents
    ```

    If no vaults are found, you can discover them:
    ```bash
    obs manage open ~/Documents
    ```

## First Run

When you type `obs` for the first time:

1. **Auto-detects iCloud location** - No configuration needed!
2. **Shows vault picker** - Select from discovered vaults
3. **Opens last vault** on subsequent runs (like Obsidian app)

**Pro Tip:** Press `d` in the TUI to discover vaults from iCloud automatically.
