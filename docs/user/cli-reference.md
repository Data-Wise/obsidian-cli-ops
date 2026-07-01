# CLI Command Reference

**Version:** 4.3.0
**Last Updated:** 2026-07-01

> **Note:** This is the **legacy** docs directory and the command list below is a partial snapshot. The live MkDocs site at `docs_mkdocs/` is authoritative — see [CLI Reference](../docs_mkdocs/cli-reference.md) for the full surface: 49 commands (18 top-level incl. `obs board`, `obs config`, and `obs research` domains).

---

## Global Options

| Flag | Description |
|------|-------------|
| `-v`, `--verbose` | Enable verbose output (passed through to AI commands) |
| `-h`, `--help` | Show help |

---

## Vault Management

### obs vaults

List all registered vaults.

```bash
obs vaults
```

**Output:** Rich-formatted table with status, name, note count, link count, last scanned, and ID.

---

### obs discover

Find Obsidian vaults in a directory tree.

```bash
obs discover <path> [--scan]
```

| Argument | Description |
|----------|-------------|
| `path` | Root directory to search |
| `--scan` | Scan discovered vaults immediately |

**Example:**
```bash
obs discover ~/Documents --scan
```

Searches for `.obsidian/` directories recursively. With `--scan`, populates the database for each found vault.

---

### obs scan

Scan a vault directory and register (or update) it in the database.

```bash
obs scan <path> [--name <name>] [--analyze] [--prune | --no-prune]
```

| Argument | Default | Description |
|----------|---------|-------------|
| `path` | | Vault directory path to scan |
| `--name` | directory name | Custom name for the vault |
| `--analyze` | off | Run graph analysis immediately after scanning |
| `--prune` / `--no-prune` | `--no-prune` | Sweep notes deleted or renamed on disk out of the index |

**Examples:**
```bash
obs scan ~/Documents/MyVault    # Additive scan (default)
obs scan ~/Vault --prune        # Scan and reconcile deleted/renamed notes
```

A plain scan is **additive** — it adds and updates notes but never removes rows, so a
note deleted or renamed on disk lingers as a ghost. `--prune` sweeps rows whose path is
gone from disk (cascading to their links, tags, metrics, and embeddings). The sweep is
skipped with a warning if a scan sees zero files, guarding against wiping the index on a
mis-pointed path. Unchanged notes are skipped via content-hash comparison, preserving the
AI embedding cache.

---

### obs stats

Show vault or global statistics with Rich panels.

```bash
obs stats [--vault <name|id>]
```

| Argument | Description |
|----------|-------------|
| `--vault` | Vault name or ID (full or prefix). Omit for global stats. |

**Examples:**
```bash
obs stats                    # Global stats (all vaults)
obs stats --vault MyVault    # Specific vault stats
obs stats --vault abc        # Prefix lookup
```

**Output:** Panel showing notes, links, tags, orphaned notes, hub notes, and broken links.

---

## Graph Analysis

### obs analyze

Analyze vault graph structure and calculate metrics (PageRank, centrality, clustering).

```bash
obs analyze <vault>
```

| Argument | Description |
|----------|-------------|
| `vault` | Vault name or ID (full or prefix) |

**Examples:**
```bash
obs analyze MyVault
obs --verbose analyze MyVault    # Includes hubs, orphans, broken links
```

**Output:**
```
Graph Analysis: MyVault
   Notes: 150
   Links: 300
   Density: 0.0134
   Clusters: 5
```

With `--verbose`, also shows top hub notes, orphaned notes, and broken links.

---

## Database Management

### obs db init

Initialize or rebuild the SQLite database.

```bash
obs db init
```

Creates the database at `~/.config/obs/vault_db.sqlite` with all tables and views.

---

## AI Provider Management

### obs ai status

Show status of all configured AI providers.

```bash
obs ai status
```

**Output:** Table showing each provider's availability, capabilities, and configuration.

---

### obs ai setup

Interactive wizard for configuring AI providers.

```bash
obs ai setup
```

Walks through API key configuration, provider selection, and testing.

---

### obs ai test

Test AI provider availability and functionality.

```bash
obs ai test [--provider <name>]
```

| Argument | Description |
|----------|-------------|
| `--provider` | Test a specific provider only |

**Available providers:** `gemini-api`, `anthropic-api`, `ollama`, `gemini-cli`, `claude-cli`

**Example:**
```bash
obs ai test                    # Test all providers
obs ai test --provider ollama  # Test Ollama only
```

---

## AI Features

All AI commands require at least one configured provider. Use `obs ai setup` to configure.

### obs ai similar

Find notes semantically similar to a given note.

