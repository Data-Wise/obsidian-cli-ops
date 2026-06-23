# API Reference

**Version:** 4.0.0

Reference documentation for the MCP tool API, Python CLI API, AI provider interface, and domain models.

---

## MCP Server API (v3.3.0)

The MCP server (`src/python/mcp_server.py`) exposes 39 tools and 4 resources over stdio to Claude Desktop, Claude Code, and Cowork.

### Connection Flow

```mermaid
flowchart LR
    C([Claude Host]) -->|"stdio (JSON-RPC 2.0)"| M[mcp_server.py\nFastMCP]
    M -->|"tools/list"| C
    M -->|"tools/call"| T[Tool handler]
    T -->|subprocess| OBS[obs_cli.py]
    T -->|direct import| CORE[Core / AI modules]
    OBS -->|JSON| T
    CORE -->|dataclass| T
    T -->|JSON result| M
    M -->|result| C
```

### MCP Tool Groups

#### Vault Tools

| Tool | Args | Returns |
|------|------|---------|
| `list_vaults()` | — | `[{id, name, path, note_count, ...}]` |
| `get_vault_stats(vault_id)` | `vault_id: str` | `{notes, links, tags, density, clusters, ...}` |
| `rescan_vault(vault_id)` | `vault_id: str` | `{notes_scanned, links_found, duration_s}` |

#### Search Tools

| Tool | Args | Returns |
|------|------|---------|
| `search_notes(query, vault_id?, limit?)` | `query: str`; optional `vault_id`, `limit` (default 10) | `[{id, title, snippet, score}]` |
| `list_notes(vault_id, limit?)` | `vault_id: str`; optional `limit` | `[{id, title, path, word_count, tags}]` |

#### Graph Tools

| Tool | Args | Returns |
|------|------|---------|
| `get_hub_notes(vault_id, limit?)` | `vault_id: str`; optional `limit` (default 10) | `[{id, title, pagerank, degree}]` |
| `get_orphaned_notes(vault_id, limit?)` | `vault_id: str`; optional `limit` | `[{id, title, word_count, modified_at}]` |
| `analyze_vault(vault_id)` | `vault_id: str` | `{density, avg_degree, clusters, diameter, hub_notes, ...}` |
| `find_similar_notes(note_id, limit?)` | `note_id: str`; optional `limit` | `[{id, title, similarity_score}]` |

#### Health Tool

| Tool | Args | Returns |
|------|------|---------|
| `get_vault_health(vault_id)` | `vault_id: str` | `{overall, connectivity, link_integrity, structure, freshness, issues: [...]}` |

#### Note CRUD Tools

```mermaid
flowchart TD
    subgraph Read["Read (safe)"]
        RN[read_note\nnote_id]
        GL[get_note_links\nnote_id]
    end
    subgraph Write["Write (modifies files)"]
        CN[create_note\nvault_id, title, content]
        WN[write_note\nnote_id, content\ncreate_backup=True]
        AN[append_to_note\nnote_id, content]
        RNN[rename_note\nnote_id, new_title]
        DN[delete_note\nnote_id\nconfirm=False ← dry-run]
    end
    subgraph Meta["Metadata"]
        TNT[get_note_tags\nnote_id]
        STT[set_note_tags\nnote_id, tags]
    end

    style Read fill:#22c55e,color:#000
    style Write fill:#f59e0b,color:#000
    style Meta fill:#6366f1,color:#fff
```

| Tool | Default Safety | Effect |
|------|---------------|--------|
| `read_note(note_id)` | — (read-only) | Returns full note content + frontmatter |
| `get_note_links(note_id)` | — (read-only) | Returns `{incoming: [...], outgoing: [...]}` |
| `get_note_tags(note_id)` | — (read-only) | Returns `[tag1, tag2, ...]` |
| `create_note(vault_id, title, content?)` | — | Creates new `.md` file |
| `write_note(note_id, content, create_backup?)` | `create_backup=True` | Overwrites; auto-creates `.bak` |
| `append_to_note(note_id, content)` | — | Appends to end of file |
| `rename_note(note_id, new_title)` | — | Renames file; warns on broken backlinks |
| `delete_note(note_id, confirm?)` | `confirm=False` (dry-run) | Requires `confirm=True` to actually delete |
| `set_note_tags(note_id, tags)` | — | Updates YAML frontmatter tags |

#### AI Passthrough Tool

| Tool | Args | Returns |
|------|------|---------|
| `run_obs_ai(command, target, options?)` | `command: str` (e.g. `"gaps"`, `"quality"`); `target: str`; optional `options: dict` | Command-specific JSON (see below) |

Valid `command` values:

