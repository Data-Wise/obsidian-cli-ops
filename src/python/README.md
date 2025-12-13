# Obsidian CLI Ops - Python Module

Python backend for obs v2.0 knowledge graph analysis.

## Overview

This module provides:

- **Database Management**: SQLite-based vault and note storage
- **Vault Scanning**: Markdown parsing and content extraction
- **Graph Analysis**: Knowledge graph metrics and link resolution
- **CLI Interface**: Command-line tools for vault management

## Installation

### Dependencies

Install Python dependencies:

```bash
pip install -r requirements.txt
```

Or install specific packages:

```bash
pip install python-frontmatter mistune PyYAML networkx rich
```

### Optional AI Dependencies

For future AI features:

```bash
pip install anthropic google-generativeai
```

## Usage

### Command Line

The Python CLI can be used directly:

```bash
# Discover vaults
python3 src/python/obs_cli.py discover ~/Documents

# Scan a vault
python3 src/python/obs_cli.py scan ~/Documents/MyVault --analyze -v

# Analyze vault graph
python3 src/python/obs_cli.py analyze <vault_id> -v

# List vaults
python3 src/python/obs_cli.py vaults

# Show statistics
python3 src/python/obs_cli.py stats
python3 src/python/obs_cli.py stats --vault <vault_id>

# Database management
python3 src/python/obs_cli.py db init
python3 src/python/obs_cli.py db stats
```

### ZSH Integration

The Python CLI is integrated with the `obs` ZSH command:

```bash
# Discover and scan vaults
obs discover ~/Documents --scan

# Analyze vault
obs analyze <vault_id> -v

# List vaults
obs vaults

# Show stats
obs stats
obs stats <vault_id>
```

### Python API

The modules can also be used programmatically:

```python
from db_manager import DatabaseManager
from vault_scanner import VaultScanner
from graph_builder import GraphBuilder

# Initialize
db = DatabaseManager()
scanner = VaultScanner(db)
graph = GraphBuilder(db)

# Scan vault
stats = scanner.scan_vault("/path/to/vault", verbose=True)

# Analyze graph
vault = db.get_vault_by_path("/path/to/vault")
graph_stats = graph.analyze_vault(vault['id'], verbose=True)

# Query results
orphans = db.get_orphaned_notes(vault['id'])
hubs = db.get_hub_notes(vault['id'], limit=10)
broken = db.get_broken_links(vault['id'])
```

## Architecture

### Database Schema

The SQLite database (`~/.config/obs/vault_db.sqlite`) contains:

- **vaults**: Vault metadata
- **notes**: Note content and metadata
- **links**: Wikilinks between notes
- **tags**: Tag definitions and usage
- **graph_metrics**: PageRank, centrality, etc.
- **scan_history**: Scan tracking

### Modules

1. **db_manager.py**: Database operations and queries
2. **vault_scanner.py**: Markdown parsing and vault traversal
3. **graph_builder.py**: Graph analysis and link resolution
4. **obs_cli.py**: Command-line interface

## Features

### Vault Scanner

- Discovers vaults (looks for `.obsidian` directories)
- Parses markdown files with frontmatter
- Extracts wikilinks `[[target|display]]`
- Extracts tags `#tag` and `#nested/tag`
- Tracks file metadata (created, modified, word count)

### Graph Builder

- Resolves wikilinks to note IDs
- Calculates graph metrics:
  - PageRank (importance score)
  - In-degree / Out-degree (connection counts)
  - Betweenness centrality
  - Closeness centrality
  - Clustering coefficient
- Identifies orphaned notes (no connections)
- Identifies hub notes (highly connected)
- Detects broken links

### Database Manager

- CRUD operations for vaults, notes, links, tags
- Graph queries (orphans, hubs, broken links)
- Scan history tracking
- Statistics aggregation

## Development

### Testing Individual Modules

Test database:
```bash
python3 src/python/db_manager.py
```

Test scanner:
```bash
python3 src/python/vault_scanner.py /path/to/vault
```

Test graph builder:
```bash
python3 src/python/graph_builder.py <vault_id>
```

### Database Location

Default: `~/.config/obs/vault_db.sqlite`

To use a different location:
```python
db = DatabaseManager("/custom/path/to/db.sqlite")
```

## Future Enhancements

Planned for future phases:

- AI-powered note similarity detection
- Automatic merge/move/archive suggestions
- Topic modeling with embeddings
- Learning system for user preferences
- TUI/GUI visualization
- Real-time vault watching

## License

See main project LICENSE file.
