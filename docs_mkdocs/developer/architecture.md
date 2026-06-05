# Architecture

**Version:** 3.2.0

Obsidian CLI Ops follows a clean **three-layer architecture** with an optional AI feature layer.

## Overview

```
Presentation (CLI)  -->  Application (Core Logic)  -->  Data (DB/Files)
                              |
                         AI Features (optional)
```

**Goals:** Code reusability, testability, flexibility, maintainability.

## Layer Diagram

```
Presentation Layer
  ZSH CLI (obs.zsh, 386 lines) --> Python CLI (obs_cli.py)

Application Layer (Core)
  VaultManager (311 lines)    GraphAnalyzer (311 lines)
  Domain Models (237 lines)   Custom Exceptions

AI Features Layer (Optional)
  AIRouter (312 lines)        Features (~744 lines)
  FeaturesVault (~500 lines)  FeaturesRefactor (~345 lines)
  5 Providers                 ObsidianBridge (123 lines)

Data Layer
  DatabaseManager (469 lines) VaultScanner (373 lines)
  GraphBuilder (307 lines)    SQLite Database
```

## Key Principles

### Zero Duplication

Business logic lives in the Core layer only. The CLI is a thin presentation layer that formats output.

```python
# Core layer (shared logic)
class VaultManager:
    def scan_vault(self, path: str) -> ScanResult:
        # Business logic once
        ...

# CLI (presentation only)
def scan_command(args):
    result = vault_manager.scan_vault(args.path)
    print(f"Scanned {result.notes_scanned} notes")  # Formatting
```

### Domain Models

Type-safe dataclasses for all business entities:

- `Vault`, `Note`, `ScanResult`, `GraphMetrics`, `VaultStats`
- AI models: `AnalysisResult`, `ComparisonResult`, `SimilarNote`
- Quality models (v3.2.0): `MergeCandidate`, `TagSuggestion`, `NoteQuality`

All models have `from_dict()`, `to_dict()`, and `from_json()` methods.

### AI Provider Architecture

5 providers with automatic fallback routing:

```
gemini-api > anthropic-api > ollama > gemini-cli > claude-cli
```

- Providers implement a common `AIProvider` interface
- All return the same dataclass types (no provider-specific returns)
- Embedding cache in SQLite with mtime invalidation
- ObsidianBridge uses the Null Object pattern (returns empty results when CLI unavailable)

## Data Flow

### Scanning a Vault

```
User --> obs scan /vault
  --> ZSH CLI (dispatcher)
    --> Python CLI (parse args)
      --> VaultManager.scan_vault()
        --> VaultScanner.scan_vault()
          --> DatabaseManager (INSERT notes, links, tags)
            --> SQLite
```

### AI Feature (suggest-links)

```
User --> obs ai suggest-links note-1
  --> Python CLI
    --> suggest_links(note_id, db)
      --> Get note embedding (cached in note_embeddings table)
      --> Compare to all candidates
      --> Exclude existing links
      --> Return top-N suggestions
```

### Quality Scoring (graph-only, no AI)

```
User --> obs ai quality MyVault
  --> Python CLI
    --> note_quality_vault(vault_id, db)
      --> list_notes() + get_orphaned_notes()
      --> For each note:
        --> Read file content (completeness: word count, headings)
        --> get_outgoing_links() + get_incoming_links() (connectivity)
        --> get_note_tags() (metadata)
        --> Check modified_at (freshness)
      --> Weighted score: completeness 30% + connectivity 30% + metadata 20% + freshness 20%
      --> Return List[NoteQuality] sorted worst-first
```

### Merge Suggest (embedding similarity)

```
User --> obs ai merge-suggest MyVault
  --> Python CLI
    --> merge_suggest_vault(vault_id, db)
      --> Batch-load all note_embeddings (single SQL JOIN)
      --> L2-normalize, compute np.dot(matrix, matrix.T) for all pairs
      --> Filter pairs above threshold (default 0.8)
      --> Enrich with shared links/tags from DB
      --> Return List[MergeCandidate] sorted by similarity
```

## File Structure

```
src/python/
  core/                      # APPLICATION LAYER
    vault_manager.py         # Vault operations
    graph_analyzer.py        # Graph operations
    models.py                # Domain models
    exceptions.py            # Custom exceptions

  ai/                        # AI FEATURES LAYER
    features.py              # Core AI features (similar, analyze, duplicates, suggest-links, gaps, summarize)
    features_vault.py        # Vault-level features (merge-suggest, tag-suggest, quality) [v3.2.0]
    features_refactor.py     # Refactor vault feature (extracted from features.py) [v3.2.0]
    router.py                # Smart provider selection
    models.py                # AI dataclasses (6 types)
    obsidian_bridge.py       # Obsidian CLI bridge
    providers/               # 5 AI providers

  obs_cli.py                 # PRESENTATION LAYER
  db_manager.py              # DATA LAYER
  vault_scanner.py           # DATA LAYER
  graph_builder.py           # DATA LAYER
```

## Design Patterns

| Pattern | Where Used |
|---------|-----------|
| **Repository** | DatabaseManager wraps SQLite |
| **Facade** | VaultManager/GraphAnalyzer simplify complex operations |
| **Factory** | `from_db_row()` class methods on domain models |
| **Dependency Injection** | Core classes accept optional DatabaseManager |
| **Null Object** | ObsidianBridge returns empty results when unavailable |

## Testing

- **235 pytest tests** covering core, AI, vault features, and data layers
- **59 Jest tests** for ZSH wrapper + dependency-bootstrapping validation (2 network-gated, run in CI)
- Core layer tested independently with mocked dependencies
- AI providers mocked for deterministic tests
