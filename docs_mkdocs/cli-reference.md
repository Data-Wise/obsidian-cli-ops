# CLI Command Reference

**Version:** 3.0.0

Complete reference for all `obs` commands -- 15 commands covering vault management, graph analysis, and AI features.

---

## Global Options

| Flag | Description |
|------|-------------|
| `-v`, `--verbose` | Enable verbose output |
| `-h`, `--help` | Show help |
| `--json` | Output as JSON (supported on data commands) |

---

## Vault Management

### obs

List all registered vaults.

```bash
obs
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

Searches for `.obsidian/` directories recursively. With `--scan`, populates the database for each found vault.

---

### obs stats

Show vault or global statistics.

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

---

### obs health

Vault health dashboard with scores and recommendations.

```bash
obs health <vault>
```

**Dimensions scored:**

- **Connectivity** -- orphan ratio
- **Link Integrity** -- broken link count
- **Structure** -- tag coverage, hub balance
- **Freshness** -- stale note detection

---

## Graph Analysis

### obs analyze

Analyze vault graph structure (PageRank, centrality, clustering).

```bash
obs analyze <vault>
```

With `--verbose`, also shows top hub notes, orphaned notes, and broken links.

---

## Database

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

### obs ai setup

Interactive wizard for configuring AI providers.

```bash
obs ai setup
```

### obs ai test

Test AI provider availability and functionality.

```bash
obs ai test [--provider <name>]
```

**Available providers:** `gemini-api`, `anthropic-api`, `ollama`, `gemini-cli`, `claude-cli`

---

## AI Features

All AI commands require at least one configured provider. Use `obs ai setup` to configure.

### obs ai similar

Find notes semantically similar to a given note.

```bash
obs ai similar <note_id> [--limit N] [--threshold F] [--provider NAME]
```

| Argument | Default | Description |
|----------|---------|-------------|
| `--limit` | `10` | Maximum results |
| `--threshold` | `0.3` | Minimum similarity (0.0-1.0) |
| `--provider` | auto | Force specific AI provider |

### obs ai analyze

Deep AI analysis of a single note -- themes, quality, suggestions.

```bash
obs ai analyze <note_id> [--provider NAME]
```

### obs ai duplicates

Find potential duplicate notes using embedding similarity.

```bash
obs ai duplicates <vault> [--threshold F] [--limit N]
```

### obs ai suggest-links

Suggest new wikilinks for a note based on embedding similarity.

```bash
obs ai suggest-links <note_id> [--limit N]
```

### obs ai gaps

Identify knowledge gaps in a vault.

```bash
obs ai gaps <vault> [--provider NAME]
```

**Gap detection:**

1. **Stub notes** -- High incoming links but low word count
2. **Orphaned notes** -- No connections in either direction

### obs ai summarize

Generate a vault-wide summary with themes and statistics.

```bash
obs ai summarize <vault> [--folder PATH] [--tag TAG]
```

### obs ai refactor

AI-powered vault reorganization suggestions.

```bash
obs ai refactor <vault> [--dry-run] [--json]
```

**Suggestion categories:** `move`, `archive`, `merge-folder`, `create-folder`, `connect`

---

## Utility

### obs help

Show help for commands.

```bash
obs help [--all]
```

### obs version

Show version information.

```bash
obs version
```

---

## Quick Reference

| Command | Purpose |
|---------|---------|
| `obs` | List registered vaults |
| `obs discover <path>` | Find vaults in directory |
| `obs stats` | Show statistics |
| `obs health <vault>` | Vault health dashboard |
| `obs analyze <vault>` | Graph analysis |
| `obs db init` | Initialize database |
| `obs ai status` | Provider status |
| `obs ai setup` | Configure AI |
| `obs ai test` | Test providers |
| `obs ai similar <id>` | Find similar notes |
| `obs ai analyze <id>` | Analyze a note |
| `obs ai duplicates <vault>` | Find duplicates |
| `obs ai suggest-links <id>` | Suggest new links |
| `obs ai gaps <vault>` | Find knowledge gaps |
| `obs ai summarize <vault>` | Summarize vault |
| `obs ai refactor <vault>` | Reorganization suggestions |

---

## Next Steps

- [Cookbook](cookbook.md) -- Task-based recipes
- [Quick Reference](refcard.md) -- Command cheat sheet
