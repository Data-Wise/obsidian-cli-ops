# ORCHESTRATE: AI Enhancement — Modern SDKs + Obsidian CLI Integration

## Overview

Modernize the AI provider stack with latest SDKs and integrate with Obsidian's native CLI (v1.12.4+) for data sourcing. Focus on what `obs` uniquely provides — graph analysis + AI — while leveraging Obsidian CLI for note/link/tag data.

**Branch**: `feature/ai-enhance`
**Base**: `dev`
**Scope**: `src/python/ai/` (providers, config, install, features) + 4 new commands

---

## Design Decisions (from interactive review)

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Scope | All 6 increments | Full modernization |
| Obsidian CLI | Available, use it | Silent fallback to file scanning if Obsidian not running |
| Claude model default | `claude-sonnet-4-6` | Fast + capable, good balance for note analysis |
| Legacy ai_client*.py | Delete | Clean break, new ai/ package fully replaces them |
| Obsidian data sources | Backlinks, orphans, tags, note content | All 4 — query transiently, don't sync to DB |
| Pydantic vs dataclasses | Dataclasses with manual validation | Zero new dependencies |
| Docs location | `docs/developer/ai-providers.md` | Fits existing structure |
| New commands | 4 new commands under `obs ai` | suggest-links, cluster, gaps, summarize |
| Embedding cache | New `note_embeddings` table in vault DB | Single DB, invalidate on mtime change |
| Rate limits | Batch with delays + progress bar | 10 per batch, sleep between |
| suggest-links default | 5 suggestions with `--limit N` | Focused, actionable |
| Structured output | All providers return same dataclass types | CLI/Ollama parse JSON into dataclasses |
| Summarize scope | Vault-wide default, optional `--folder`/`--tag` | Flexible |

---

## Obsidian CLI Integration Principle

Obsidian CLI (v1.12.4+) provides 40+ commands for note CRUD, search, tags, backlinks, orphans, properties, tasks. Our `obs` tool does NOT duplicate these. Instead:

1. **Use Obsidian CLI as data source** — backlinks, orphans, tags, note content (transient, not synced to DB)
2. **Focus AI on unique value-add** — graph metrics (PageRank, centrality, clustering) + AI analysis (similarity, duplicates, embeddings)
3. **Silent fallback** — if Obsidian not running, fall back to file scanning. No warning unless `--verbose`.

---

## Increment 1: Shared Structured Output Models (30 min)

**Goal**: Define dataclass models shared across all providers, replacing brittle JSON parsing.

### Files to create:
- `src/python/ai/models.py` — Shared dataclass models

### Design:

```python
from dataclasses import dataclass, field
from typing import List, Optional
import json

@dataclass
class AnalysisResult:
    summary: str
    themes: List[str]
    quality_score: float  # 0.0-1.0
    suggestions: List[str]
    connections: List[str]

    @classmethod
    def from_json(cls, text: str) -> 'AnalysisResult':
        """Parse JSON string into AnalysisResult."""
        data = json.loads(text)
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})

    def to_dict(self) -> dict:
        return {k: getattr(self, k) for k in self.__dataclass_fields__}

@dataclass
class ComparisonResult:
    similarity_score: float  # 0.0-1.0
    common_themes: List[str]
    differences: List[str]
    relationship: str

    @classmethod
    def from_json(cls, text: str) -> 'ComparisonResult':
        data = json.loads(text)
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})

@dataclass
class SimilarNote:
    note_id: int
    title: str
    similarity: float
    reason: Optional[str] = None
```

### Files to modify:
- `src/python/ai/providers/base.py` — Remove `_parse_json_response()`, import models
- All providers — Return dataclass instances instead of dicts

**Contract**: ALL providers return the same dataclass types. Gemini/Anthropic use native structured output; Ollama/CLI providers parse JSON output into dataclasses via `from_json()`.

### Tests:
- Test `from_json()` parsing for each model
- Test validation (missing fields, extra fields, type coercion)

---

## Increment 2: Gemini SDK Migration (1-2 hours)

**Goal**: Replace deprecated `google-generativeai` with `google-genai` SDK.

