# AI Setup Guide

Complete guide to setting up AI-powered features in Obsidian CLI Ops v2.0.

## Overview

Obsidian CLI Ops v2.0 includes AI-powered features for:

- **Note Similarity Detection** - Find similar notes using semantic embeddings
- **Duplicate Detection** - Identify potential duplicate notes automatically
- **Topic Analysis** - Extract topics and themes from your vault
- **Smart Recommendations** - Get suggestions for note organization and merging

### Privacy First

All AI options are **100% free** and run **locally on your machine**. No data is sent to external servers, and there are no API costs.

## Quick Start

The fastest way to get started is with Quick Start mode:

```bash
obs ai setup --quick
```

This will:

1. ✅ Auto-detect your system capabilities
2. ✅ Recommend the best AI provider for your setup
3. ✅ Install and configure everything automatically
4. ✅ Test the installation to verify it works
5. ✅ Save your configuration

**Time:** ~5 minutes on first run (downloads models)

## Detailed Setup

For more control over your setup, use interactive mode:

```bash
obs ai setup
```

You'll be presented with two paths:

### Path 1: Quick Start (Recommended)

**Best for:**
- First-time users
- Users who want "it just works"
- Users with typical setups

**What it does:**
- Detects if Ollama is installed and running
- Detects if Python packages are already installed
- Recommends the best option based on your system
- Installs and tests automatically

**Typical recommendation:**
- If Ollama is running → Use Ollama
- If sentence-transformers installed → Use HuggingFace
- Otherwise → Install HuggingFace (most compatible)

### Path 2: Custom Setup

**Best for:**
- Tech-savvy users
- Users with specific requirements
- Users who want to choose models

**What you can customize:**
- AI provider (HuggingFace or Ollama)
- Model size and quality
- Performance vs. quality tradeoffs

## Provider Comparison

| Feature | HuggingFace ⭐ | Ollama |
|---------|---------------|--------|
| **Cost** | FREE forever | FREE forever |
| **Privacy** | 100% local | 100% local |
| **Setup** | Easy (pip install) | Medium (requires Ollama) |
| **Dependencies** | Python only | Ollama service |
| **Speed** | Medium | Fast (with small models) |
| **Quality** | Good | Good to Excellent |
| **Embeddings** | ✅ 384-1024 dim | ✅ 768 dim |
| **Reasoning** | ❌ | ✅ (with chat models) |
| **Offline** | ✅ Yes | ✅ Yes |
| **RAM Usage** | 500MB - 2GB | 500MB - 5GB |
| **Best For** | Most users | Power users |

### HuggingFace (Recommended)

**Pros:**
- Pure Python, no external services
- Works everywhere (Mac, Linux, Windows)
- Free forever (no quotas, no limits)
- Easy to install (`pip install sentence-transformers`)
- Multiple model sizes to choose from

**Cons:**
- Slower than Ollama for batch processing
- No built-in reasoning capabilities
- Models take disk space (80MB - 1.3GB)

**Model Options:**

| Model | Size | Dimension | Speed | Best For |
|-------|------|-----------|-------|----------|
| all-MiniLM-L6-v2 | 80MB | 384 | Fast | Testing, small vaults |
| all-mpnet-base-v2 ⭐ | 420MB | 768 | Medium | Production use |
| bge-large-en-v1.5 | 1.3GB | 1024 | Slow | Maximum quality |

**Recommended:** `all-mpnet-base-v2` for best balance

### Ollama

**Pros:**
- Fast embedding generation
- Includes reasoning capabilities (chat models)
- Can use very small models (qwen2.5:0.5b = 500MB)
- Active development and community
- Can run models locally without Python

**Cons:**
- Requires Ollama installation
- Requires background service running
- Slightly more complex setup

**Installation Options:**

```bash
# Option 1: Homebrew CLI (recommended)
brew install ollama

# Option 2: Homebrew Cask (GUI app)
brew install --cask ollama-app

# Option 3: Official installer
# Download from: https://ollama.com/download
```

**After installation:**

```bash
# Start Ollama service
ollama serve

# Pull recommended models (in another terminal)
ollama pull qwen2.5:0.5b        # Chat model (500MB, fast)
ollama pull nomic-embed-text    # Embedding model (768-dim)
```

**Model Options:**

| Model | Size | Speed | Quality | Best For |
|-------|------|-------|---------|----------|
| qwen2.5:0.5b ⭐ | 500MB | Fast | Good | Most users |
| llama3.1 | 4GB | Slow | Excellent | Maximum quality |
| mistral | 4GB | Medium | Excellent | Balance |

**Recommended:** `qwen2.5:0.5b` for speed, `llama3.1` for quality

## Performance Benchmarks

Based on testing with a 100-note vault:

### HuggingFace Performance

