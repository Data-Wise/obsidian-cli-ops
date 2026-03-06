# Configuration

> **TL;DR** (30 seconds)
> - **What:** Optional settings for database, AI providers, and shell integration
> - **Why:** `obs` works out of the box — configure only what you need
> - **How:** iCloud auto-detected; set `OBS_ROOT` to override vault location
> - **Next:** [AI Setup Guide](ai-setup.md) for AI provider configuration

**Time:** ~3 minutes | **Level:** Beginner | **Steps:** 3 sections

---

## :floppy_disk: Database Location

The SQLite database is stored at:

```
~/.config/obs/vault_db.sqlite
```

To reinitialize:

```bash
python3 src/python/obs_cli.py db init
```

## :robot: AI Provider Configuration

`obs` supports multiple AI providers with automatic fallback routing:

| Priority | Provider | Type | Setup |
|----------|----------|------|-------|
| 1 | Gemini API | Cloud | `GEMINI_API_KEY` env var |
| 2 | Anthropic API | Cloud | `ANTHROPIC_API_KEY` env var |
| 3 | Ollama | Local | Install [Ollama](https://ollama.com), pull a model |
| 4 | Gemini CLI | Local | Install `gemini` CLI tool |
| 5 | Claude CLI | Local | Install `claude` CLI tool |

### Setting API Keys

```bash
# Add to ~/.zshrc or ~/.zshenv
export GEMINI_API_KEY="your-key-here"
export ANTHROPIC_API_KEY="your-key-here"
```

### Using Ollama (100% Local, Private)

```bash
# Install Ollama
brew install ollama

# Pull a model
ollama pull llama3.2

# Verify
obs ai status
```

### Check Provider Status

```bash
# See which providers are available
obs ai status

# Interactive setup wizard
obs ai setup

# Test all configured providers
obs ai test
```

## :shell: Shell Integration

### Verbose Mode

Add `--verbose` to any command for detailed output:

```bash
obs analyze Knowledge_Base --verbose
```

### Custom Python Path

If your Python installation is in a non-standard location:

```bash
export OBS_PYTHON=/path/to/python3
```

### iCloud Vault Auto-Detection

`obs` automatically checks the standard Obsidian iCloud path:

```
~/Library/Mobile Documents/iCloud~md~obsidian/Documents
```

To discover vaults elsewhere:

```bash
obs discover ~/Documents --scan
```

## :mag: Config Lookup Order

```mermaid
graph TD
    A[obs starts] --> B{OBS_ROOT set?}
    B -->|Yes| C[Use OBS_ROOT path]
    B -->|No| D{iCloud path exists?}
    D -->|Yes| E[Use iCloud auto-detect]
    D -->|No| F[Use ~/.config/obs/ default]
    style C fill:#6366f1,color:#fff
    style E fill:#22c55e,color:#fff
    style F fill:#f59e0b,color:#000
```

---

## Next Steps

- [AI Setup Guide](ai-setup.md) -- Detailed provider configuration
- [Usage](usage.md) -- Core commands and workflows
