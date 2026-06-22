# CLI Command Reference

> **TL;DR** (30 seconds)
> - **What:** Full reference for all 35 `obs` commands (19 shipped + 16 Phase 1, unreleased) + 25 MCP tools for Claude
> - **Why:** One-stop lookup for exact syntax and options
> - **How:** `obs help --all` — see this in your terminal
> - **Next:** [Quick Reference](refcard.md) for a printable cheat sheet
{ .tldr }

**Version:** 3.5.0

---

## :gear: Global Options

| Flag | Description |
|------|-------------|
| `-v`, `--verbose` | Enable verbose output |
| `-h`, `--help` | Show help |
| `--json` | Output as JSON (supported on data commands) |

---

## :file_folder: Vault Management

### obs

List all registered vaults.

```bash
obs
```

**Output:** Rich-formatted table with status, name, note count, link count, last scanned, and ID.

!!! tip "Pro tip"
    This is the only command you need on day one. Everything starts from the vault list.

---

### obs search

Search notes by title across all registered vaults.

```bash
obs search <query> [--vault <name|id>] [--limit N] [--json]
```

| Argument | Default | Description |
|----------|---------|-------------|
| `query` | required | Search string (title match) |
| `--vault` / `-v` | all vaults | Limit search to one vault |
| `--limit` / `-n` | `20` | Maximum results to return |
| `--json` | | Machine-readable JSON output |

**Examples:**

```bash
obs search "causal mediation"                     # Search all vaults
obs search "causal mediation" --vault Research    # One vault only
obs search "meeting" --limit 5                    # Cap at 5 results
obs search "causal" --json                        # JSON output
```

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

!!! info "Link count display (v3.2.3+)"
    Stats now shows internal and broken links separately, e.g. `Links: 56 (635 broken)`. The first number is valid internal links; the parenthetical is the broken-link count.

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

## :chart_with_upwards_trend: Graph Analysis

### obs analyze

Analyze vault graph structure (PageRank, centrality, clustering).

```bash
obs analyze <vault>
```

With `--verbose`, also shows top hub notes, orphaned notes, and broken links.

---

## :floppy_disk: Database

### obs db init

Initialize or rebuild the SQLite database.

```bash
obs db init
```

Creates the database at `~/.config/obs/vault_db.sqlite` with all tables and views.

---

## :robot: AI Provider Management

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

## :sparkles: AI Features

All AI commands require at least one configured provider. Use `obs ai setup` to configure.

!!! warning "Provider required"
    AI commands will fail gracefully if no provider is available. Run `obs ai status` first to check.

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

??? info "Refactor is read-only"
    `obs ai refactor` only **suggests** changes — it never moves or deletes files. Use `--dry-run` to preview scope without AI calls.

### obs ai merge-suggest

Find note pairs with high embedding similarity that may be merge candidates.

```bash
obs ai merge-suggest <vault> [--threshold N] [--provider X] [--json]
```

| Flag | Default | Description |
|------|---------|-------------|
| `--threshold` | `0.8` | Minimum cosine similarity (0-1) |
| `--provider` | auto | AI provider for embeddings |
| `--json` | | Machine-readable output |

### obs ai tag-suggest

Suggest tags for untagged notes using AI and vault context.

```bash
obs ai tag-suggest <target> [--apply] [--min-confidence N] [--provider X] [--json]
```

| Flag | Default | Description |
|------|---------|-------------|
| `--apply` | | Auto-apply tags with >80% confidence to frontmatter |
| `--min-confidence` | `0.0` | Only show suggestions above this threshold |
| `--provider` | auto | AI provider |
| `--json` | | Machine-readable output |

`<target>` accepts a vault name/ID (vault-wide) or a note ID (single note).

### obs ai quality

Score notes across 4 quality dimensions (graph-only, no AI required).

```bash
obs ai quality <target> [--json]
```

**Dimensions** (weighted): completeness (30%), connectivity (30%), metadata (20%), freshness (20%).

`<target>` accepts a vault name/ID (vault-wide) or a note ID (single note). Vault-wide output is sorted worst-first.

---

## :wrench: Utility

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

## :gear: Config Management

!!! info "Phase 1 — not yet released"
    `obs config` ships in **v3.6.0** (nexus-cli absorption). It is committed but not in the current `v3.5.0` release; `brew install` users won't have it until v3.6.0.

Unified configuration at `~/.config/obs/config.yaml` — shared between `obs` and previously nexus-cli.

### obs config show

Print the current config and which file it was loaded from.

```bash
obs config show
```

### obs config validate

Validate the config file and report any errors.

```bash
obs config validate
```

### obs config migrate

