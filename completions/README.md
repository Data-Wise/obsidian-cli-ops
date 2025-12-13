# Shell Completion for obs

Tab completion for the `obs` command in Zsh and Bash.

## Zsh Installation

### Option 1: User Installation (Recommended)
```bash
# Create user completion directory if it doesn't exist
mkdir -p ~/.zsh/completions

# Copy the completion file
cp completions/_obs ~/.zsh/completions/

# Add to your ~/.zshrc (if not already present)
echo 'fpath=(~/.zsh/completions $fpath)' >> ~/.zshrc
echo 'autoload -Uz compinit && compinit' >> ~/.zshrc

# Reload your shell
source ~/.zshrc
```

### Option 2: System-wide Installation
```bash
# Copy to system completion directory (requires sudo)
sudo cp completions/_obs /usr/local/share/zsh/site-functions/

# Reload completion cache
rm -f ~/.zcompdump
exec zsh
```

## Bash Installation

### Option 1: User Installation (Recommended)
```bash
# Add to your ~/.bashrc
echo 'source /path/to/obsidian-cli-ops/completions/obs.bash' >> ~/.bashrc

# Reload your shell
source ~/.bashrc
```

### Option 2: System-wide Installation
```bash
# Copy to system completion directory (requires sudo)
sudo cp completions/obs.bash /etc/bash_completion.d/obs

# Reload your shell
source ~/.bashrc
```

## Features

The completion provides:

- **Main commands**: `check`, `list`, `sync`, `install`, `search`, `audit`, `r-dev`, `help`, `version`
- **Global flags**: `--verbose`, `-v`
- **R-Dev subcommands**: `link`, `unlink`, `status`, `log`, `context`, `draft`
- **File completion**: For `log` and `draft` commands
- **Flag completion**: For commands like `sync --force` and `install --all`

## Testing

After installation, try typing:

```bash
obs <TAB>         # Shows all main commands
obs r-dev <TAB>   # Shows r-dev subcommands
obs install <TAB> # After plugin name, shows --all and --vault
obs --<TAB>       # Shows --verbose flag
```

## Uninstallation

### Zsh
```bash
rm ~/.zsh/completions/_obs
# Or for system-wide:
sudo rm /usr/local/share/zsh/site-functions/_obs
```

### Bash
Remove the source line from `~/.bashrc` or:
```bash
sudo rm /etc/bash_completion.d/obs
```