### Files to modify:
- `src/python/ai/providers/gemini_api.py` — Rewrite client initialization and all API calls
- `src/python/ai/install.py` — Update `PROVIDER_DEPS` and `IMPORT_NAMES` mappings
- `src/python/requirements.txt` — Replace `google-generativeai` with `google-genai`

### Changes:

**gemini_api.py**:
```python
# OLD (deprecated)
import google.generativeai as genai
genai.configure(api_key=key)
client = genai.GenerativeModel(model)
response = client.generate_content(prompt)

# NEW (google-genai SDK)
from google import genai
client = genai.Client(api_key=key)
response = client.models.generate_content(
    model=model,
    contents=prompt,
    config=genai.types.GenerateContentConfig(
        response_mime_type="application/json",
        response_schema=AnalysisResult  # Native structured output
    )
)
```

**Structured output**: Pass dataclass schema to `response_schema` for native JSON validation.

**Batch embeddings**: Use `client.models.embed_content()` with list of texts (true batch, not sequential loop).

**Models**: Keep `gemini-2.5-flash` (analysis), `text-embedding-004` (embeddings).

### install.py changes:
```python
PROVIDER_DEPS = {
    "gemini-api": ["google-genai"],  # was google-generativeai
    ...
}
IMPORT_NAMES = {
    "google-genai": "google.genai",  # was google.generativeai
    ...
}
```

### Tests:
- Update `test_gemini_api.py` mocks for new SDK interface
- Add test for structured output parsing → dataclass
- Add test for true batch embeddings

---

## Increment 3: Anthropic API Provider (1-2 hours)

**Goal**: Add direct `anthropic` SDK provider alongside existing CLI wrapper.

### Files to create:
- `src/python/ai/providers/anthropic_api.py` — New provider using `anthropic` Python SDK

### Files to modify:
- `src/python/ai/install.py` — Add `anthropic-api` to `PROVIDER_DEPS`
- `src/python/ai/router.py` — Add `anthropic-api` to routing priority
- `src/python/ai/config.py` — Add config for anthropic-api provider
- `src/python/ai/providers/__init__.py` — Export new provider
- `src/python/requirements.txt` — Add `anthropic>=0.40.0` (commented, optional)

### Design:

```python
class AnthropicAPIProvider(AIProvider):
    """Direct Anthropic API provider using official SDK."""

    def __init__(self):
        self.provider_type = ProviderType.API
        self.capabilities = ProviderCapabilities(
            embeddings=False,       # Anthropic doesn't have native embeddings
            batch_embeddings=False,
            analysis=True,
            comparison=True,
        )
        self._client = None
        self.model = "claude-sonnet-4-6"  # Fast + capable

    def _get_client(self):
        import anthropic
        if not self._client:
            self._client = anthropic.Anthropic()  # Uses ANTHROPIC_API_KEY env var
        return self._client

    def analyze_note(self, title, content, metadata) -> AnalysisResult:
        client = self._get_client()
        response = client.messages.create(
            model=self.model,
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}],
        )
        return AnalysisResult.from_json(response.content[0].text)

    def compare_notes(self, note1, note2) -> ComparisonResult:
        client = self._get_client()
        response = client.messages.create(
            model=self.model,
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}],
        )
        return ComparisonResult.from_json(response.content[0].text)
```