| command | target | Returns |
|---------|--------|---------|
| `"gaps"` | vault_id | `{gaps: [{topic, references, suggested_title}]}` |
| `"quality"` | vault_id or note_id | `{notes: [{title, overall_score, completeness, connectivity, metadata, freshness}]}` |
| `"merge-suggest"` | vault_id | `[{note_a_id, note_b_id, similarity, shared_links, shared_tags}]` |
| `"tag-suggest"` | vault_id or note_id | `{suggestions: [{note_id, tags: [{tag, confidence}]}]}` |
| `"refactor"` | vault_id | `{suggestions: [{category, priority, description, affected_paths}]}` |
| `"summarize"` | vault_id | `{themes: [...], key_notes: [...], summary: "..."}` |

### MCP Resources

```mermaid
flowchart LR
    C([Claude Host]) -->|"resources/read"| M[mcp_server.py]
    M --> R1["vault://{vault_id}/stats\n→ same as get_vault_stats"]
    M --> R2["vault://{vault_id}/health\n→ same as get_vault_health"]
    M --> R3["obsidian://overview\n→ all vaults summary"]
    M --> R4["note://{note_id}\n→ same as read_note"]
```

Resources are read-only and do not modify vault state.

---

## Python CLI API (`obs_cli.py`)

The Python CLI is the canonical interface between the presentation layers and the core. All MCP tools ultimately invoke it via subprocess or direct import.

### Invocation Pattern

```mermaid
flowchart LR
    Z[obs.zsh] -->|"$PYTHON obs_cli.py subcommand [args] [--json]"| P[obs_cli.py]
    M[mcp_server.py] -->|"subprocess.run(['python', 'obs_cli.py', ...])"| P
    P -->|argparse| C[Core / AI]
    C -->|dataclass| P
    P -->|Rich table\nor --json| OUT[stdout]
```

### Subcommand Map

```mermaid
flowchart TD
    P[obs_cli.py] --> V[vault subcommands]
    P --> G[graph subcommands]
    P --> A[ai subcommands]
    P --> DB[db subcommands]

    V --> V1[list-vaults]
    V --> V2[scan PATH]
    V --> V3[discover PATH --scan]
    V --> V4[stats --vault NAME]
    V --> V5[health VAULT]
    V --> V6[analyze VAULT]

    G --> G1[hubs VAULT]
    G --> G2[orphans VAULT]

    A --> A1[ai status / setup / test]
    A --> A2[ai similar NOTE_ID]
    A --> A3[ai analyze NOTE_ID]
    A --> A4[ai duplicates VAULT]
    A --> A5[ai suggest-links NOTE_ID]
    A --> A6[ai gaps VAULT]
    A --> A7[ai summarize VAULT]
    A --> A8[ai refactor VAULT]
    A --> A9[ai merge-suggest VAULT]
    A --> A10[ai tag-suggest TARGET]
    A --> A11[ai quality TARGET]

    DB --> DB1[db init]
```

### `--json` Flag

All data commands accept `--json` for machine-readable output (used by MCP tools and scripting):

```python
# obs_cli.py pattern
if args.json:
    print(json.dumps(result.to_dict(), indent=2))
else:
    console.print(rich_table)
```

---

## Core Python API

### VaultManager

```mermaid
classDiagram
    class VaultManager {
        +db: DatabaseManager
        +discover_vaults(path: str) → List[Vault]
        +scan_vault(path: str) → ScanResult
        +list_vaults() → List[Vault]
        +get_vault(vault_id: str) → Vault
        +get_vault_stats(vault_id: str) → VaultStats
        +create_note(vault_id, title, content) → Note
        +read_note(note_id: str) → Note
        +write_note(note_id, content, backup) → Note
        +append_to_note(note_id, content) → Note
        +rename_note(note_id, new_title) → Note
        +delete_note(note_id, confirm) → DeleteResult
        +get_note_tags(note_id) → List[str]
        +set_note_tags(note_id, tags) → Note
    }
```

### GraphAnalyzer

```mermaid
classDiagram
    class GraphAnalyzer {
        +db: DatabaseManager
        +analyze_vault(vault_id: str) → GraphMetrics
        +get_hub_notes(vault_id, limit) → List[Note]
        +get_orphaned_notes(vault_id, limit) → List[Note]
        +get_note_links(note_id) → LinkResult
        +get_vault_health(vault_id) → HealthResult
        +find_similar_notes(note_id, limit) → List[SimilarNote]
    }
```

---

## AI Provider Interface