| Model | Embedding Time | Comparison Time | RAM Usage |
|-------|---------------|-----------------|-----------|
| all-MiniLM-L6-v2 | ~1-2 min | ~0.5 sec/pair | ~500MB |
| all-mpnet-base-v2 | ~2-3 min | ~0.8 sec/pair | ~800MB |
| bge-large-en-v1.5 | ~4-6 min | ~1.2 sec/pair | ~1.5GB |

### Ollama Performance

| Model | Embedding Time | Comparison Time | RAM Usage |
|-------|---------------|-----------------|-----------|
| qwen2.5:0.5b | ~1-2 min | ~2-3 sec/pair | ~1GB |
| llama3.1 | ~6-8 min | ~8-10 sec/pair | ~5GB |

**Notes:**
- First run is slower (downloads models)
- Subsequent runs use cached models
- Times are for M1/M2 Macs (adjust for your hardware)
- Batch processing is faster than individual comparisons

## Configuration

After setup, your configuration is saved to:

```
~/.config/obs/ai_config.json
```

**Example configuration:**

```json
{
  "version": "2.0.0",
  "setup_completed": true,
  "setup_date": "2025-12-12 10:30:00",
  "provider": {
    "primary": "huggingface",
    "config": {
      "model_name": "all-mpnet-base-v2"
    }
  },
  "system_info": {
    "os": "Darwin",
    "python_version": "3.9.6",
    "ram_gb": 16
  }
}
```

### View Current Configuration

```bash
obs ai config
```

### Change Configuration

To change your setup, simply run the wizard again:

```bash
obs ai setup
```

This will detect your previous configuration and allow you to change it.

## Usage Examples

Once setup is complete, you can use AI features:

```bash
# Test your setup
obs ai test

# Find similar notes (coming soon)
obs ai similar <vault_id>

# Detect duplicates (coming soon)
obs ai duplicates <vault_id>

# Analyze topics (coming soon)
obs ai topics <vault_id>
```

## Troubleshooting

### HuggingFace Issues

**Problem:** `ImportError: No module named 'sentence_transformers'`

**Solution:**
```bash
pip install sentence-transformers
# or
pip3 install sentence-transformers
```

**Problem:** `OSError: [Errno 28] No space left on device`

**Solution:**
Models take disk space. Free up space or use a smaller model:
- all-MiniLM-L6-v2 (80MB) instead of bge-large-en-v1.5 (1.3GB)

**Problem:** `RuntimeError: Failed to load model`

**Solution:**
Clear cache and retry:
```bash
rm -rf ~/.cache/huggingface/
obs ai setup
```

**Problem:** Slow performance on older Mac

**Solution:**
Use the smallest model:
```bash
# During Custom Setup, choose:
# Model: all-MiniLM-L6-v2
```

### Ollama Issues

**Problem:** `ConnectionError: Cannot connect to Ollama`

**Solution:**
Start Ollama service:
```bash
ollama serve
```

**Problem:** `ollama: command not found`

**Solution:**
Install Ollama:
```bash
brew install ollama
```

**Problem:** Model download fails

**Solution:**
Check internet connection and retry:
```bash
ollama pull qwen2.5:0.5b
ollama pull nomic-embed-text
```

**Problem:** Ollama service won't start

**Solution:**
Check if port 11434 is in use:
```bash
lsof -i :11434
# If another process is using it, kill it:
kill -9 <PID>
# Then retry:
ollama serve
```

**Problem:** High RAM usage with llama3.1

**Solution:**
Use smaller model:
```bash
ollama pull qwen2.5:0.5b
# Then re-run setup and choose qwen2.5:0.5b
```

### General Issues

**Problem:** `rich` library installation fails

**Solution:**
The setup wizard auto-installs `rich`, but if it fails:
```bash
pip install rich
# or
pip3 install rich
```

**Problem:** Python 3.8 or older

**Solution:**
Upgrade Python:
```bash
brew install python@3.9
```

**Problem:** Setup wizard freezes

**Solution:**
1. Press Ctrl+C to cancel
2. Check internet connection
3. Retry with `--quick` flag:
```bash
obs ai setup --quick
```

**Problem:** "Permission denied" errors

**Solution:**
Install to user directory:
```bash
pip install --user sentence-transformers
```

## System Requirements

### Minimum Requirements

- **OS:** macOS 10.15+, Linux (most distros), Windows 10+
- **Python:** 3.9 or higher
- **RAM:** 4GB (8GB recommended)
- **Disk:** 500MB - 2GB (depending on models)
- **Internet:** Required for initial model download only

### Recommended Requirements

- **OS:** macOS 12+ (M1/M2 Macs for best performance)
- **Python:** 3.10+
- **RAM:** 8GB or more
- **Disk:** 2GB free space
- **CPU:** Apple Silicon or modern Intel/AMD

## Frequently Asked Questions

### Is this really free?

**Yes.** Both HuggingFace and Ollama are 100% free and open source. There are no API costs, no quotas, and no hidden fees.

