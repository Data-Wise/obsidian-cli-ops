# Installation

## Homebrew (Recommended)

```bash
brew install data-wise/tap/obsidian-cli-ops
```

This installs `obs` with all Python dependencies and sets up the shell integration automatically.

## Manual Install

### Prerequisites

- **macOS** or **Linux**
- **Python 3.9+**: `python3 --version`
- **ZSH**: Default on macOS; available on Linux via `apt install zsh`
- **Git**: For cloning the repository

### Steps

1. **Clone the repository**:

    ```bash
    git clone https://github.com/Data-Wise/obsidian-cli-ops.git ~/projects/obsidian-cli-ops
    cd ~/projects/obsidian-cli-ops
    ```

2. **Install Python dependencies**:

    ```bash
    pip3 install -r src/python/requirements.txt
    ```

3. **Symlink the CLI function**:

    ```bash
    ln -s "$(pwd)/src/obs.zsh" ~/.config/zsh/functions/obs.zsh
    ```

    Then add to your `~/.zshrc`:

    ```zsh
    fpath=(~/.config/zsh/functions $fpath)
    autoload -Uz obs
    ```

4. **Initialize the database**:

    ```bash
    python3 src/python/obs_cli.py db init
    ```

5. **Restart your shell**:

    ```bash
    source ~/.zshrc
    ```

## Verify Installation

```bash
# Check version
obs version

# List discovered vaults
obs
```

You should see the version number and any Obsidian vaults found in your iCloud directory.

## Troubleshooting

### Python not found

If `obs` reports a Python error, ensure `/opt/homebrew/bin/python3` (macOS) or `/usr/bin/python3` (Linux) exists. You can set a custom path:

```bash
export OBS_PYTHON=/path/to/python3
```

### ZSH autoload not working

Verify the function file is in your `fpath`:

```bash
echo $fpath | tr ' ' '\n' | grep obs
```

If nothing appears, double-check the symlink path and your `~/.zshrc` configuration.

### Database initialization fails

Ensure the config directory exists:

```bash
mkdir -p ~/.config/obs
python3 src/python/obs_cli.py db init
```

---

## Next Steps

- [Configuration](configuration.md) -- AI providers, shell integration, advanced settings
- [Usage](usage.md) -- Core commands and workflows
