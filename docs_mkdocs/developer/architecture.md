# Architecture

**Version:** 3.4.1

Obsidian CLI Ops follows a clean **four-layer architecture**: Presentation, Application (Core), AI Features, and Data — plus an MCP Integration layer added in v3.3.0.

---

## High-Level Overview

```mermaid
flowchart TD
    subgraph Presentation["Presentation Layer"]
        Z[obs.zsh\n501 lines]
        P[obs_cli.py\n985 lines]
    end

    subgraph MCP["MCP Integration Layer (v3.3.0)"]
        M[mcp_server.py\n956 lines\n20 tools · 4 resources]
    end

    subgraph Core["Application Layer (Core)"]
        VM[VaultManager]
        GA[GraphAnalyzer]
        DM[Domain Models]
    end

    subgraph AI["AI Features Layer (Optional)"]
        AR[AIRouter]
        FT[features.py]
        FV[features_vault.py]
        FR[features_refactor.py]
        OB[ObsidianBridge\nNull Object]
        PR[5 Providers]
    end

    subgraph Data["Data Layer"]
        DB[DatabaseManager]
        VS[VaultScanner]
        GB[GraphBuilder]
        SQ[(SQLite\nvault_db)]
        FS[Vault .md files]
    end

    Z --> P
    P --> VM
    P --> GA
    M --> P
    VM --> DB
    GA --> DB
    VM --> VS
    VS --> FS
    FT --> DB
    FV --> DB
    FR --> DB
    AR --> PR
    DB --> SQ
    GB --> SQ
```

**Key principle:** Business logic lives in the Core layer only. Both the ZSH CLI and the MCP server are thin presentation layers that call `obs_cli.py` subprocesses or Python APIs.

---

## Layer Details

### Presentation Layer

```mermaid
flowchart LR
    U([User / Terminal]) -->|shell command| Z[obs.zsh\n501 lines]
    Z -->|subprocess| P[obs_cli.py\n985 lines]
    P -->|imports| VM[VaultManager]
    P -->|imports| GA[GraphAnalyzer]
    P --> Rich[Rich Output\ntables, colors, progress]
```

- **`obs.zsh`** — ZSH dispatcher. Resolves Python interpreter (3-candidate chain: `$OBS_PYTHON` → user venv → Homebrew venv → ambient), calls `obs_cli.py` via subprocess, handles `--verbose`.
- **`obs_cli.py`** — Python CLI. Argparse subcommands, calls Core/AI methods, formats output with Rich.

### MCP Integration Layer (v3.3.0)

```mermaid
flowchart LR
    C([Claude Desktop\nClaude Code\nCowork]) -->|"stdio (JSON-RPC)"| M[mcp_server.py\nFastMCP · 956 lines]
    M -->|subprocess| P[obs_cli.py]
    M -->|"direct Python\nimport"| VM[VaultManager]
    M -->|"direct Python\nimport"| GA[GraphAnalyzer]
    M --> RES["4 MCP Resources\nvault://{id}/stats\nnote://{id}\nobsidian://overview\n..."]
```

- **20 MCP tools** in 6 groups: Vault (3), Search (2), Graph (4), Health (1), Notes (9), AI (1)
- **FastMCP** (`from mcp.server.fastmcp import FastMCP`) — stdio transport, clean exit when no client
- Note write tools include built-in safety: `delete_note` defaults `confirm=False` (dry-run), `write_note` defaults `create_backup=True`

### Application Layer (Core)

```mermaid
flowchart TD
    VM[VaultManager] -->|scan, discover, list| VS[VaultScanner]
    VM -->|CRUD operations| DB[DatabaseManager]
    GA[GraphAnalyzer] -->|PageRank, centrality| GB[GraphBuilder]
    GA -->|read metrics| DB
    DM[Domain Models] -->|"Vault, Note, ScanResult\nGraphMetrics, VaultStats"| VM
    DM --> GA
```

- **VaultManager** — vault discovery, scanning, database registration, stats
- **GraphAnalyzer** — graph metrics, hub detection, orphan detection, clustering
- **Domain Models** — typed dataclasses with `from_dict()`, `to_dict()`, `from_json()`

### AI Features Layer

```mermaid
flowchart TD
    AR[AIRouter\nSmart fallback] -->|priority chain| P1[gemini-api]
    AR --> P2[anthropic-api]
    AR --> P3[ollama]
    AR --> P4[gemini-cli]
    AR --> P5[claude-cli]

    FT[features.py\nCore AI] -->|similar, analyze\nduplicates, gaps| AR
    FV[features_vault.py\nVault AI] -->|merge-suggest\ntag-suggest, quality| DB[(SQLite)]
    FR[features_refactor.py\nRefactor] -->|plan generation| AR
    OB[ObsidianBridge\nNull Object] -->|safe fallback| FT
```

- All providers implement a common `AIProvider` interface and return identical dataclass types
- Embedding cache in `note_embeddings` SQLite table with mtime invalidation
- **ObsidianBridge** uses Null Object pattern: returns empty results when Obsidian CLI is unavailable (never crashes)

### Data Layer

