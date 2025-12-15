# AI Setup Quick Start

**Get AI-powered features running in 5 minutes.**

## One Command Setup

```bash
obs ai setup --quick
```

This will:
- ✅ Auto-detect your system
- ✅ Recommend the best free AI provider
- ✅ Install and configure everything
- ✅ Test to verify it works
- ✅ Save your configuration

**Time:** ~5 minutes (downloads models on first run)

## What You Get

- **Note Similarity** - Find notes with similar content
- **Duplicate Detection** - Identify potential duplicates
- **Topic Analysis** - Extract topics and themes
- **100% Free** - No API costs, no quotas
- **100% Private** - Everything runs locally

## Requirements

- **Python 3.9+** (check: `python3 --version`)
- **Internet** (for initial model download only)
- **Disk Space:**
  - Minimum: 500MB
  - Recommended: 1GB

## Providers

### HuggingFace (Recommended)

**Best for:** Most users

```bash
obs ai setup --quick  # Auto-selects HuggingFace if no Ollama
```

**Pros:**
- Pure Python, no external services
- Works everywhere
- Free forever
- Easy to install

**Model:** `all-mpnet-base-v2` (420MB, balanced)

### Ollama

**Best for:** Power users

**Install first:**
```bash
brew install ollama
ollama serve
ollama pull qwen2.5:0.5b
ollama pull nomic-embed-text
```

**Then setup:**
```bash
obs ai setup --quick  # Auto-selects Ollama if running
```

**Pros:**
- Fast processing
- Reasoning capabilities
- Flexible model choices

**Model:** `qwen2.5:0.5b` (500MB, fast)

## Usage

```bash
# View configuration
obs ai config

# Test setup (coming soon)
obs ai test

# Find similar notes (coming soon)
obs ai similar <vault_id>

# Detect duplicates (coming soon)
obs ai duplicates <vault_id>
```

## Troubleshooting

### HuggingFace

**Error:** `No module named 'sentence_transformers'`

**Fix:**
```bash
pip3 install sentence-transformers
```

### Ollama

**Error:** `Cannot connect to Ollama`

**Fix:**
```bash
ollama serve  # In a separate terminal
```

**Error:** `command not found: ollama`

**Fix:**
```bash
brew install ollama
```

## More Help

- **Full Guide:** [docs/ai-setup.md](docs_mkdocs/ai-setup.md)
- **Issues:** [GitHub Issues](https://github.com/Data-Wise/obsidian-cli-ops/issues)
- **Docs:** [https://data-wise.github.io/obsidian-cli-ops/ai-setup/](https://data-wise.github.io/obsidian-cli-ops/ai-setup/)

## FAQ

**Q: Is this really free?**
A: Yes. 100% free, no API costs, no quotas.

**Q: Does my data leave my machine?**
A: No. Everything runs locally.

**Q: Which provider should I choose?**
A: HuggingFace for most users, Ollama for power users.

**Q: Can I change my setup later?**
A: Yes. Just run `obs ai setup` again.

**Q: How much disk space?**
A: 500MB minimum, 1GB recommended.

**Q: Will this work offline?**
A: Yes, after initial setup.

## What's Next?

After setup completes, you'll be ready to use AI features as they're released:

- `obs ai similar <vault_id>` - Find similar notes
- `obs ai duplicates <vault_id>` - Detect duplicates
- `obs ai topics <vault_id>` - Analyze topics
- `obs ai suggest <vault_id>` - Get merge suggestions

Stay tuned for Phase 3!
