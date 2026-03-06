# Architecture

**Version:** 3.0.0

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
  AIRouter (312 lines)        Features (~960 lines)
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

All models have `from_db_row()`, `to_dict()`, and `to_json()` methods.

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

## File Structure

```
src/python/
  core/                      # APPLICATION LAYER
    vault_manager.py         # Vault operations
    graph_analyzer.py        # Graph operations
    models.py                # Domain models
    exceptions.py            # Custom exceptions

  ai/                        # AI FEATURES LAYER
    features.py              # 8 AI feature functions
    router.py                # Smart provider selection
    models.py                # AI dataclasses
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

- **202 pytest tests** covering core, AI, and data layers
- **30 Jest tests** for ZSH wrapper validation
- Core layer tested independently with mocked dependencies
- AI providers mocked for deterministic tests
