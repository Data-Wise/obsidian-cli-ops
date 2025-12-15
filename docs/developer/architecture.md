# Architecture Documentation

**Project:** Obsidian CLI Ops (obs)
**Version:** 2.0.0-beta
**Last Updated:** 2025-12-15

---

## Table of Contents

1. [Overview](#overview)
2. [Three-Layer Architecture](#three-layer-architecture)
3. [Layer Details](#layer-details)
4. [Data Flow](#data-flow)
5. [Design Patterns](#design-patterns)
6. [Benefits](#benefits)
7. [How to Add New Interfaces](#how-to-add-new-interfaces)
8. [Code Examples](#code-examples)
9. [Testing Strategy](#testing-strategy)
10. [Migration Guide](#migration-guide)

---

## Overview

Obsidian CLI Ops follows a clean **three-layer architecture** that separates:
- **Presentation** (UI/CLI/TUI)
- **Application** (business logic)
- **Data** (persistence)

This architecture enables multiple user interfaces (CLI, TUI, GUI) to share the same core business logic without duplication.

### Architecture Goals

1. **Code Reusability:** CLI and TUI share 100% of business logic
2. **Testability:** Core layer can be tested independently of UI
3. **Flexibility:** Easy to add new interfaces (GUI, web API, mobile)
4. **Maintainability:** Clear separation of concerns
5. **Type Safety:** Domain models provide compile-time checking

---

## Three-Layer Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    PRESENTATION LAYER                       │
│                                                             │
│  ┌───────────┐    ┌───────────┐    ┌───────────┐          │
│  │           │    │           │    │           │          │
│  │    CLI    │    │    TUI    │    │    GUI    │          │
│  │           │    │           │    │           │          │
│  │ obs_cli.py│    │  Textual  │    │  (Future) │          │
│  │           │    │   app.py  │    │           │          │
│  └─────┬─────┘    └─────┬─────┘    └─────┬─────┘          │
│        │                │                │                │
│        └────────────────┼────────────────┘                │
│                         │                                 │
└─────────────────────────┼─────────────────────────────────┘
                          │
                          │ Uses
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                   APPLICATION LAYER (CORE)                  │
│                                                             │
│  ┌───────────────────────────────────────────────────┐     │
│  │                                                   │     │
│  │           VaultManager (311 lines)                │     │
│  │    - discover_vaults()                            │     │
│  │    - scan_vault() → ScanResult                    │     │
│  │    - list_vaults() → List[Vault]                  │     │
│  │    - get_vault_stats() → VaultStats               │     │
│  │                                                   │     │
│  │           GraphAnalyzer (311 lines)               │     │
│  │    - analyze_vault() → Dict                       │     │
│  │    - calculate_metrics()                          │     │
│  │    - get_hub_notes() → List[Dict]                 │     │
│  │    - get_orphan_notes() → List[Dict]              │     │
│  │                                                   │     │
│  │           Domain Models (237 lines)               │     │
│  │    - Vault, Note, ScanResult                      │     │
│  │    - GraphMetrics, VaultStats                     │     │
│  │                                                   │     │
│  │           Custom Exceptions                       │     │
│  │    - VaultNotFoundError                           │     │
│  │    - ScanError, AnalysisError                     │     │
│  │                                                   │     │
│  └───────────────────────────────────────────────────┘     │
│                         │                                  │
└─────────────────────────┼──────────────────────────────────┘
                          │
                          │ Uses
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                       DATA LAYER                            │
│                                                             │
│  ┌───────────────────────────────────────────────────┐     │
│  │                                                   │     │
│  │    DatabaseManager (469 lines)                    │     │
│  │    - get_connection()                             │     │
│  │    - add_vault(), get_vault(), list_vaults()      │     │
│  │    - add_note(), get_note(), list_notes()         │     │
│  │    - get_orphaned_notes(), get_hub_notes()        │     │
│  │                                                   │     │
│  │    VaultScanner (373 lines)                       │     │
│  │    - discover_vaults()                            │     │
│  │    - scan_vault()                                 │     │
│  │    - MarkdownParser                               │     │
│  │                                                   │     │
│  │    GraphBuilder (307 lines)                       │     │
│  │    - build_graph() → nx.DiGraph                   │     │
│  │    - calculate_metrics()                          │     │
│  │    - find_clusters()                              │     │
│  │    - LinkResolver                                 │     │
│  │                                                   │     │
│  └───────────────────────────────────────────────────┘     │
│                                                             │
└─────────────────────────────────────────────────────────────┘
                          │
                          │ Stores
                          ▼
                ┌──────────────────────┐
                │   SQLite Database    │
                │  vault_db.sqlite     │
                └──────────────────────┘
```

---

## Layer Details

### Layer 1: Presentation (Interfaces)

**Location:** `src/obs.zsh`, `src/python/obs_cli.py`, `src/python/tui/`

**Purpose:** Handle user interaction and format output

**Components:**

1. **ZSH CLI** (`src/obs.zsh`, 680 lines)
   - Shell integration
   - v1.x features (sync, install, r-dev)
   - Wrapper for Python CLI

2. **Python CLI** (`src/python/obs_cli.py`, 318 lines)
   - Argparse-based command line
   - v2.0 features (discover, analyze, stats)
   - JSON output support
   - Verbose mode

3. **TUI** (`src/python/tui/`, 1,701 lines)
   - Textual framework
   - Interactive screens: Vaults, Notes, Graph, Stats
   - Real-time updates
   - Keyboard navigation (vim keys)

4. **GUI** (planned, future)
   - PySide6/Qt framework
   - Visual graph exploration
   - Point-and-click operations

**Responsibilities:**
- Parse user input (CLI args, keyboard, mouse)
- Format output (text, colors, widgets, dialogs)
- Display errors with context
- Call application layer methods
- **NO business logic**

**Example:**

```python
# CLI presentation
def scan_command(args):
    result = vault_manager.scan_vault(args.path)  # Core layer
    print(f"✓ Scanned {result.notes_scanned} notes")  # Presentation

# TUI presentation
class VaultBrowserScreen(Screen):
    def on_scan_clicked(self):
        result = vault_manager.scan_vault(self.vault_path)  # Core layer
        self.update_status(result)  # Presentation
```

---

### Layer 2: Application (Core Business Logic)

**Location:** `src/python/core/`

**Purpose:** Interface-agnostic business logic

**Components:**

#### 1. VaultManager (`vault_manager.py`, 311 lines)

**Orchestrates vault operations:**

```python
class VaultManager:
    def discover_vaults(self, root_path: str) -> List[str]:
        """Find Obsidian vaults in directory tree."""

    def scan_vault(self, path: str, name: str = None) -> ScanResult:
        """Scan vault and return results."""

    def list_vaults(self) -> List[Vault]:
        """Get all registered vaults."""

    def get_vault_stats(self, vault_id: str) -> VaultStats:
        """Get statistical summary."""
```

**Key features:**
- Validates vault paths
- Coordinates scanning process
- Aggregates statistics
- Returns structured results (ScanResult, VaultStats)
- Raises domain-specific exceptions

#### 2. GraphAnalyzer (`graph_analyzer.py`, 311 lines)

**Orchestrates graph analysis:**

```python
class GraphAnalyzer:
    def analyze_vault(self, vault_id: str) -> Dict[str, Any]:
        """Complete graph analysis pipeline."""

    def calculate_metrics(self, vault_id: str) -> Dict[str, Any]:
        """Calculate PageRank, centrality, etc."""

    def get_hub_notes(self, vault_id: str) -> List[Dict]:
        """Get highly connected notes."""

    def get_orphan_notes(self, vault_id: str) -> List[Dict]:
        """Get isolated notes."""

    def find_clusters(self, vault_id: str) -> List[Set[str]]:
        """Detect communities in graph."""

    def get_ego_graph(self, note_id: str, radius: int) -> nx.DiGraph:
        """Get local neighborhood."""
```

**Key features:**
- Coordinates link resolution, metrics, clustering
- Returns structured data (GraphMetrics)
- Works with NetworkX graphs
- No presentation logic

#### 3. Domain Models (`models.py`, 237 lines)

**Type-safe business entities:**

```python
@dataclass
class Vault:
    id: str
    name: str
    path: str
    note_count: int
    link_count: int
    # ... more fields ...

    @classmethod
    def from_db_row(cls, row: Dict) -> 'Vault':
        """Create from database row."""

    def to_dict(self) -> Dict:
        """Convert to dictionary."""

    def to_json(self) -> str:
        """Convert to JSON."""
```

**Models:**
- `Vault`: Vault metadata
- `Note`: Note content and metadata
- `ScanResult`: Scan operation results
- `GraphMetrics`: Graph analysis metrics
- `VaultStats`: Statistical summaries

**All models have:**
- `from_db_row()`: Create from database
- `to_dict()`: Convert to dictionary
- `to_json()`: Serialize to JSON

#### 4. Custom Exceptions (`exceptions.py`)

**Domain-specific errors:**

```python
class VaultNotFoundError(Exception):
    """Vault doesn't exist or path invalid."""

class ScanError(Exception):
    """Scan operation failed."""

class AnalysisError(Exception):
    """Graph analysis failed."""
```

**Responsibilities:**
- All business logic lives here
- Interface-agnostic (no CLI/TUI dependencies)
- Returns structured data (not formatted strings)
- Raises domain exceptions
- Orchestrates data layer operations

---

### Layer 3: Data (Persistence & I/O)

**Location:** `src/python/` (db_manager.py, vault_scanner.py, etc.)

**Purpose:** Data access and external I/O

**Components:**

#### 1. DatabaseManager (`db_manager.py`, 469 lines)

**SQLite database operations:**

```python
class DatabaseManager:
    def get_connection(self):
        """Context manager for connections."""

    def add_vault(self, path, name) -> str:
        """Add vault to database."""

    def get_vault(self, vault_id) -> Dict:
        """Get vault by ID."""

    def list_vaults(self) -> List[Dict]:
        """List all vaults."""

    def get_orphaned_notes(self, vault_id) -> List[Dict]:
        """Query orphaned notes view."""

    def get_hub_notes(self, vault_id) -> List[Dict]:
        """Query hub notes view."""
```

#### 2. VaultScanner (`vault_scanner.py`, 373 lines)

**File system scanning:**

```python
class VaultScanner:
    def discover_vaults(self, root: str) -> List[str]:
        """Find .obsidian directories."""

    def scan_vault(self, path: str, name: str) -> Dict:
        """Parse markdown files, populate database."""
```

#### 3. GraphBuilder (`graph_builder.py`, 307 lines)

**NetworkX graph construction:**

```python
class GraphBuilder:
    def build_graph(self, vault_id: str) -> nx.DiGraph:
        """Build directed graph from database."""

    def calculate_metrics(self, vault_id: str) -> Dict:
        """Calculate PageRank, centrality."""

    def find_clusters(self, vault_id: str) -> List[Set]:
        """Community detection."""
```

**Responsibilities:**
- Database queries and updates
- File system I/O
- External API calls
- **NO business logic**
- Returns raw data (dicts, lists, graphs)

---

## Data Flow

### Typical Flow: Scanning a Vault

```
┌──────────┐
│   User   │
└────┬─────┘
     │
     │ obs scan /vault
     ▼
┌──────────────────────┐
│  ZSH CLI (obs.zsh)   │  ← Presentation Layer
└────┬─────────────────┘
     │
     │ python3 obs_cli.py scan /vault
     ▼
┌──────────────────────┐
│  Python CLI          │  ← Presentation Layer
│  (obs_cli.py)        │
└────┬─────────────────┘
     │
     │ vault_manager.scan_vault("/vault")
     ▼
┌──────────────────────┐
│  VaultManager        │  ← Application Layer (CORE)
│  (core/)             │
│                      │
│  1. Validate path    │
│  2. Call scanner     │
│  3. Aggregate stats  │
│  4. Return result    │
└────┬─────────────────┘
     │
     │ scanner.scan_vault("/vault")
     ▼
┌──────────────────────┐
│  VaultScanner        │  ← Data Layer
│  (vault_scanner.py)  │
│                      │
│  1. Read files       │
│  2. Parse markdown   │
│  3. Store in DB      │
└────┬─────────────────┘
     │
     │ db.add_note(...)
     ▼
┌──────────────────────┐
│  DatabaseManager     │  ← Data Layer
│  (db_manager.py)     │
└────┬─────────────────┘
     │
     │ INSERT INTO notes ...
     ▼
┌──────────────────────┐
│  SQLite Database     │
│  (vault_db.sqlite)   │
└──────────────────────┘
```

### Return Flow: Results Back to User

```
┌──────────────────────┐
│  VaultManager        │  ← Returns ScanResult object
└────┬─────────────────┘
     │
     │ ScanResult(notes=150, links=300, ...)
     ▼
┌──────────────────────┐
│  Python CLI          │  ← Formats as text
│  (obs_cli.py)        │
│                      │
│  print(f"✓ {result.notes_scanned} notes")
└────┬─────────────────┘
     │
     │ Text output
     ▼
┌──────────┐
│   User   │  ← Sees: "✓ 150 notes scanned"
└──────────┘
```

### Same Flow for TUI

```
┌──────────────────────┐
│  VaultManager        │  ← Same core logic!
└────┬─────────────────┘
     │
     │ ScanResult(notes=150, links=300, ...)
     ▼
┌──────────────────────┐
│  TUI Screen          │  ← Formats as widgets
│  (tui/screens/)      │
│                      │
│  self.status_label.update("Scanned 150 notes")
└────┬─────────────────┘
     │
     │ Widget update
     ▼
┌──────────┐
│   User   │  ← Sees widget: "Scanned 150 notes"
└──────────┘
```

**Key point:** Same business logic, different presentation!

---

## Design Patterns

### 1. Repository Pattern

**Data layer acts as repository:**

```python
# Data layer: DatabaseManager is repository
class DatabaseManager:
    def get_vault(self, vault_id) -> Dict:
        """Get vault from database."""
        # SQL query here

# Application layer: Uses repository
class VaultManager:
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager

    def get_vault(self, vault_id) -> Vault:
        row = self.db.get_vault(vault_id)  # Repository
        return Vault.from_db_row(row)  # Domain model
```

### 2. Facade Pattern

**Core layer provides simplified interface:**

```python
# Complex operations hidden behind simple methods
class GraphAnalyzer:
    def analyze_vault(self, vault_id: str) -> Dict:
        """One method handles: resolve links, calc metrics, find clusters."""
        link_stats = self.resolver.resolve_all_links(vault_id)
        metric_stats = self.graph_builder.calculate_metrics(vault_id)
        clusters = self.graph_builder.find_clusters(vault_id)
        # Combine results
        return {...}
```

### 3. Factory Pattern

**Domain models from database rows:**

```python
@dataclass
class Vault:
    @classmethod
    def from_db_row(cls, row: Dict) -> 'Vault':
        """Factory method to create from database."""
        return cls(
            id=row['id'],
            name=row['name'],
            # ...
        )
```

### 4. Dependency Injection

**Core layer receives dependencies:**

```python
class VaultManager:
    def __init__(self, db_manager: Optional[DatabaseManager] = None):
        """Inject database manager for testability."""
        self.db = db_manager if db_manager else DatabaseManager()
```

Benefits:
- Easy to mock in tests
- Can swap implementations
- Clear dependencies

---

## Benefits

### 1. Code Reusability

**Before (two-layer):**
```python
# CLI
def scan_command(args):
    # Duplicate business logic
    vault = validate_vault(args.path)
    stats = scan_files(vault)
    result = aggregate_stats(stats)
    print(result)

# TUI
class ScanScreen(Screen):
    def on_scan(self):
        # Duplicate business logic again!
        vault = validate_vault(self.path)
        stats = scan_files(vault)
        result = aggregate_stats(stats)
        self.display(result)
```

**After (three-layer):**
```python
# Core layer (shared)
class VaultManager:
    def scan_vault(self, path) -> ScanResult:
        # Business logic once!
        ...

# CLI
def scan_command(args):
    result = vault_manager.scan_vault(args.path)
    print(result)

# TUI
class ScanScreen(Screen):
    def on_scan(self):
        result = vault_manager.scan_vault(self.path)
        self.display(result)
```

### 2. Testability

**Test core layer independently:**

```python
def test_scan_vault():
    # Mock database
    mock_db = MockDatabaseManager()

    # Test business logic without UI
    manager = VaultManager(mock_db)
    result = manager.scan_vault("/test/vault")

    assert result.notes_scanned == 10
    assert result.links_found == 20
```

### 3. Flexibility

**Add GUI without changing core:**

```python
# gui/main_window.py
class MainWindow(QMainWindow):
    def __init__(self):
        self.vault_manager = VaultManager()  # Same core!

    def on_scan_clicked(self):
        result = self.vault_manager.scan_vault(self.path)
        QMessageBox.information(self, "Complete", f"Scanned {result.notes_scanned}")
```

### 4. Clear Separation

**Each layer has single responsibility:**

- Presentation: Format output
- Application: Business logic
- Data: Persistence

**No mixing:**

```python
# Bad: Business logic in CLI
def scan_command(args):
    if not Path(args.path).exists():  # Validation (business logic)
        print("Error: Path not found")  # Output (presentation)

# Good: Separation
def scan_command(args):
    try:
        result = vault_manager.scan_vault(args.path)  # Business logic
        print(f"✓ Scanned {result.notes_scanned} notes")  # Presentation
    except VaultNotFoundError as e:
        print(f"Error: {e}")  # Presentation
```

### 5. Type Safety

**Domain models provide compile-time checking:**

```python
# Type hints ensure correctness
def scan_vault(self, path: str) -> ScanResult:
    ...

# IDE catches errors
result: ScanResult = vault_manager.scan_vault("/path")
print(result.notes_scanned)  # ✓ IDE knows this field exists
print(result.invalid_field)  # ✗ IDE shows error
```

---

## How to Add New Interfaces

### Example: Adding a Web API

**Step 1: Create presentation layer**

```python
# src/python/web/app.py
from flask import Flask, jsonify
from core.vault_manager import VaultManager

app = Flask(__name__)
vault_manager = VaultManager()

@app.route('/api/vaults', methods=['GET'])
def list_vaults():
    vaults = vault_manager.list_vaults()
    return jsonify([v.to_dict() for v in vaults])

@app.route('/api/vaults/<vault_id>/scan', methods=['POST'])
def scan_vault(vault_id):
    vault = vault_manager.get_vault(vault_id)
    result = vault_manager.scan_vault(vault.path)
    return jsonify(result.to_dict())
```

**Step 2: Done!**

No changes to core layer needed. Business logic is reused.

### Example: Adding a Mobile App

**Step 1: Create presentation layer (React Native)**

```javascript
// mobile/src/api/vaults.js
import { VaultManager } from '@core/vault_manager';

const vaultManager = new VaultManager();

export async function scanVault(vaultId) {
  const result = await vaultManager.scanVault(vaultId);
  return {
    notesScanned: result.notes_scanned,
    linksFound: result.links_found,
  };
}
```

**Step 2: Display in UI**

```javascript
// mobile/src/screens/ScanScreen.js
const result = await scanVault(vaultId);
Alert.alert('Scan Complete', `Scanned ${result.notesScanned} notes`);
```

---

## Code Examples

### Example 1: Scanning with Different Interfaces

**Core layer (shared):**

```python
# src/python/core/vault_manager.py
class VaultManager:
    def scan_vault(self, path: str, name: str = None) -> ScanResult:
        """Scan vault and return results."""
        # Validate
        if not Path(path).exists():
            raise VaultNotFoundError(f"Path not found: {path}")

        # Scan
        stats = self.scanner.scan_vault(path, name)

        # Return structured result
        return ScanResult(
            vault_id=stats['vault_id'],
            notes_scanned=stats['notes'],
            links_found=stats['links'],
            duration_seconds=stats['duration']
        )
```

**CLI interface:**

```python
# src/python/obs_cli.py
def scan(self, args):
    try:
        result = self.vault_manager.scan_vault(args.path)

        if args.json:
            print(result.to_json())
        else:
            print(f"✓ Scanned {result.notes_scanned} notes")
            print(f"✓ Found {result.links_found} links")
            print(f"✓ Took {result.duration_seconds:.2f}s")

    except VaultNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
```

**TUI interface:**

```python
# src/python/tui/screens/vaults.py
class VaultBrowserScreen(Screen):
    def on_scan_button_pressed(self):
        try:
            result = self.vault_manager.scan_vault(self.selected_vault_path)

            # Update UI widgets
            self.status_label.update(
                f"Scanned {result.notes_scanned} notes in {result.duration_seconds:.2f}s"
            )
            self.refresh_table()

        except VaultNotFoundError as e:
            self.notify(f"Error: {e}", severity="error")
```

**GUI interface (future):**

```python
# src/python/gui/main_window.py
class MainWindow(QMainWindow):
    def on_scan_clicked(self):
        try:
            result = self.vault_manager.scan_vault(self.vault_path_field.text())

            QMessageBox.information(
                self,
                "Scan Complete",
                f"Scanned {result.notes_scanned} notes\n"
                f"Found {result.links_found} links\n"
                f"Took {result.duration_seconds:.2f}s"
            )

        except VaultNotFoundError as e:
            QMessageBox.critical(self, "Error", str(e))
```

**All four interfaces:**
- Use same `vault_manager.scan_vault()` method
- Get same `ScanResult` object
- Different presentation only
- Zero business logic duplication

---

## Testing Strategy

### Unit Tests: Core Layer

**Test business logic independently:**

```python
# tests/test_vault_manager.py
import pytest
from core.vault_manager import VaultManager
from core.exceptions import VaultNotFoundError

def test_scan_vault_success(mock_db):
    manager = VaultManager(mock_db)
    result = manager.scan_vault("/valid/path")

    assert result.notes_scanned > 0
    assert result.success is True

def test_scan_vault_invalid_path(mock_db):
    manager = VaultManager(mock_db)

    with pytest.raises(VaultNotFoundError):
        manager.scan_vault("/invalid/path")
```

### Integration Tests: Data Layer

**Test database operations:**

```python
# tests/test_db_manager.py
def test_add_vault():
    db = DatabaseManager(":memory:")  # In-memory DB
    vault_id = db.add_vault("/path", "Test Vault")

    assert vault_id is not None

    vault = db.get_vault(vault_id)
    assert vault['name'] == "Test Vault"
```

### UI Tests: Presentation Layer

**Test CLI output:**

```python
# tests/test_obs_cli.py
def test_scan_command_output(capsys):
    # Run CLI command
    cli = ObsCLI()
    cli.scan(Args(path="/test/vault", json=False))

    # Check output
    captured = capsys.readouterr()
    assert "✓ Scanned" in captured.out
```

**Test TUI interactions:**

```python
# tests/test_tui.py
async def test_vault_browser_scan():
    app = ObsTUIApp()
    screen = app.get_screen("vaults")

    # Simulate button press
    await screen.on_scan_button_pressed()

    # Check UI updated
    assert "Scanned" in screen.status_label.renderable
```

---

## Migration Guide

### For Contributors: Using the Core Layer

**Before (direct database calls):**

```python
# CLI command (old way)
def scan_command(args):
    db = DatabaseManager()
    scanner = VaultScanner(db)

    # Business logic mixed in CLI
    if not Path(args.path).exists():
        print("Error: Path not found")
        return

    stats = scanner.scan_vault(args.path)
    print(f"Scanned {stats['notes']} notes")
```

**After (using VaultManager):**

```python
# CLI command (new way)
def scan_command(args):
    vault_manager = VaultManager()  # Core layer

    try:
        result = vault_manager.scan_vault(args.path)  # Business logic
        print(f"✓ Scanned {result.notes_scanned} notes")  # Presentation
    except VaultNotFoundError as e:
        print(f"Error: {e}")
```

### Best Practices

1. **Always use core layer in presentation:**
   ```python
   # Good
   result = vault_manager.scan_vault(path)

   # Bad
   scanner = VaultScanner(db)
   stats = scanner.scan_vault(path)
   ```

2. **Return structured data from core:**
   ```python
   # Good
   return ScanResult(notes_scanned=150, ...)

   # Bad
   return {"notes": 150, ...}  # Untyped dict
   ```

3. **Raise domain exceptions:**
   ```python
   # Good
   raise VaultNotFoundError("Vault not found")

   # Bad
   return None  # Unclear error handling
   ```

4. **Format in presentation layer:**
   ```python
   # Good
   result = vault_manager.scan_vault(path)
   print(f"✓ {result.notes_scanned} notes")

   # Bad
   result = vault_manager.scan_vault_and_format(path)
   print(result)  # Pre-formatted string
   ```

---

## Summary

### Architecture Overview

- **Three layers:** Presentation, Application, Data
- **Core layer:** Interface-agnostic business logic
- **Multiple interfaces:** CLI, TUI, GUI (future)
- **Shared logic:** Zero duplication between interfaces

### Key Files

```
src/python/
├── core/                      # APPLICATION LAYER
│   ├── vault_manager.py       # Vault operations (311 lines)
│   ├── graph_analyzer.py      # Graph operations (311 lines)
│   ├── models.py              # Domain models (237 lines)
│   └── exceptions.py          # Custom exceptions
│
├── obs_cli.py                 # PRESENTATION - CLI (318 lines)
├── tui/                       # PRESENTATION - TUI (1,701 lines)
│
├── db_manager.py              # DATA LAYER (469 lines)
├── vault_scanner.py           # DATA LAYER (373 lines)
└── graph_builder.py           # DATA LAYER (307 lines)
```

### Benefits Achieved

1. ✅ CLI and TUI share 100% of business logic
2. ✅ Core layer is testable independently
3. ✅ Easy to add GUI - just create new presentation layer
4. ✅ Clear separation of concerns
5. ✅ Type-safe domain models

### Next Steps

- Complete TUI implementation
- Add GUI (PySide6) if needed
- Add web API for remote access
- Consider mobile app

---

**Last Updated:** 2025-12-15
**Architecture Version:** 3-layer (refactored from 2-layer on 2025-12-14)
