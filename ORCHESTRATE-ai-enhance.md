# ORCHESTRATE: AI Enhancement — Modern SDKs + Obsidian CLI Integration

## Overview

Modernize the AI provider stack with latest SDKs and integrate with Obsidian's native CLI (v1.12.4+) for data sourcing. Focus on what `obs` uniquely provides — graph analysis + AI — while leveraging Obsidian CLI for note/link/tag data.

**Branch**: `feature/ai-enhance`
**Base**: `dev`
**Scope**: `src/python/ai/` (providers, config, install, features)

---

## Obsidian CLI Integration Principle

Obsidian CLI (v1.12.4+) provides 40+ commands for note CRUD, search, tags, backlinks, orphans, properties, tasks. Our `obs` tool should NOT duplicate these. Instead:

1. **Use Obsidian CLI as data source** where it's faster/more accurate (backlinks, orphans, tags)
2. **Focus AI on unique value-add**: graph metrics (PageRank, centrality, clustering) + AI analysis (similarity, duplicates, embeddings)
3. **Bridge commands**: `obs ai suggest-links` could combine graph metrics + AI embeddings + Obsidian CLI backlink data

---

## Increment 1: Gemini SDK Migration (1-2 hours)

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

**Structured output**: Define Pydantic models for `AnalysisResult`, `ComparisonResult`, `SimilarNote` and pass as `response_schema` — eliminates brittle `_parse_json_response()`.

**Batch embeddings**: Use `client.models.embed_content()` with list of texts (true batch, not sequential loop).

**Models**: Update defaults to `gemini-2.5-flash` (already set) — confirm latest available.

### Tests:
- Update `test_gemini_api.py` mocks for new SDK interface
- Add test for structured output parsing
- Add test for batch embeddings

---

## Increment 2: Anthropic API Provider (1-2 hours)

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
            embeddings=False,       # Anthropic doesn't have embeddings
            batch_embeddings=False,
            analysis=True,
            comparison=True,
        )
        self._client = None
        self.model = "claude-sonnet-4-6"  # Latest, fast + capable

    def _get_client(self):
        import anthropic
        if not self._client:
            self._client = anthropic.Anthropic()  # Uses ANTHROPIC_API_KEY env var
        return self._client

    def analyze_note(self, title, content, metadata):
        client = self._get_client()
        # Use messages.parse() for structured output with Pydantic
        response = client.messages.parse(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            response_model=AnalysisResult
        )
        return response
```

**Key decisions**:
- No embeddings (Anthropic doesn't offer them directly — that's fine, Gemini/Ollama handle embeddings)
- Use `messages.parse()` with Pydantic models for structured output
- Use `claude-sonnet-4-6` as default (good balance of speed/quality for note analysis)
- API key from `ANTHROPIC_API_KEY` env var (consistent with existing pattern)

### Routing priority update:
```
gemini-api > anthropic-api > ollama > gemini-cli > claude-cli
```

### Tests:
- `test_anthropic_api.py` — Mock SDK, test structured output
- Integration test with router fallback

---

## Increment 3: Obsidian CLI Bridge (1 hour)

**Goal**: Add optional integration with Obsidian's native CLI for data sourcing.

### Files to create:
- `src/python/ai/obsidian_bridge.py` — Bridge to Obsidian CLI commands

### Design:

```python
class ObsidianBridge:
    """Bridge to Obsidian's native CLI (v1.12.4+) for data sourcing."""

    def __init__(self):
        self._available = None

    def is_available(self) -> bool:
        """Check if Obsidian CLI is installed and Obsidian is running."""
        # Cache result
        if self._available is None:
            result = subprocess.run(["obsidian", "--version"], capture_output=True)
            self._available = result.returncode == 0
        return self._available

    def get_backlinks(self, file: str) -> List[str]:
        """Get backlinks for a note using Obsidian CLI."""
        result = subprocess.run(
            ["obsidian", "backlinks", f"file={file}", "format=json"],
            capture_output=True, text=True
        )
        return json.loads(result.stdout)

    def get_orphans(self) -> List[str]:
        """Get orphaned notes using Obsidian CLI."""
        result = subprocess.run(
            ["obsidian", "orphans", "format=json"],
            capture_output=True, text=True
        )
        return json.loads(result.stdout)

    def get_tags(self, sort: str = "count") -> Dict[str, int]:
        """Get vault tags with counts."""
        ...
