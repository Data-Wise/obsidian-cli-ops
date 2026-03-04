# AI Provider Architecture

## Overview

Obsidian CLI Ops uses a multi-provider AI architecture with automatic fallback routing. All providers implement a common interface and return shared dataclass types.

```
┌──────────────────────────────────────────────────┐
│                  AI Router                        │
│  Priority: gemini-api > anthropic-api > ollama    │
│            > gemini-cli > claude-cli              │
├──────────────────────────────────────────────────┤
│  ┌──────────┐  ┌───────────┐  ┌──────────┐      │
│  │Gemini API│  │Anthropic  │  │  Ollama  │      │
│  │(default) │  │API        │  │ (local)  │      │
│  └──────────┘  └───────────┘  └──────────┘      │
│  ┌──────────┐  ┌───────────┐                     │
│  │Gemini CLI│  │Claude CLI │                     │
│  └──────────┘  └───────────┘                     │
└──────────────────────────────────────────────────┘
         │                │
         ▼                ▼
  ┌─────────────┐  ┌─────────────────┐
  │ models.py   │  │ obsidian_bridge  │
  │ Dataclasses │  │ (data source)    │
  └─────────────┘  └─────────────────┘
```

## Available Providers

| Provider | Type | Embeddings | Batch | Analysis | Cost | Requirements |
|----------|------|------------|-------|----------|------|-------------|
| `gemini-api` | API | Yes | Yes | Yes | Free tier | `GOOGLE_API_KEY` + `google-genai` |
| `anthropic-api` | API | No | No | Yes | Paid | `ANTHROPIC_API_KEY` + `anthropic` |
| `ollama` | Local | Yes | No | Yes | Free | Ollama running locally |
| `gemini-cli` | CLI | No | No | Yes | Subscription | Gemini CLI installed |
| `claude-cli` | CLI | No | No | Yes | Subscription | Claude CLI installed |

## Structured Output Models

All providers return the same dataclass types defined in `ai/models.py`:

- **`AnalysisResult`** — Note analysis (summary, themes, quality_score, suggestions, connections)
- **`ComparisonResult`** — Note comparison (similarity_score, common_themes, differences, relationship)
- **`SimilarNote`** — Similar note reference (note_id, title, similarity, reason)

Each model has `from_json(json_str)` and `to_dict()` methods. `from_json()` handles:
- Missing fields (uses defaults)
- Extra fields (silently ignored)
- Score clamping (0.0–1.0)
- Invalid JSON (raises `ValueError`)

## Adding a New Provider

1. Create `src/python/ai/providers/your_provider.py`
2. Extend `AIProvider` base class
3. Set `name`, `provider_type`, `capabilities`
4. Implement `is_available()`, `get_status()`, `analyze_note()`, `compare_notes()`
5. Optionally implement `get_embedding()` / `get_embeddings_batch()`
6. Add to `PROVIDER_CLASSES` in `router.py`
7. Add to `DEFAULT_PRIORITY` in `router.py`
8. Add dependency info to `install.py`

## Obsidian CLI Bridge

`ai/obsidian_bridge.py` provides a bridge to Obsidian's native CLI (v1.12.4+) for data sourcing:

- **Backlinks** — `get_backlinks(note_path)`
- **Orphans** — `get_orphans()`
- **Tags** — `get_tags(note_path)`
- **Note content** — `read_note(note_path)`

The bridge uses a Null Object pattern: all methods return empty results when Obsidian CLI is unavailable, with no warnings unless `--verbose` is set.

## Embedding Cache

Embeddings are cached in the SQLite database (`note_embeddings` table):

- **Key**: `(note_id, provider, model)`
- **Invalidation**: `file_mtime` — re-computed when file modification time changes
- **Storage**: `numpy.float32` byte arrays as BLOBs

Cache methods in `db_manager.py`: `save_embedding()`, `get_embedding()`, `get_embedding_with_mtime()`, `delete_embeddings()`, `count_embeddings()`.

## API Key Management

| Provider | Env Variable | How to Get |
|----------|-------------|------------|
| Gemini API | `GOOGLE_API_KEY` or `GEMINI_API_KEY` | [Google AI Studio](https://aistudio.google.com/) |
| Anthropic API | `ANTHROPIC_API_KEY` | [Anthropic Console](https://console.anthropic.com/) |
| Ollama | N/A | Install from [ollama.com](https://ollama.com/) |

## Rate Limiting & Retry

- **Batch processing**: 10 notes per batch with configurable delay (default 4s)
- **Retry**: API providers use `@retry_with_backoff(max_retries=3, base_delay=1.0)` — exponential backoff on transient failures
- **Gemini free tier**: 1000 RPD, 1M TPM — batch delays prevent hitting limits

## Error Handling

- API failures: Retry with backoff, then raise
- Missing API keys: Provider reports `is_available() = False`, router skips
- Import errors: Caught in `_get_client()`, helpful install message
- Cache failures: Silently ignored (caching is optional optimization)
