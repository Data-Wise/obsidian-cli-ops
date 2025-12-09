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

5.  **Check Dependencies**:
    ```bash
    obs check
    ```