### Does my data leave my machine?

**No.** Everything runs locally on your computer. Your notes never leave your machine.

### Can I use both providers?

**Not yet.** Currently, you choose one provider during setup. Multi-provider support is planned for a future release.

### Which provider should I choose?

**For most users:** HuggingFace with `all-mpnet-base-v2` model
- Easy setup
- Good performance
- Free forever
- Works everywhere

**For power users:** Ollama with `qwen2.5:0.5b` model
- Faster processing
- Reasoning capabilities
- More flexibility

### Can I change my setup later?

**Yes.** Just run `obs ai setup` again. Your previous configuration will be detected, and you can choose a new provider or model.

### How much disk space do I need?

**HuggingFace:**
- Minimum: 80MB (all-MiniLM-L6-v2)
- Recommended: 420MB (all-mpnet-base-v2)
- Maximum: 1.3GB (bge-large-en-v1.5)

**Ollama:**
- Minimum: 500MB (qwen2.5:0.5b) + 274MB (nomic-embed-text)
- Recommended: Same as minimum
- Maximum: 4GB (llama3.1) + 274MB (nomic-embed-text)

### Will this work offline?

**Yes.** After initial setup and model download, everything works offline.

### Can I use my own models?

**Not yet.** Custom model support is planned for a future release.

### What if I have a slow internet connection?

**Use Quick Start with HuggingFace.** The default model (all-mpnet-base-v2) is only 420MB. If your connection is very slow, you can:

1. Use Custom Setup
2. Choose HuggingFace
3. Select all-MiniLM-L6-v2 (only 80MB)

### How do I uninstall?

**HuggingFace:**
```bash
pip uninstall sentence-transformers
rm -rf ~/.cache/huggingface/
rm ~/.config/obs/ai_config.json
```

**Ollama:**
```bash
brew uninstall ollama
# or
brew uninstall --cask ollama-app
rm ~/.config/obs/ai_config.json
```

## Advanced Configuration

### Environment Variables

You can override default settings with environment variables:

```bash
# Change config directory
export OBS_AI_CONFIG_DIR="$HOME/.my-config"

# Use specific Python
export PYTHON_BIN="/usr/local/bin/python3.11"
```

### Manual Configuration

You can manually edit the config file:

```bash
# Edit config
vim ~/.config/obs/ai_config.json

# Test configuration
obs ai config
```

### Python API

You can also use the AI clients directly in Python:

```python
from ai_client import get_ai_client

# Get HuggingFace client
client = get_ai_client("huggingface", model_name="all-mpnet-base-v2")

# Get embedding
embedding = client.get_embedding("My note content")

# Compare notes
score = client.compare_notes("Note 1 content", "Note 2 content")
print(f"Similarity: {score.score:.2f}")
```

### Ollama API

Direct Ollama API usage:

```python
from ai_client import get_ai_client

# Get Ollama client
client = get_ai_client("ollama",
                      embedding_model="nomic-embed-text",
                      chat_model="qwen2.5:0.5b")

# Compare with reasoning
score = client.compare_notes(
    "Statistical mediation analysis",
    "Causal mediation methods",
    use_reasoning=True  # Use chat model for better comparison
)
print(f"Similarity: {score.score:.2f}")
print(f"Reason: {score.reason}")
```

## What's Next?

After setup, you'll be able to use these upcoming features:

- `obs ai similar <vault_id>` - Find similar notes
- `obs ai duplicates <vault_id>` - Detect duplicates
- `obs ai topics <vault_id>` - Analyze topics
- `obs ai suggest <vault_id>` - Get merge suggestions
- `obs ai analyze <note_id>` - Analyze single note

Stay tuned for Phase 2 feature implementation!

## Support

### Get Help

- **Documentation:** [https://data-wise.github.io/obsidian-cli-ops/](https://data-wise.github.io/obsidian-cli-ops/)
- **GitHub Issues:** [https://github.com/Data-Wise/obsidian-cli-ops/issues](https://github.com/Data-Wise/obsidian-cli-ops/issues)
- **Discussions:** [https://github.com/Data-Wise/obsidian-cli-ops/discussions](https://github.com/Data-Wise/obsidian-cli-ops/discussions)

### Contributing

Found a bug or have a suggestion? Please open an issue on GitHub!

## Credits

**AI Providers:**
- [HuggingFace sentence-transformers](https://www.sbert.net/)
- [Ollama](https://ollama.com/)

**Models:**
- [all-mpnet-base-v2](https://huggingface.co/sentence-transformers/all-mpnet-base-v2)
- [all-MiniLM-L6-v2](https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2)
- [bge-large-en-v1.5](https://huggingface.co/BAAI/bge-large-en-v1.5)
- [qwen2.5](https://ollama.com/library/qwen2.5)
- [nomic-embed-text](https://ollama.com/library/nomic-embed-text)