```

**Integration points**:
- `features.py:find_similar_notes()` — enrich results with Obsidian backlink data
- `features.py:find_duplicates()` — use Obsidian's orphan list as starting point
- `graph_analyzer.py` — supplement NetworkX graph with Obsidian's link data for accuracy

**Graceful degradation**: If Obsidian CLI not available (not installed, Obsidian not running), fall back to existing file-scanning approach. Zero impact on current functionality.

---

## Increment 4: Shared Structured Output Models (30 min)

**Goal**: Define Pydantic models shared across all providers, replacing brittle JSON parsing.

### Files to create:
- `src/python/ai/models.py` — Shared Pydantic models

### Files to modify:
- `src/python/ai/providers/base.py` — Remove `_parse_json_response()`, use models
- All providers — Use shared models for structured output

### Models:

```python
from pydantic import BaseModel
from typing import List, Optional

class AnalysisResult(BaseModel):
    summary: str
    themes: List[str]
    quality_score: float  # 0.0-1.0
    suggestions: List[str]
    connections: List[str]

class ComparisonResult(BaseModel):
    similarity_score: float  # 0.0-1.0
    common_themes: List[str]
    differences: List[str]
    relationship: str

class SimilarNote(BaseModel):
    note_id: int
    title: str
    similarity: float
    reason: Optional[str] = None
```

**Benefit**: Both Gemini (`response_schema=`) and Anthropic (`response_model=`) can use these directly for native structured output. Ollama and CLI providers fall back to prompt-engineering + Pydantic `.model_validate_json()`.

---

## Increment 5: Cleanup & Docs (30 min)

**Goal**: Remove legacy files, update docs, update requirements.

### Files to delete:
- `src/python/ai_client.py` — Legacy v2 AI client
- `src/python/ai_client_ollama.py` — Legacy v2 Ollama client
- `src/python/ai_client_hf.py` — Legacy v2 HuggingFace client

### Files to update:
- `src/python/requirements.txt` — Clean up, add new deps
- `CLAUDE.md` — Update AI features section
- `README.md` — Update AI provider list
- `docs/` — Create `docs/developer/ai-providers.md` best practices guide
- `.STATUS` — Update completion

### Documentation to create:
- `docs/developer/ai-providers.md` — Provider architecture, best practices:
  - How to add a new provider
  - Structured output patterns
  - Obsidian CLI integration guide
  - API key management
  - Error handling and retry patterns

---

## Increment 6: Retry & Rate Limiting (optional, 30 min)

**Goal**: Add resilience to API providers.

### Files to modify:
- `src/python/ai/providers/base.py` — Add `@retry` decorator or mixin
- `src/python/ai/providers/gemini_api.py` — Apply retry
- `src/python/ai/providers/anthropic_api.py` — Apply retry

### Design:
```python
import time

def retry_with_backoff(max_retries=3, base_delay=1.0):
    """Decorator for API calls with exponential backoff."""
    def decorator(func):
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except (RateLimitError, TimeoutError) as e:
                    if attempt == max_retries - 1:
                        raise
                    delay = base_delay * (2 ** attempt)
                    time.sleep(delay)
        return wrapper
    return decorator
```

---

## Test Strategy

- Unit tests for each new/modified provider (mock SDK calls)
- Integration tests for router with new provider priority
- Test Obsidian bridge graceful degradation (CLI not available)
- Test Pydantic model validation for all result types
- Existing 42 Python tests must continue passing

## Order of Execution

1. **Increment 4** (models) — Foundation, needed by 1 & 2
2. **Increment 1** (Gemini migration) — Highest priority, deprecated SDK
3. **Increment 2** (Anthropic API) — New capability
4. **Increment 3** (Obsidian bridge) — Integration layer
5. **Increment 5** (cleanup & docs)
6. **Increment 6** (retry) — Optional polish

## PR Target

`feature/ai-enhance` → `dev`
