# AI API Reference

**Module:** `src/python/ai/`
**Version:** 3.0.0-beta
**Last Updated:** 2026-03-04

Complete reference for the AI features layer: functions, dataclasses, routing, and caching.

---

## Table of Contents

1. [Entry Point](#entry-point)
2. [Feature Functions](#feature-functions)
3. [Data Models](#data-models)
4. [Router & Provider Selection](#router--provider-selection)
5. [Obsidian Bridge](#obsidian-bridge)
6. [Embedding Cache](#embedding-cache)
7. [Error Handling](#error-handling)

---

## Entry Point

```python
from ai.router import get_ai_client

client = get_ai_client()                        # Auto-select best provider
client = get_ai_client(provider="ollama")       # Force specific provider
```

`get_ai_client()` returns an `AIRouter` singleton. The router auto-selects providers based on operation type and availability.

---

## Feature Functions

All functions live in `ai/features.py`. Import individually:

```python
from ai.features import find_similar_notes, analyze_note, suggest_links
```

### find_similar_notes

```python
def find_similar_notes(
    note_id: str,
    db_manager: DatabaseManager,
    limit: int = 10,
    min_similarity: float = 0.3,
    provider: Optional[str] = None,
) -> List[SimilarityMatch]
```

Find notes semantically similar to a given note using embedding cosine similarity.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `note_id` | `str` | required | Source note ID |
| `db_manager` | `DatabaseManager` | required | Database instance |
| `limit` | `int` | `10` | Max results |
| `min_similarity` | `float` | `0.3` | Minimum similarity threshold (0.0–1.0) |
| `provider` | `Optional[str]` | `None` | Force specific AI provider |

**Returns:** `List[SimilarityMatch]` sorted by similarity (highest first)

**Raises:** `ValueError` (note not found), `RuntimeError` (no AI provider)

**Example:**
```python
matches = find_similar_notes("abc123", db, limit=5, min_similarity=0.5)
for m in matches:
    print(f"{m.title}: {m.similarity:.0%}")
```

---

### analyze_note

```python
def analyze_note(
    note_id: str,
    db_manager: DatabaseManager,
    provider: Optional[str] = None,
) -> AnalysisResult
```

Deep AI analysis of a single note — themes, quality, suggestions.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `note_id` | `str` | required | Note ID to analyze |
| `db_manager` | `DatabaseManager` | required | Database instance |
| `provider` | `Optional[str]` | `None` | Force specific AI provider |

**Returns:** `AnalysisResult` with summary, themes, quality_score, suggestions, connections

**Raises:** `ValueError` (note not found), `RuntimeError` (no AI provider)

---

### find_duplicates

```python
def find_duplicates(
    vault_id: str,
    db_manager: DatabaseManager,
    threshold: float = 0.85,
    limit: int = 50,
    provider: Optional[str] = None,
) -> List[DuplicateGroup]
```

Detect potential duplicate notes using embedding similarity with Union-Find clustering.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `vault_id` | `str` | required | Vault ID to scan |
| `db_manager` | `DatabaseManager` | required | Database instance |
| `threshold` | `float` | `0.85` | Minimum similarity for duplicate detection |
| `limit` | `int` | `50` | Max duplicate groups to return |
| `provider` | `Optional[str]` | `None` | Force specific AI provider |

**Returns:** `List[DuplicateGroup]` sorted by similarity

**Raises:** `ValueError` (vault not found), `RuntimeError` (no AI provider)

---

### compare_notes

```python
def compare_notes(
    note1_id: str,
    note2_id: str,
    db_manager: DatabaseManager,
    provider: Optional[str] = None,
) -> ComparisonResult
```

Compare two notes for similarity, common themes, and merge potential.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `note1_id` | `str` | required | First note ID |
| `note2_id` | `str` | required | Second note ID |
| `db_manager` | `DatabaseManager` | required | Database instance |
| `provider` | `Optional[str]` | `None` | Force specific AI provider |

**Returns:** `ComparisonResult` with similarity_score, common_themes, differences, relationship

**Raises:** `ValueError` (note not found), `RuntimeError` (no AI provider)

---

### suggest_links

```python
def suggest_links(
    note_id: str,
    db_manager: DatabaseManager,
    limit: int = 5,
    provider: Optional[str] = None,
    verbose: bool = False,
) -> List[LinkSuggestion]
```

Suggest new wikilinks for a note based on embedding similarity, excluding already-linked notes.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `note_id` | `str` | required | Source note ID |
| `db_manager` | `DatabaseManager` | required | Database instance |
| `limit` | `int` | `5` | Number of suggestions |
| `provider` | `Optional[str]` | `None` | Force specific AI provider |
| `verbose` | `bool` | `False` | Log cache hits/misses and embedding computation to stderr |

**Returns:** `List[LinkSuggestion]` sorted by similarity

**Raises:** `ValueError` (note not found)

**How it works:**
1. Gets source note embedding (cached)
2. Queries existing outgoing links from `links` table
3. Computes embeddings for all candidate notes (cached)
4. Returns top-N by cosine similarity, excluding already-linked notes

---

### find_gaps

```python
def find_gaps(
    vault_id: str,
    db_manager: DatabaseManager,
    provider: Optional[str] = None,
    verbose: bool = False,
) -> List[KnowledgeGap]
```

Identify knowledge gaps: stub notes (high in-degree, low word count), orphans, and Obsidian CLI-detected orphans.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `vault_id` | `str` | required | Vault ID to analyze |
| `db_manager` | `DatabaseManager` | required | Database instance |
| `provider` | `Optional[str]` | `None` | Force specific AI provider |
| `verbose` | `bool` | `False` | Log Obsidian CLI fallback status to stderr |

**Returns:** `List[KnowledgeGap]`

**Raises:** `ValueError` (vault not found)

**Gap detection strategy:**
1. **Stub notes** — `word_count < 100` with `in_degree > 3` (via `graph_metrics` JOIN)
2. **DB orphans** — Notes with no links in either direction
3. **Bridge orphans** — Additional orphans detected by Obsidian CLI (if running)

---

### summarize_vault

```python
def summarize_vault(
    vault_id: str,
    db_manager: DatabaseManager,
    folder: Optional[str] = None,
    tag: Optional[str] = None,
    provider: Optional[str] = None,
    batch_size: int = 10,
    batch_delay: float = 4.0,
    progress_callback: Optional[Callable[[int, int], None]] = None,
    verbose: bool = False,
) -> VaultSummary
```

Generate a vault-wide summary with themes, hubs, and graph stats. Processes notes in batches with rate limiting.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `vault_id` | `str` | required | Vault ID |
| `db_manager` | `DatabaseManager` | required | Database instance |
| `folder` | `Optional[str]` | `None` | Scope to folder path |
| `tag` | `Optional[str]` | `None` | Scope to tag |
| `provider` | `Optional[str]` | `None` | Force specific AI provider |
| `batch_size` | `int` | `10` | Notes per batch |
| `batch_delay` | `float` | `4.0` | Seconds between batches (rate limiting) |
| `progress_callback` | `Callable` | `None` | Called with `(current, total)` after each note |
| `verbose` | `bool` | `False` | Enable verbose logging |

**Returns:** `VaultSummary`

**Raises:** `ValueError` (vault not found), `RuntimeError` (no AI provider)

---

## Data Models

### Feature-Level Dataclasses

Defined in `ai/features.py`:

#### SimilarityMatch

```python
@dataclass
class SimilarityMatch:
    note_id: str        # Matched note ID
    title: str          # Note title
    path: str           # File path relative to vault
    similarity: float   # 0.0–1.0 cosine similarity
    reason: str = ""    # Human-readable explanation
```

#### LinkSuggestion

```python
@dataclass
class LinkSuggestion:
    source_title: str   # Source note title
    target_title: str   # Suggested target title
    target_path: str    # Target file path
    similarity: float   # 0.0–1.0 cosine similarity
    reason: str = ""    # Human-readable explanation
```

#### KnowledgeGap

```python
@dataclass
class KnowledgeGap:
    description: str                        # What the gap is
    related_notes: List[str] = []           # Affected note titles
    suggested_action: str = ""              # What to do about it
```

#### DuplicateGroup

```python
@dataclass
class DuplicateGroup:
    notes: List[Dict]    # [{'id', 'title', 'path'}, ...]
    similarity: float    # Average pairwise similarity
    reason: str = ""     # Human-readable explanation
```

#### VaultSummary

```python
@dataclass
class VaultSummary:
    note_count: int = 0
    themes: List[str] = []                  # Top themes (lowercase, sorted by frequency)
    top_hubs: List[Dict] = []               # [{'title', 'connections'}, ...]
    orphan_count: int = 0
    graph_stats: Dict = {}                  # {'total_notes', 'themes_found', 'hub_count'}
    summary_text: str = ""                  # One-sentence summary
```

### Provider-Level Dataclasses

Defined in `ai/models.py`. All providers return these types:

#### AnalysisResult

```python
@dataclass
class AnalysisResult:
    summary: str = ""                       # Note summary
    themes: List[str] = []                  # Detected themes
    quality_score: float = 0.0              # 0.0–1.0 (clamped)
    suggestions: List[str] = []             # Improvement suggestions
    connections: List[str] = []             # Related topic suggestions
```

**Serialization:**
- `AnalysisResult.from_json(json_str)` — Parse LLM output (ignores extra keys, clamps scores)
- `result.to_dict()` — Serialize to dictionary

#### ComparisonResult

```python
@dataclass
class ComparisonResult:
    similarity_score: float = 0.0           # 0.0–1.0 (clamped)
    common_themes: List[str] = []           # Shared themes
    differences: List[str] = []             # Key differences
    relationship: str = ""                  # e.g. "complementary", "overlapping"
```

#### SimilarNote

```python
@dataclass
class SimilarNote:
    note_id: int = 0
    title: str = ""
    similarity: float = 0.0
    reason: Optional[str] = None
```

### Design Decision: Dataclasses over Pydantic

All models use stdlib `dataclasses` with manual `from_json()` validation to avoid adding Pydantic as a dependency. The `from_json()` methods:

- Ignore extra keys (LLMs often add unexpected fields)
- Use default values for missing fields
- Clamp scores to 0.0–1.0
- Raise `ValueError` on invalid JSON

---

## Router & Provider Selection

### AIRouter

```python
class AIRouter:
    def __init__(
        self,
        priority: Optional[List[str]] = None,
        preferred_provider: Optional[str] = None,
    )
```

The router selects providers based on operation type and availability.

**Routing strategy:**

| Operation | Provider Priority |
|-----------|------------------|
| Embedding | gemini-api > ollama |
| Batch embedding | gemini-api > ollama > sequential fallback |
| Analysis | gemini-api > anthropic-api > ollama > gemini-cli > claude-cli |
| Comparison | Same as analysis |

**Router methods:**

| Method | Returns | Description |
|--------|---------|-------------|
| `get_embedding(text)` | `List[float]` | Get single embedding |
| `get_embeddings_batch(texts)` | `List[List[float]]` | Batch embeddings (falls back to sequential) |
| `analyze_note(content, title)` | `AnalysisResult` | Analyze a note |
| `compare_notes(c1, c2, t1, t2)` | `ComparisonResult` | Compare two notes |
| `get_status()` | `Dict` | All provider statuses |
| `refresh_availability()` | `None` | Clear availability cache |

### Provider Capabilities

| Provider | Embeddings | Batch | Analysis | Comparison | Cost |
|----------|:----------:|:-----:|:--------:|:----------:|------|
| gemini-api | Yes | Yes | Yes | Yes | Free tier |
| anthropic-api | No | No | Yes | Yes | Paid |
| ollama | Yes | No | Yes | Yes | Free (local) |
| gemini-cli | No | No | Yes | Yes | Subscription |
| claude-cli | No | No | Yes | Yes | Subscription |

### Adding a Provider

1. Create `ai/providers/your_provider.py` extending `AIProvider`
2. Set `name`, `provider_type`, `capabilities`
3. Implement `is_available()`, `get_status()`, `analyze_note()`, `compare_notes()`
4. Optionally implement `get_embedding()` / `get_embeddings_batch()`
5. Add to `PROVIDER_CLASSES` and `DEFAULT_PRIORITY` in `router.py`
6. Add dependency info to `install.py`

---

## Obsidian Bridge

```python
from ai.obsidian_bridge import ObsidianBridge

bridge = ObsidianBridge(verbose=False)
```

Bridge to Obsidian's native CLI (v1.12.4+) for supplementary data. Uses the **Null Object pattern** — all methods return empty results when Obsidian CLI is unavailable.

| Method | Returns | Fallback |
|--------|---------|----------|
| `is_available()` | `bool` | Cached after first check |
| `get_backlinks(file)` | `List[str]` | `[]` |
| `get_orphans()` | `List[str]` | `[]` |
| `get_tags(sort="count")` | `Dict[str, int]` | `{}` |
| `read_note(file)` | `Optional[str]` | `None` |
| `reset()` | `None` | Clears availability cache |

**Verbose mode:** When `verbose=True` and the CLI is unavailable, prints a notice to stderr:
```
  [verbose] Obsidian CLI not available, using file scanning fallback
```

**Requirements:** Obsidian must be running. CLI availability is checked once and cached.

---

## Embedding Cache

Embeddings are stored in the `note_embeddings` SQLite table to avoid recomputation.

### Cache Function

```python
def _get_cached_embedding(
    note_id: str,
    content: str,
    file_mtime: float,
    db_manager: DatabaseManager,
    router: AIRouter,
    provider_name: str = "",
    model_name: str = "",
) -> List[float]
```

**Cache key:** `(note_id, provider, model)`

**Invalidation:** `file_mtime` — cache is invalidated when the file's modification time changes.

**Storage format:** `numpy.float32` byte arrays stored as SQLite BLOBs.

**Exception handling:**
- Cache read failures: `(OSError, KeyError)` — table might not exist or row format unexpected
- Cache write failures: `(OSError, sqlite3.OperationalError)` — table missing or disk full
- Both are non-fatal; caching is an optimization, not a requirement

### Database Methods

| Method | Description |
|--------|-------------|
| `db.ensure_embeddings_table()` | Create table if not exists |
| `db.save_embedding(note_id, provider, model, vector, mtime)` | Store embedding |
| `db.get_embedding_with_mtime(note_id, provider, model)` | Retrieve with mtime for invalidation check |
| `db.delete_embeddings(note_id)` | Remove cached embeddings |
| `db.count_embeddings()` | Count cached entries |

---

## Error Handling

### Exception Strategy

| Context | Exception Types | Rationale |
|---------|----------------|-----------|
| File I/O (`_get_note_content`) | `(OSError, UnicodeDecodeError)` | File permissions + encoding |
| SQL queries (links, metrics) | `(sqlite3.OperationalError, KeyError)` | Missing table + row format |
| Cache read | `(OSError, KeyError)` | DB file + stale schema |
| Cache write | `(OSError, sqlite3.OperationalError)` | Table missing + disk full |
| Batch API fallback | `Exception` (broad) | Graceful degradation to sequential |
| Batch analysis loop | `Exception` (broad) | One note failing shouldn't kill the batch |

**Principle:** Narrow exceptions for internal operations (bugs should propagate). Broad exceptions at API/provider boundaries where the fallback is always correct.

### Error Flow

```
User calls obs ai suggest-links note-1
  → obs_cli.py catches (ValueError, RuntimeError) → prints error, exits 1
    → suggest_links() raises ValueError if note/vault not found
      → _get_cached_embedding() silently handles cache miss
        → router.get_embedding() raises RuntimeError if no provider
```