```mermaid
flowchart LR
    DB[DatabaseManager\n469 lines] -->|CRUD| SQ[(vault_db.sqlite)]
    VS[VaultScanner\n373 lines] -->|parse .md files| FS[Vault Files]
    VS -->|INSERT notes, links, tags| DB
    GB[GraphBuilder\n307 lines] -->|NetworkX graph| SQ
    SQ --- T1[vaults]
    SQ --- T2[notes]
    SQ --- T3[links]
    SQ --- T4[tags]
    SQ --- T5[graph_metrics]
    SQ --- T6[note_embeddings]
```

---

## Key Data Flows

### Vault Scan

```mermaid
sequenceDiagram
    participant U as User
    participant Z as obs.zsh
    participant P as obs_cli.py
    participant VM as VaultManager
    participant VS as VaultScanner
    participant DB as DatabaseManager
    participant FS as .md Files

    U->>Z: obs scan /vault
    Z->>P: subprocess call
    P->>VM: scan_vault(path)
    VM->>VS: scan_vault(path)
    VS->>FS: read all .md files
    FS-->>VS: note content, wikilinks
    VS->>DB: INSERT notes, links, tags
    DB-->>VS: row IDs
    VS-->>VM: ScanResult
    VM-->>P: ScanResult
    P-->>U: "Scanned 847 notes"
```

### MCP Tool Call (note creation via Claude)

```mermaid
sequenceDiagram
    participant C as Claude Desktop
    participant M as mcp_server.py
    participant P as obs_cli.py
    participant VM as VaultManager
    participant FS as .md Files

    C->>M: create_note(vault_id, title, content)
    M->>P: subprocess: obs_cli create-note ...
    P->>VM: create_note(vault_id, title, content)
    VM->>FS: write title.md
    FS-->>VM: success
    VM-->>P: NoteCreateResult
    P-->>M: JSON result
    M-->>C: tool response
```

### AI Suggest-Links

```mermaid
sequenceDiagram
    participant P as obs_cli.py
    participant FT as features.py
    participant DB as DatabaseManager
    participant AR as AIRouter
    participant PR as AI Provider

    P->>FT: suggest_links(note_id, db)
    FT->>DB: get_note_embedding(note_id)
    alt Embedding cached
        DB-->>FT: cached embedding vector
    else Not cached
        FT->>AR: embed(note_content)
        AR->>PR: generate_embedding(text)
        PR-->>AR: embedding vector
        AR-->>FT: embedding
        FT->>DB: cache embedding
    end
    FT->>DB: get_all_embeddings(vault_id)
    DB-->>FT: candidate embeddings
    FT->>FT: cosine similarity, filter existing links
    FT-->>P: List[SimilarNote] top-N
```

---

## Design Patterns

| Pattern | Where Used |
|---------|-----------|
| **Repository** | `DatabaseManager` wraps all SQLite operations |
| **Facade** | `VaultManager` / `GraphAnalyzer` simplify complex multi-step operations |
| **Factory** | `from_db_row()` class methods on every domain model |
| **Dependency Injection** | Core classes accept an optional `DatabaseManager` |
| **Null Object** | `ObsidianBridge` returns empty results when Obsidian CLI unavailable |
| **Strategy** | `AIRouter` selects among 5 interchangeable provider strategies |
| **Adapter** | Each AI provider adapts a different API to the common `AIProvider` interface |

---

## File Structure

```
src/python/
  core/                      # APPLICATION LAYER
    vault_manager.py         # Vault operations (~400 lines)
    graph_analyzer.py        # Graph operations (~350 lines)
    models.py                # Domain models (~310 lines)
    exceptions.py            # Custom exceptions

  ai/                        # AI FEATURES LAYER
    features.py              # Core AI: similar, analyze, duplicates, suggest-links, gaps, summarize
    features_vault.py        # Vault AI: merge-suggest, tag-suggest, quality (v3.2.0)
    features_refactor.py     # Refactor pipeline (extracted v3.2.0)
    router.py                # Smart provider selection + fallback chain
    models.py                # AI dataclasses: AnalysisResult, SimilarNote, MergeCandidate, TagSuggestion, NoteQuality...
    obsidian_bridge.py       # Null Object bridge to Obsidian CLI
    providers/               # 5 provider implementations

  mcp_server.py              # MCP INTEGRATION LAYER (v3.3.0, 956 lines)
  obs_cli.py                 # PRESENTATION LAYER (985 lines)
  db_manager.py              # DATA LAYER: SQLite CRUD
  vault_scanner.py           # DATA LAYER: .md file parsing
  graph_builder.py           # DATA LAYER: NetworkX graph construction

src/obs.zsh                  # PRESENTATION LAYER: ZSH dispatcher (501 lines)
schema/vault_db.sql          # Database schema
```

---

## Testing

- **304 pytest tests** covering core, AI, vault features, data layer, and MCP server
- **69 Jest tests** for ZSH wrapper + dependency-bootstrapping validation
- Core layer tested independently with mocked dependencies
- AI providers mocked for deterministic tests
- MCP tools tested via FastMCP test client

See [Testing Overview](testing/overview.md) for full details.
