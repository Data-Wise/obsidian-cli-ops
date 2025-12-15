---
paths:
  - "src/python/core/**"
  - "src/python/tui/**"
  - "src/python/obs_cli.py"
  - "src/python/db_manager.py"
  - "src/python/vault_scanner.py"
  - "src/python/graph_builder.py"
---

# Architecture Rules

## Three-Layer Design

Obsidian CLI Ops follows a clean three-layer architecture that separates presentation, business logic, and data access. This design enables multiple interfaces (CLI, TUI, GUI) to share the same core logic without duplication.

```
┌─────────────────────────────────────────────────┐
│         PRESENTATION LAYER                      │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐     │
│  │   CLI    │  │   TUI    │  │   GUI    │     │
│  │(obs_cli) │  │(Textual) │  │ (Future) │     │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘     │
└───────┼─────────────┼─────────────┼───────────┘
        │             │             │
        └─────────────┼─────────────┘
                      │
┌─────────────────────▼─────────────────────────┐
│         APPLICATION LAYER (CORE)              │
│  ┌──────────────────────────────────────┐    │
│  │  VaultManager                        │    │
│  │  - discover_vaults()                 │    │
│  │  - scan_vault()                      │    │
│  │  - list_vaults()                     │    │
│  │  - get_vault_stats()                 │    │
│  │                                      │    │
│  │  GraphAnalyzer                       │    │
│  │  - analyze_vault()                   │    │
│  │  - calculate_metrics()               │    │
│  │  - find_clusters()                   │    │
│  │  - get_hub_notes()                   │    │
│  │                                      │    │
│  │  Domain Models                       │    │
│  │  - Vault, Note, ScanResult          │    │
│  │  - GraphMetrics, VaultStats          │    │
│  └──────────────────────────────────────┘    │
└─────────────────────▼─────────────────────────┘
                      │
┌─────────────────────▼─────────────────────────┐
│         DATA LAYER                            │
│  ┌──────────────────────────────────────┐    │
│  │  DatabaseManager                     │    │
│  │  VaultScanner                        │    │
│  │  GraphBuilder                        │    │
│  │  MarkdownParser                      │    │
│  └──────────────────────────────────────┘    │
└───────────────────────────────────────────────┘
```

## Layer 1: Presentation (Interfaces)

**Location:** `src/obs.zsh`, `src/python/obs_cli.py`, `src/python/tui/`

- **ZSH CLI** (`src/obs.zsh`): Shell integration, v1.x commands, wrapper for Python CLI
- **Python CLI** (`src/python/obs_cli.py`): Argparse-based CLI for v2.0 commands
- **TUI** (`src/python/tui/`): Textual-based interactive interface
- **GUI** (planned): Future graphical interface

**Responsibilities:**
- Handle user input (keyboard, mouse, CLI arguments)
- Format output for specific interface (text, colors, widgets)
- No business logic - just presentation
- Call application layer methods
- Display errors and results

## Layer 2: Application (Core Business Logic)

**Location:** `src/python/core/`

### VaultManager (vault_manager.py, 311 lines)
- Vault discovery and validation
- Scanning orchestration
- Vault CRUD operations
- Statistics aggregation
- Interface-agnostic business logic

**Key methods:**
- `discover_vaults(root_path)`: Find Obsidian vaults in directory tree
- `list_vaults()`: Get all registered vaults
- `get_vault(vault_id)`: Get vault by ID
- `scan_vault(path, name, force)`: Scan vault and return ScanResult
- `get_vault_stats(vault_id)`: Get statistical summary
- `get_notes(vault_id, limit, offset)`: Get notes from vault
- `search_notes(vault_id, query)`: Search notes by title/content
- `delete_vault(vault_id)`: Remove vault from database

### GraphAnalyzer (graph_analyzer.py, 311 lines)
- Graph analysis orchestration
- Metrics calculation
- Hub/orphan detection
- Cluster finding
- Link resolution

**Key methods:**
- `analyze_vault(vault_id)`: Complete graph analysis pipeline
- `get_graph(vault_id)`: Build NetworkX graph
- `get_note_metrics(note_id)`: Get graph metrics for note
- `get_hub_notes(vault_id)`: Get highly connected notes
- `get_orphan_notes(vault_id)`: Get isolated notes
- `get_broken_links(vault_id)`: Get unresolved wikilinks
- `calculate_metrics(vault_id)`: Calculate PageRank, centrality
- `resolve_links(vault_id)`: Resolve wikilinks to note IDs
- `find_clusters(vault_id)`: Detect communities in graph
- `get_ego_graph(note_id, radius)`: Get local neighborhood

### Domain Models (models.py, 237 lines)
- `Vault`: Vault metadata (id, name, path, counts, timestamps)
- `Note`: Note content and metadata (title, path, word_count, tags, links)
- `ScanResult`: Scan operation results (notes scanned, links found, duration, errors)
- `GraphMetrics`: Graph analysis metrics (PageRank, centrality, clustering)
- `VaultStats`: Statistical summaries (totals, averages, graph density)
- All models have `from_db_row()`, `to_dict()`, `to_json()` methods

### Custom Exceptions (exceptions.py)
- `VaultNotFoundError`: Vault doesn't exist or path invalid
- `ScanError`: Scan operation failed
- `AnalysisError`: Graph analysis failed

## Layer 3: Data (Persistence & I/O)

**Location:** `src/python/` (db_manager.py, vault_scanner.py, etc.)