```bash
obs ai similar <note_id> [--limit N] [--threshold F] [--provider NAME]
```

| Argument | Type | Default | Description |
|----------|------|---------|-------------|
| `note_id` | string | required | Note ID to find similar notes for |
| `--limit` | int | `10` | Maximum results |
| `--threshold` | float | `0.3` | Minimum similarity (0.0–1.0) |
| `--provider` | string | auto | Force specific AI provider |

**Example:**
```bash
obs ai similar abc123 --limit 5 --threshold 0.5
```

**Output:**
```
Found 3 similar notes:

  1. Machine Learning Basics
     Similarity: 82%
     Path: notes/ml-basics.md
     ID: def456

  2. Neural Networks
     Similarity: 67%
     Path: notes/neural-nets.md
     ID: ghi789
```

---

### obs ai analyze

Deep AI analysis of a single note — themes, quality, suggestions.

```bash
obs ai analyze <note_id> [--provider NAME]
```

| Argument | Type | Default | Description |
|----------|------|---------|-------------|
| `note_id` | string | required | Note ID to analyze |
| `--provider` | string | auto | Force specific AI provider |

**Output:**
```
Analysis Results:

  Summary: Comprehensive overview of graph theory fundamentals
  Themes: mathematics, algorithms, data structures
  Quality: 85%
  Connections: linear algebra, optimization

  Suggestions:
    - Add examples of real-world graph applications
    - Link to related algorithm notes
```

---

### obs ai duplicates

Find potential duplicate notes in a vault using embedding similarity.

```bash
obs ai duplicates <vault_id> [--threshold F] [--limit N] [--provider NAME]
```

| Argument | Type | Default | Description |
|----------|------|---------|-------------|
| `vault_id` | string | required | Vault ID to scan |
| `--threshold` | float | `0.85` | Similarity threshold for duplicate detection |
| `--limit` | int | `50` | Maximum duplicate groups |
| `--provider` | string | auto | Force specific AI provider |

**Example:**
```bash
obs ai duplicates v1 --threshold 0.9
```

---

### obs ai suggest-links

Suggest new wikilinks for a note based on embedding similarity.

```bash
obs ai suggest-links <note_id> [--limit N] [--provider NAME]
```

| Argument | Type | Default | Description |
|----------|------|---------|-------------|
| `note_id` | string | required | Note ID to suggest links for |
| `--limit` | int | `5` | Number of suggestions |
| `--provider` | string | auto | Force specific AI provider |

**Example:**
```bash
obs --verbose ai suggest-links abc123 --limit 3
```

**Output:**
```
Found 3 link suggestions:

  1. [[Graph Theory]] (78%)
     notes/graph-theory.md
     Semantic similarity: 78%

  2. [[Algorithms]] (65%)
     notes/algorithms.md
     Semantic similarity: 65%
```

With `--verbose`, also logs embedding computation and cache hits to stderr.

---

### obs ai gaps

Identify knowledge gaps in a vault.

```bash
obs ai gaps <vault_id> [--provider NAME]
```

| Argument | Type | Default | Description |
|----------|------|---------|-------------|
| `vault_id` | string | required | Vault ID to analyze |
| `--provider` | string | auto | Force specific AI provider |

**Gap detection:**
1. **Stub notes** — High incoming links but low word count (< 100 words)
2. **Orphaned notes** — No connections in either direction
3. **Obsidian-detected orphans** — Additional orphans from Obsidian CLI (if running)

**Output:**
```
Found 3 knowledge gaps:

  1. Stub note 'Python' has 8 incoming links but only 45 words
     - Python
     -> Expand 'Python' -- it's referenced by 8 other notes

  2. 5 orphaned notes with no connections
     - scratch-2024.md
     - ideas.md
     -> Add links to connect these notes to the knowledge graph
```

---

### obs ai summarize

Generate a vault-wide summary with themes and statistics.

```bash
obs ai summarize <vault_id> [--folder PATH] [--tag TAG] [--provider NAME]
```

| Argument | Type | Default | Description |
|----------|------|---------|-------------|
| `vault_id` | string | required | Vault ID to summarize |
| `--folder` | string | all | Scope to a specific folder path |
| `--tag` | string | all | Scope to notes with a specific tag |
| `--provider` | string | auto | Force specific AI provider |

**Example:**
```bash
obs ai summarize v1 --folder "projects/"
obs ai summarize v1 --tag "python"
```

**Output:**
```
  Notes: 150
  Themes: machine learning, data science, python, statistics, algorithms
  Top hubs:
    - Index (45 connections)
    - Python (32 connections)
  Orphans: 12

  Vault contains 150 notes across 23 themes. Top themes: machine learning,
  data science, python, statistics, algorithms. 12 orphaned notes, 5 hub notes.
```

