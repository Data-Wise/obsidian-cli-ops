# Configuration

`obs` works out of the box with sensible defaults. This page covers optional configuration for advanced setups.

## Database Location

The SQLite database is stored at:

```
~/.config/obs/vault_db.sqlite
```

To reinitialize:

```bash
python3 src/python/obs_cli.py db init
```

## AI Provider Configuration

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

## Shell Integration

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

---

## Next Steps

- [AI Setup Guide](ai-setup.md) -- Detailed provider configuration
- [Usage](usage.md) -- Core commands and workflows