- **DatabaseManager**: SQLite operations
- **VaultScanner**: File system scanning
- **GraphBuilder**: NetworkX graph construction
- **MarkdownParser**: Markdown parsing
- **AI Clients**: Embeddings and similarity

**Responsibilities:**
- Database queries and updates
- File system I/O
- External API calls
- No business logic
- Returns raw data

## Benefits of Three-Layer Architecture

1. **Code Reusability**: CLI and TUI share 100% of business logic
2. **Easy Testing**: Core layer can be tested independently
3. **Flexible Interfaces**: Add GUI without changing business logic
4. **Clear Separation**: Each layer has single responsibility
5. **Type Safety**: Domain models provide type checking
6. **Maintainability**: Changes in one layer don't affect others

## How CLI and TUI Share Core Logic

The three-layer architecture enables CLI and TUI to share 100% of business logic:

```python
# Core layer (interface-agnostic business logic)
from core.vault_manager import VaultManager

vault_manager = VaultManager()
result = vault_manager.scan_vault("/path/to/vault")
```

```python
# CLI implementation (formats result as text)
def scan_command(args):
    vault_manager = VaultManager()
    result = vault_manager.scan_vault(args.path)

    # CLI-specific formatting
    print(f"✓ Scanned {result.notes_scanned} notes")
    print(f"✓ Found {result.links_found} links")
    print(f"✓ Took {result.duration_seconds:.2f}s")
```

```python
# TUI implementation (displays result in widgets)
class VaultBrowserScreen(Screen):
    def on_scan_clicked(self):
        vault_manager = VaultManager()
        result = vault_manager.scan_vault(self.vault_path)

        # TUI-specific display
        self.update_status_label(
            f"Scanned {result.notes_scanned} notes in {result.duration_seconds:.2f}s"
        )
        self.refresh_vault_list()
```

**Key points:**
- Same `vault_manager.scan_vault()` call in both
- Same `result` object with structured data
- Different presentation: CLI prints text, TUI updates widgets
- Zero business logic duplication

## Module Structure

```
src/python/
├── __init__.py                # Package initialization
│
├── core/                      # APPLICATION LAYER (859 lines)
│   ├── __init__.py            # Core package initialization
│   ├── vault_manager.py       # Vault business logic (311 lines)
│   ├── graph_analyzer.py      # Graph business logic (311 lines)
│   ├── models.py              # Domain models (237 lines)
│   └── exceptions.py          # Custom exceptions
│
├── tui/                       # PRESENTATION LAYER - TUI (1,701 lines)
│   ├── __init__.py
│   ├── app.py                 # Main TUI application (282 lines)
│   ├── screens/
│   │   ├── __init__.py
│   │   ├── vaults.py          # Vault browser (267 lines)
│   │   ├── notes.py           # Note explorer (378 lines)
│   │   ├── graph.py           # Graph visualizer (378 lines)
│   │   └── stats.py           # Statistics dashboard (420 lines)
│   └── widgets/
│       └── __init__.py
│
├── obs_cli.py                 # PRESENTATION LAYER - CLI (318 lines)
│
├── db_manager.py              # DATA LAYER - Database (469 lines)
├── vault_scanner.py           # DATA LAYER - File scanning (373 lines)
├── graph_builder.py           # DATA LAYER - Graph construction (307 lines)
│
├── ai_client.py               # AI client base & factory (440 lines)
├── ai_client_ollama.py        # Ollama integration (450 lines)
├── ai_client_hf.py            # HuggingFace integration (340 lines)
├── setup_wizard.py            # Interactive AI setup (837 lines)
├── similarity_analyzer.py     # Note similarity analysis (470 lines)
│
├── requirements.txt           # Python dependencies
└── README.md                  # Python module documentation
```

## Key Implementation Details

### Vault Scanning (v2.0)
1. Discovers vaults by searching for `.obsidian` directories
2. Parses markdown files with `python-frontmatter` library
3. Extracts wikilinks using regex: `\[\[([^\]|]+)(?:\|([^\]]+))?\]\]`
4. Extracts tags using regex: `#([a-zA-Z0-9_/-]+)`
5. Stores content hash (SHA256) for change detection
6. Populates database with notes, links, tags

### Link Resolution (v2.0)
1. Builds cache of note paths, titles, and aliases
2. Resolves wikilinks by trying multiple strategies:
   - Exact path match
   - Path without `.md` extension
   - Relative path from source note
   - Filename only match
3. Updates links table with resolved `target_note_id`
4. Marks unresolved links as `broken`

### Graph Analysis (v2.0)
1. Constructs NetworkX `DiGraph` from database links
2. Calculates metrics:
   - **PageRank**: Importance score based on link structure
   - **In/Out Degree**: Number of incoming/outgoing links
   - **Betweenness Centrality**: How often note is on path between others
   - **Closeness Centrality**: Average distance to all other notes
   - **Clustering Coefficient**: How connected note's neighbors are
3. Updates `graph_metrics` table
4. Identifies special notes (orphans, hubs)

## Adding a New Interface (GUI Example)

Because business logic is in the core layer, adding a GUI is straightforward:

```python
# gui/main_window.py (Future)
from PySide6.QtWidgets import QMainWindow, QPushButton
from core.vault_manager import VaultManager

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.vault_manager = VaultManager()  # Same core logic!

    def on_scan_clicked(self):
        result = self.vault_manager.scan_vault(self.vault_path)

        # GUI-specific display
        QMessageBox.information(
            self,
            "Scan Complete",
            f"Scanned {result.notes_scanned} notes\n"
            f"Found {result.links_found} links"
        )
```

**No changes needed to VaultManager!** Just create new presentation layer.