Shows a progress indicator during processing. Notes are analyzed in batches of 10 with rate limiting between batches.

---

### obs ai refactor

AI-powered vault reorganization analysis. Suggests moves, archives, folder merges, and new folder creation.

```bash
obs ai refactor <vault> [--dry-run] [--provider NAME]
```

| Argument | Type | Default | Description |
|----------|------|---------|-------------|
| `vault` | string | required | Vault name or ID |
| `--dry-run` | flag | false | Run Phase 1 (graph-only) without AI calls |
| `--provider` | string | auto | Force specific AI provider |

**3-Phase Pipeline:**

1. **Phase 1 (Graph-only)** — Root orphans → move, stale folders → archive, small folders → merge
2. **Phase 2 (AI-enhanced)** — Tag-folder mismatch → create-folder, semantic orphan placement → connect
3. **Phase 3** — Sort by priority and confidence scoring

**Example:**

```bash
obs ai refactor MyVault                  # Full analysis
obs ai refactor MyVault --dry-run        # Graph-only preview (free, no AI)
obs --json ai refactor MyVault           # JSON output for scripting
obs --verbose ai refactor MyVault        # Show progress on stderr
```

**Output:**

```
🔄 Vault Refactor Analysis: MyVault
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 Analyzed 150 notes across 23 folders

🔴 HIGH PRIORITY (3 items)
  1. Move "unsorted-note" to inbox/
     Root-level note with no links, likely unsorted
  2. Archive folder "old-project/" → archive/
     4 notes, all >90 days stale, low connectivity

🟡 MEDIUM PRIORITY (2 items)
  1. Create "python/" folder for 8 notes with #python tag
     8 notes share #python tag but may span multiple folders

📋 Summary: 5 suggestions (3 high, 2 medium, 0 low)
```

**Suggestion Categories:**

| Category | Priority | Trigger |
|----------|----------|---------|
| `move` | high | Root-level orphan notes |
| `archive` | high | All notes >90 days stale + low connectivity |
| `merge-folder` | medium | Shallow folders with <3 notes |
| `create-folder` | medium | Tags with 5+ notes spanning folders |
| `connect` | varies | AI-detected semantic similarity (Phase 2) |

---

## Board Management

### obs board refresh

Refresh the `_ACTION-BOARD.md` file from atlas state, vault stats, and `.STATUS` files.

```bash
obs board refresh [--vault <name>] [--all] [--dry-run] [--json]
```

| Argument | Default | Description |
|----------|---------|-------------|
| `--vault` | first research vault | Vault name or ID |
| `--all` | | Refresh boards in all vaults |
| `--dry-run` | | Show what would change without writing |
| `--json` | | Machine-readable JSON output |

### obs board status

Show board existence, last-refreshed age, and ghost drift status.

```bash
obs board status [--vault <name>] [--all] [--json]
```

| Argument | Default | Description |
|----------|---------|-------------|
| `--vault` | all vaults | Vault name or ID |
| `--all` | | Show status for all vaults |
| `--json` | | Machine-readable JSON output |

**Output:**

```
  Research: board=✔ last=0d ago
  Documents: board=✘ last=never
```

---

## Quick Reference

| Command | Purpose |
|---------|---------|
| `obs vaults` | List registered vaults |
| `obs discover <path>` | Find vaults in directory |
| `obs stats` | Show statistics |
| `obs board refresh` | Refresh research action board |
| `obs board status` | Show board refresh status |
| `obs analyze <vault>` | Graph analysis |
| `obs db init` | Initialize database |
| `obs ai status` | Provider status |
| `obs ai setup` | Configure AI |
| `obs ai test` | Test providers |
| `obs ai similar <id>` | Find similar notes |
| `obs ai analyze <id>` | Analyze a note |
| `obs ai duplicates <id>` | Find duplicates |
| `obs ai suggest-links <id>` | Suggest new links |
| `obs ai gaps <id>` | Find knowledge gaps |
| `obs ai summarize <id>` | Summarize vault |
| `obs ai refactor <vault>` | Reorganization suggestions |

---

## Error Handling

All commands exit with code 1 on error and print messages prefixed with `❌`.

Common errors:

| Error | Cause | Fix |
|-------|-------|-----|
| `Vault not found` | Invalid name/ID | Check with `obs vaults` |
| `Note not found` | Invalid note ID | Check with `obs stats --vault <name>` |
| `No provider available` | No AI provider configured | Run `obs ai setup` |
| `Ambiguous prefix` | Multiple vaults match prefix | Use full name or longer prefix |