```mermaid
flowchart TD
    AR[AIRouter] -->|"provider_priority list"| P1[GeminiAPIProvider]
    AR --> P2[AnthropicAPIProvider]
    AR --> P3[OllamaProvider]
    AR --> P4[GeminiCLIProvider]
    AR --> P5[ClaudeCLIProvider]

    subgraph Interface["AIProvider interface"]
        IA[is_available() → bool]
        CT[complete(prompt: str) → str]
        EM[embed(text: str) → List[float]]
    end

    P1 -.implements.-> Interface
    P2 -.implements.-> Interface
    P3 -.implements.-> Interface
    P4 -.implements.-> Interface
    P5 -.implements.-> Interface
```

**Fallback logic:**

```mermaid
flowchart LR
    AR[AIRouter] --> C1{gemini-api\navailable?}
    C1 -->|Yes| P1[GeminiAPI]
    C1 -->|No| C2{anthropic-api?}
    C2 -->|Yes| P2[AnthropicAPI]
    C2 -->|No| C3{ollama?}
    C3 -->|Yes| P3[Ollama]
    C3 -->|No| C4{gemini-cli?}
    C4 -->|Yes| P4[GeminiCLI]
    C4 -->|No| P5[ClaudeCLI]
```

---

## Domain Models

### Core Models

```mermaid
classDiagram
    class Vault {
        +id: str
        +name: str
        +path: str
        +note_count: int
        +link_count: int
        +last_scanned: datetime
        +from_db_row() Vault$
        +to_dict() dict
    }

    class Note {
        +id: str
        +vault_id: str
        +title: str
        +path: str
        +word_count: int
        +tags: List[str]
        +created_at: datetime
        +modified_at: datetime
        +content: str
        +from_db_row() Note$
        +to_dict() dict
    }

    class GraphMetrics {
        +vault_id: str
        +density: float
        +avg_degree: float
        +cluster_count: int
        +hub_notes: List[Note]
        +orphan_count: int
    }

    class VaultStats {
        +vault: Vault
        +graph: GraphMetrics
        +top_tags: List[TagCount]
        +broken_links: int
    }

    class HealthResult {
        +overall: int
        +connectivity: int
        +link_integrity: int
        +structure: int
        +freshness: int
        +issues: List[HealthIssue]
    }

    Vault "1" --> "n" Note
    VaultStats --> Vault
    VaultStats --> GraphMetrics
```

### AI Models

```mermaid
classDiagram
    class SimilarNote {
        +note: Note
        +similarity_score: float
    }

    class MergeCandidate {
        +note_a: Note
        +note_b: Note
        +similarity: float
        +shared_links: List[str]
        +shared_tags: List[str]
    }

    class TagSuggestion {
        +note: Note
        +tags: List[TagWithConfidence]
    }

    class NoteQuality {
        +note: Note
        +overall_score: float
        +completeness: float
        +connectivity: float
        +metadata: float
        +freshness: float
    }

    class RefactorPlan {
        +suggestions: List[RefactorSuggestion]
    }

    class RefactorSuggestion {
        +category: str
        +priority: str
        +description: str
        +affected_paths: List[str]
    }

    RefactorPlan --> RefactorSuggestion
```

---

## Database Schema

```mermaid
erDiagram
    vaults {
        text id PK
        text name
        text path
        integer note_count
        text last_scanned
    }

    notes {
        text id PK
        text vault_id FK
        text title
        text path
        integer word_count
        text created_at
        text modified_at
    }

    links {
        integer id PK
        text source_note_id FK
        text target_note_id FK
        text link_type
    }

    tags {
        integer id PK
        text note_id FK
        text tag_name
    }

    graph_metrics {
        integer id PK
        text vault_id FK
        real density
        real avg_degree
        integer cluster_count
        text computed_at
    }

    note_embeddings {
        text note_id PK
        blob embedding
        text model_id
        text computed_at
    }

    scan_history {
        integer id PK
        text vault_id FK
        integer notes_scanned
        integer duration_ms
        text scanned_at
    }

    vaults ||--o{ notes : "has"
    notes ||--o{ links : "source"
    notes ||--o{ tags : "has"
    notes ||--o| note_embeddings : "cached in"
    vaults ||--o{ graph_metrics : "has"
    vaults ||--o{ scan_history : "tracked in"
```

---

## Error Handling

All public API methods raise typed exceptions from `src/python/core/exceptions.py`:

| Exception | When Raised |
|-----------|-------------|
| `VaultNotFoundError` | `vault_id` not registered in database |
| `NoteNotFoundError` | `note_id` not found in database |
| `VaultScanError` | Filesystem errors during scanning |
| `AIProviderError` | All AI providers unavailable |
| `DatabaseError` | SQLite operation failure |

MCP tools catch all exceptions and return structured error JSON rather than propagating to the stdio transport.

---

## See Also

- [Architecture](architecture.md) — layer diagrams and data flows
- [Claude Integration](../claude-integration.md) — MCP setup guide with all 39 tools
- [Testing Overview](testing/overview.md) — test strategy and coverage