**Key decisions**:
- No embeddings (Anthropic doesn't offer them — Gemini/Ollama handle embeddings)
- Default model: `claude-sonnet-4-6`
- API key from `ANTHROPIC_API_KEY` env var
- Returns structured dataclass types via `from_json()` parsing

### Routing priority update:
```
gemini-api > anthropic-api > ollama > gemini-cli > claude-cli
```

### Tests:
- `test_anthropic_api.py` — Mock SDK, test structured output
- Integration test with router fallback

---

## Increment 4: Obsidian CLI Bridge (1 hour)

**Goal**: Add optional integration with Obsidian's native CLI for data sourcing.

### Files to create:
- `src/python/ai/obsidian_bridge.py` — Bridge to Obsidian CLI commands

### Design:

```python
import subprocess
import json
from typing import List, Dict, Optional

class ObsidianBridge:
    """Bridge to Obsidian's native CLI (v1.12.4+) for data sourcing.

    Requires Obsidian to be running. Falls back silently if unavailable.
    Data is used transiently — not synced to SQLite.
    """

    def __init__(self):
        self._available = None

    def is_available(self) -> bool:
        """Check if Obsidian CLI is installed and Obsidian is running."""
        if self._available is None:
            try:
                result = subprocess.run(
                    ["obsidian", "--version"],
                    capture_output=True, timeout=5
                )
                self._available = result.returncode == 0
            except (FileNotFoundError, subprocess.TimeoutExpired):
                self._available = False
        return self._available

    def get_backlinks(self, file: str) -> List[str]:
        """Get backlinks for a note. Returns empty list if unavailable."""
        if not self.is_available():
            return []
        result = subprocess.run(
            ["obsidian", "backlinks", f"file={file}", "format=json"],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode == 0:
            return json.loads(result.stdout)
        return []

    def get_orphans(self) -> List[str]:
        """Get orphaned notes. Returns empty list if unavailable."""
        if not self.is_available():
            return []
        result = subprocess.run(
            ["obsidian", "orphans", "format=json"],
            capture_output=True, text=True, timeout=30
        )
        if result.returncode == 0:
            return json.loads(result.stdout)
        return []

    def get_tags(self, sort: str = "count") -> Dict[str, int]:
        """Get vault tags with counts. Returns empty dict if unavailable."""
        if not self.is_available():
            return {}
        result = subprocess.run(
            ["obsidian", "tags", f"sort={sort}", "format=json"],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode == 0:
            return json.loads(result.stdout)
        return {}

    def read_note(self, file: str) -> Optional[str]:
        """Read note content via Obsidian CLI. Returns None if unavailable."""
        if not self.is_available():
            return None
        result = subprocess.run(
            ["obsidian", "read", f"file={file}"],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode == 0:
            return result.stdout
        return None
```

**Integration points** in `features.py`:
- `find_similar_notes()` — enrich results with Obsidian backlink data
- `find_duplicates()` — use Obsidian's orphan list as starting candidates
- New commands (Increment 5b) — bridge is primary data source

**Fallback**: Every method returns empty/None if Obsidian CLI unavailable. Callers don't need to check — they just get less data.

### Tests:
- Test graceful degradation (mock subprocess returning errors)
- Test JSON parsing from Obsidian CLI output
- Test availability caching

---

## Increment 5: New AI Commands (1-2 hours)

**Goal**: Add 4 new commands that combine graph analysis + AI + Obsidian CLI data.

### New commands (all under `obs ai`):

#### `obs ai suggest-links <note>`
- Get note's current backlinks (Obsidian CLI) and graph neighbors (NetworkX)
- Compute embeddings for the note and all vault notes (cached in SQLite)
- Find top 5 most similar notes that aren't already linked
- Display: note title, similarity score, reason for suggestion
- Flag: `--limit N` to change default count

#### `obs ai cluster <vault>`
- Get all tags (Obsidian CLI) and note embeddings (cached)
- Cluster notes using embeddings + tag overlap
- Use scikit-learn KMeans or DBSCAN
- Display: cluster name (auto-generated from top tags), member count, key notes
- Flag: `--n-clusters N` (default: auto-detect via silhouette score)

#### `obs ai gaps <vault>`
- Compute PageRank and centrality (existing graph_analyzer)
- Get orphans (Obsidian CLI) and backlink counts
- Find notes with high incoming references but low content (< 100 words)
- Find topic areas with high centrality but few notes
- Display: gap description, related notes, suggested action

#### `obs ai summarize <vault>`
- Default: whole vault. Optional: `--folder=X` or `--tag=X` to scope
- Get notes in scope (Obsidian CLI `files` or file scanning)
- Batch process through AI for theme extraction (batches of 10, delay between)
- Aggregate themes, identify top hubs (PageRank), orphan count
- Display: vault summary, top themes, key hubs, orphan analysis, knowledge graph stats
- Show progress bar for large vaults

### Embedding Cache (SQLite):

Add to `schema/vault_db.sql`:
```sql
CREATE TABLE IF NOT EXISTS note_embeddings (
    note_id INTEGER NOT NULL,
    provider TEXT NOT NULL,      -- e.g. 'gemini-api', 'ollama'
    model TEXT NOT NULL,         -- e.g. 'text-embedding-004'
    vector BLOB NOT NULL,        -- numpy array serialized
    updated_at TEXT NOT NULL,    -- ISO 8601
    file_mtime REAL NOT NULL,    -- file modification time at embedding creation
    PRIMARY KEY (note_id, provider, model),
    FOREIGN KEY (note_id) REFERENCES notes(id)
);
```

Cache invalidation: compare `file_mtime` with current `os.path.getmtime()`. Recompute if file changed.

### Rate limiting:
- Batch size: 10 requests per batch
- Delay: 4 seconds between batches (keeps under 15 RPM for Gemini free tier)
- Progress bar via Rich

### Files to modify:
- `src/python/obs_cli.py` — Add 4 new argparse subcommands under `ai`
- `src/python/ai/features.py` — Add new feature functions
- `src/python/core/graph_analyzer.py` — Expose PageRank/centrality for new commands
- `src/python/db_manager.py` — Add embedding cache CRUD
- `src/obs.zsh` — Add wrappers for new commands
- `schema/vault_db.sql` — Add `note_embeddings` table

### Tests:
- Unit test each new feature function with mocked providers
- Test embedding cache hit/miss/invalidation
- Test rate limiting batching logic

---

## Increment 6: Cleanup, Docs & Retry (1 hour)

### 6a: Delete Legacy Files
- `src/python/ai_client.py`
- `src/python/ai_client_ollama.py`
- `src/python/ai_client_hf.py`

Verify nothing imports them first (grep for `from ai_client` and `import ai_client`).

### 6b: Update requirements.txt
```
# AI integration - API providers (optional)
# google-genai>=1.0.0          # Gemini API (has free tier)
# anthropic>=0.40.0            # Claude API (paid)
requests>=2.31.0               # For Ollama client
numpy>=1.24.0                  # For embedding similarity
```

Remove `sentence-transformers` (was for HuggingFace, now deleted).
Remove `google-generativeai` (replaced by `google-genai`).

### 6c: Retry with Exponential Backoff

Add to `src/python/ai/providers/base.py`:

```python
import time
import functools

def retry_with_backoff(max_retries=3, base_delay=1.0, exceptions=(Exception,)):
    """Decorator for API calls with exponential backoff."""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    if attempt == max_retries - 1:
                        raise
                    delay = base_delay * (2 ** attempt)
                    time.sleep(delay)
        return wrapper
    return decorator
```

Apply to `analyze_note()`, `compare_notes()`, `get_embedding()` in Gemini and Anthropic providers.

### 6d: Documentation

Create `docs/developer/ai-providers.md`:
- Provider architecture overview (diagram)
- Available providers table (capabilities, requirements, cost)
- How to add a new provider (step-by-step)
- Structured output patterns (dataclass models)
- Obsidian CLI integration guide
- Embedding cache design
- API key management
- Rate limiting strategy
- Error handling and retry patterns

### 6e: Update existing docs
- `CLAUDE.md` — Update AI features section, command count (10 → 14)
- `README.md` — Update AI provider list, add new commands
- `.STATUS` — Update completion

### Tests:
- Verify no imports of deleted legacy files
- Test retry decorator behavior

---

## Test Strategy

| Test Type | Count | What |
|-----------|-------|------|
| Existing | 42 | Must continue passing |
| Models | ~8 | dataclass from_json, validation |
| Gemini SDK | ~6 | New SDK interface, structured output, batch embeddings |
| Anthropic API | ~6 | SDK mock, structured output, error handling |
| Obsidian bridge | ~6 | Graceful degradation, JSON parsing, caching |
| New commands | ~12 | suggest-links, cluster, gaps, summarize |
| Embedding cache | ~4 | CRUD, invalidation, mtime check |
| Retry decorator | ~3 | Backoff timing, max retries, exception filtering |
| **Total new** | **~45** | |
| **Grand total** | **~87** | |

---

## Order of Execution

1. **Increment 1** (models) — Foundation for all providers
2. **Increment 2** (Gemini migration) — Fix deprecated SDK
3. **Increment 3** (Anthropic API) — New capability
4. **Increment 4** (Obsidian bridge) — Data source layer
5. **Increment 5** (new commands) — User-facing features
6. **Increment 6** (cleanup, docs, retry) — Polish

## PR Target

`feature/ai-enhance` → `dev`

## Estimated Total: 5-7 hours