Convert a legacy `obs` or `nexus-cli` config to the unified YAML format.

```bash
obs config migrate [--target-dir DIR]
```

| Argument | Description |
|----------|-------------|
| `--target-dir` | Write unified config here (default: `~/.config/obs/`) |

### obs config init

Interactive wizard to create a fresh config from scratch.

```bash
obs config init
```

### obs config edit

Open the config file in `$EDITOR`.

```bash
obs config edit
```

---

## :microscope: Research Domain

!!! info "Phase 1 — not yet released"
    `obs research` ships in **v3.6.0** (nexus-cli absorption). It is committed but not in the current `v3.5.0` release; `brew install` users won't have it until v3.6.0.

Research commands absorbed from nexus-cli. Requires configured paths in `obs config`.

### obs research zotero search

Search the local Zotero SQLite database.

```bash
obs research zotero search <query> [--limit N] [--type TYPE] [--tag TAG]
```

| Argument | Default | Description |
|----------|---------|-------------|
| `query` | required | Search string |
| `--limit` | `20` | Maximum results |
| `--type` | | Filter by Zotero item type (e.g. `journalArticle`) |
| `--tag` | | Filter by Zotero tag |

### obs research zotero get

Fetch a Zotero item by its library key.

```bash
obs research zotero get <key> [--format FORMAT]
```

### obs research zotero recent

List recently modified Zotero items.

```bash
obs research zotero recent [--limit N]
```

### obs research pdf search

Search full-text content of indexed PDFs.

```bash
obs research pdf search <query> [--limit N]
```

### obs research course list / show / lectures

Course management commands.

```bash
obs research course list                      # List all courses
obs research course show <name>               # Show course details
obs research course lectures <name>           # List lectures for a course
```

### obs research manuscript list / show / stats

Manuscript tracking commands.

```bash
obs research manuscript list [--archived]     # List manuscripts
obs research manuscript show <name>           # Show manuscript details
obs research manuscript stats                 # Aggregate statistics
```

### obs research bib check

Check citations in a manuscript's bibliography file.

```bash
obs research bib check <name>
```

---

## :zap: Quick Reference

| Command | Purpose |
|---------|---------|
| `obs` | List registered vaults |
| `obs search <query>` | Search notes by title |
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
| `obs ai merge-suggest <vault>` | Find merge candidates |
| `obs ai tag-suggest <target>` | Suggest tags |
| `obs ai quality <target>` | Score note quality |
| `obs config show` | Print current config |
| `obs config validate` | Validate config |
| `obs config migrate` | Migrate legacy config |
| `obs config init` | Create fresh config |
| `obs config edit` | Edit config in `$EDITOR` |
| `obs research zotero search <q>` | Search Zotero library |
| `obs research zotero get <key>` | Get Zotero item by key |
| `obs research zotero recent` | Recent Zotero items |
| `obs research pdf search <q>` | Search PDF content |
| `obs research course list` | List all courses |
| `obs research course show <name>` | Show course details |
| `obs research course lectures <name>` | List course lectures |
| `obs research manuscript list` | List manuscripts |
| `obs research manuscript show <name>` | Show manuscript details |
| `obs research manuscript stats` | Manuscript statistics |
| `obs research bib check <name>` | Check citations |

---

## :robot_face: Claude / MCP Integration

`obs` exposes **25 MCP tools** via `src/python/mcp_server.py` for use in Claude Desktop,
Claude Code, and Cowork. Once configured (see [Claude Integration](claude-integration.md)),
you can ask Claude natural-language questions about your vaults.

### MCP Tool Groups

**Vault** — `list_vaults`, `get_vault_stats`, `discover_vaults`

**Search** — `search_notes`, `find_similar_notes`

**Graph** — `get_hub_notes`, `get_orphaned_notes`, `get_broken_links`, `analyze_vault`

**Health** — `get_vault_health`

**Notes** — `list_notes`, `read_note`, `write_note`, `create_note`, `append_to_note`,
`rename_note`, `delete_note`, `get_note_links`, `rescan_vault`

**AI** — `run_obs_ai` (bridges all `obs ai` subcommands)

### Example Claude prompts

```
"Search my research vault for causal inference"
"List orphaned notes in MyVault"
"Create a note titled 'Meeting 2026-06-15'"
"Read the note on causal mediation"
"Run a quality check on MyVault"
```

See [Claude Integration](claude-integration.md) for full setup instructions and all 25 tools.

---

## Next Steps

- [Cookbook](cookbook.md) -- Task-based recipes
- [Quick Reference](refcard.md) -- Command cheat sheet
- [Claude Integration](claude-integration.md) -- MCP server setup
