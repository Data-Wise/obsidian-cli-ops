# CLI Command Reference

> **TL;DR** (30 seconds)
> - **What:** Full reference for all 62 `obs` commands (18 top-level groups, incl. the board, config & research families) + 42 MCP tools for Claude
> - **Why:** One-stop lookup for exact syntax and options
> - **How:** `obs help --all` — see this in your terminal
> - **Next:** [Quick Reference](refcard.md) for a printable cheat sheet
{ .tldr }

**Version:** 4.3.0

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
| `--prune` / `--no-prune` | `--no-prune` | Sweep notes that were deleted or renamed on disk out of the index |

**Examples:**

```bash
obs scan ~/Documents/MyVault              # Scan and register a vault (additive)
obs scan ~/Notes --name "Personal Notes"  # Scan with a custom name
obs scan ~/Vault --analyze                # Scan and run analysis in one step
obs scan ~/Vault --prune                  # Scan AND remove deleted/renamed notes
```

!!! note "Additive by default — `--prune` opts into removal"
    A plain `obs scan` is **additive**: it adds and updates notes but never removes
    rows, so a note deleted or renamed on disk lingers in the index (a "ghost").
    Pass `--prune` to reconcile: after scanning, rows whose path is no longer on
    disk are swept (cascading to their links, tags, graph metrics, and embeddings).
    `--no-prune` is the explicit form of the default.

    Pruning is **guarded against accidental wipes** — if a scan sees zero files
    (e.g. a mis-pointed path or an iCloud vault that hasn't materialised), the
    sweep is skipped and a warning is emitted rather than emptying the index.

!!! tip "Unchanged notes are skipped, embeddings preserved"
    A scan compares each file's content hash against the stored one and **skips
    unchanged notes**, so re-scanning no longer rewrites every row or destroys the
    AI embedding cache. The scan summary reports unchanged, updated, pruned, and
    failed counts.

!!! tip "Staleness warnings"
    `obs analyze`, `obs search`, and `obs health` emit a warning when the index is stale (older than 24 hours). Run `obs scan <path>` to refresh.

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

### obs vault info

Show metadata for a single vault.

```bash
obs vault info <vault> [--json]
```

| Argument | Description |
|----------|-------------|
| `vault` | Vault name, ID, or unambiguous ID prefix |
| `--json` | Emit the result as JSON instead of a panel |

Reports name, ID, path, note count, last-scanned time, and registration time.

---

### obs vault rename

Change a vault's display name. The path and ID (a hash of the path) are
unchanged, so existing notes, links, and graph metrics stay valid.

```bash
obs vault rename <vault> <new-name> [--json]
```

| Argument | Description |
|----------|-------------|
| `vault` | Vault name, ID, or unambiguous ID prefix |
| `new-name` | New display name |
| `--json` | Emit the result as JSON |

**Examples:**

```bash
obs vault rename OldName "Research Vault"   # Rename by current name
obs vault rename abc123 Archive             # Rename by ID prefix
```

!!! warning "Name collisions are rejected"
    If another vault already uses the new name, the rename is refused -- name-based
    vault resolution must stay unambiguous.

---

### obs vault delete

Remove a vault from the obs database. **The vault folder on disk is never
touched** -- only the index is removed. Deletion cascades to the vault's notes,
links, tags, graph metrics, and embeddings.

```bash
obs vault delete <vault> [--force] [--json]
```

| Argument | Description |
|----------|-------------|
| `vault` | Vault name, ID, or unambiguous ID prefix |
| `--force` | Actually delete. Without it, prints a dry-run preview only. |
| `--json` | Emit the result as JSON |

**Examples:**

```bash
obs vault delete MyVault            # Dry-run preview (nothing removed)
obs vault delete MyVault --force    # Actually remove from the index
```

!!! tip "Dry-run by default"
    `obs vault delete <vault>` previews what would be removed (name, path, note
    count) without changing anything. Re-run with `--force` to commit. Re-index a
    deleted vault any time with `obs scan <path>`.

---

## :stethoscope: Monitoring & Diagnostics

### obs bridge status

Show Obsidian CLI bridge status — whether the native Obsidian CLI (v1.12.4+) is installed and the app is running.

```bash
obs bridge status
```

No arguments. Reports the bridge state and the native CLI version if detected.

---

### obs trends

Show weekly activity trends for a vault — note creation, edit, and link activity bucketed by week.

```bash
obs trends <vault> [--days N] [--json]
```

| Argument | Default | Description |
|----------|---------|-------------|
| `vault` | required | Vault name or ID |
| `--days` | `90` | Lookback window in days |
| `--json` | | Machine-readable output |

**Examples:**

```bash
obs trends Research              # 90-day trend for Research vault
obs trends Research --days 30    # Last 30 days only
obs trends Research --json       # JSON output for scripting
```

---

### obs stale

Find high-importance notes (by PageRank) that haven't been updated recently — the notes most worth revisiting.

```bash
obs stale <vault> [--limit N] [--json]
```

| Argument | Default | Description |
|----------|---------|-------------|
| `vault` | required | Vault name or ID |
| `--limit` | `20` | Maximum notes to return |
| `--json` | | Machine-readable output |

**Examples:**

```bash
obs stale Research               # Top 20 stale hub notes
obs stale Research --limit 10    # Cap at 10 results
```

!!! tip "Complementary to `obs health`"
    `obs stale` drills into the Freshness dimension of the health dashboard, surfacing the most-linked notes that need attention.

---

### obs daily-digest

Combined summary of bridge status, vault trends, and stale notes — a single morning check-in command.

```bash
obs daily-digest <vault> [--days N] [--limit N] [--json]
```

| Argument | Default | Description |
|----------|---------|-------------|
| `vault` | required | Vault name or ID |
| `--days` | `90` | Trend lookback window in days |
| `--limit` | `5` | Max stale notes to show |
| `--json` | | Machine-readable output |

**Example:**

```bash
obs daily-digest Research               # Morning digest for Research vault
obs daily-digest Research --limit 3     # Fewer stale notes in output
```

---

### obs doctor

Run self-diagnostic checks on the `obs` installation — Python runtime, database integrity, per-vault health, vault↔index sync, MCP server config, doc count accuracy, and iCloud offload detection.

```bash
obs doctor [--vault NAME] [--layer LAYER]... [--json]
```

| Argument | Default | Description |
|----------|---------|-------------|
| `--vault` | all vaults | Limit vault-level and sync checks to this vault name or ID |
| `--layer` | all layers | Run only the specified diagnostic layer (repeatable). One of `python`, `database`, `vault`, `sync`, `mcp`, `docs`, `icloud` |
| `--json` | | Machine-readable output |

**Examples:**

```bash
obs doctor                           # Full diagnostic
obs doctor --vault Research          # Vault-scoped checks only
obs doctor --layer docs              # Check doc count accuracy only
obs doctor --layer sync              # Vault↔index drift only
obs doctor --layer database --json   # DB checks as JSON
```

!!! info "Sync layer — content-based drift"
    `obs doctor --layer sync` compares each registered vault's files on disk
    against its index rows (a cheap `rglob` + `SELECT path` set diff), catching
    drift that the time-only staleness warning misses. Per vault it reports:

    | Check | Verdict | Catches | Fix |
    |-------|---------|---------|-----|
    | `sync-ghosts` | warn | DB rows whose file is gone from disk (deleted / renamed) | `obs scan <vault> --prune` |
    | `sync-missing` | warn | `*.md` on disk absent from the DB (never scanned, or a swallowed scan error) | `obs scan <vault>` (check logs) |
    | `sync-errors` | warn/fail | the last `scan_history` row recorded per-note failures | inspect the failing paths in the scan log |
    | `sync-drift` | info | one-line summary: `disk=N db=M (X ghost, Y missing)` | — |

!!! info "Doc count gate"
    `obs doctor --layer docs` is part of the release harness — it catches count drift between source code and documentation before any release lands.

!!! info "MCP static guards"
    `obs doctor --layer mcp` includes two AST guards over `mcp_server.py` that
    catch whole bug classes before release:

    - **`mcp-tool-resolvers`** — fails if a `@mcp.tool` resolves a vault with the
      exact-ID-only `db.get_vault()` instead of name/ID/prefix resolution.
    - **`mcp-async-run`** — fails if a **sync** `@mcp.tool` calls `asyncio.run()`,
      which crashes inside FastMCP's running event loop (regression guard for #62).

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

## :books: Research Registry

### obs link

Create the per-project `.obs/sync.yml` mirror map ([schema](obs-sync-yml.md)). Idempotent.

```bash
obs link [project_dir] [--vault-root <path>] [--mirror auto|mirror|none] [--force] [--json]
```

- `--vault-root` — vault path for an active mirror (defaults to `mirror: none` when omitted).
- `--mirror` — force the mode; `--force` overwrites an existing map.

```bash
obs link                                  # mirror: none (non-vault project)
obs link --vault-root ~/vault/Research/x  # active mirror
```

### obs research board

Render a deterministic dashboard of manuscripts + programs from atlas state into the vault
([tutorial](tutorials/research-board.md)).

```bash
obs research board [--out <vault file>] [--kind manuscript|program|package] [--dry-run]
```

- No `--out` → prints to stdout. `--out` → marker-bounded atomic update of the file.
- `--dry-run` → shows changes, writes nothing (non-zero exit on drift — a scheduling guard).
- No `--kind` → manuscripts + programs; `--kind` narrows to one.

```bash
obs research board
obs research board --out ~/vault/00_meta/_RESEARCH-BOARD.md
```

## :gear: Config Management

!!! info "Shipped in v4.0.0"
    `obs config` ships in **v4.0.0** (nexus-cli absorption) — available to `brew install` users.

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

## :clipboard: Board Management

!!! info "New in v4.3.0"
    `obs board` ships in **v4.3.0** (board-sync automation) — deterministic action-board
    refresh from atlas, vault, and `.STATUS` files. The LLM augments thinking sections
    on demand via the `research--action-board` prompt.

### obs board refresh

Refresh the `_ACTION-BOARD.md` file from atlas project state, vault stats, and
`.STATUS` files.

```bash
obs board refresh [--vault <name>] [--all] [--dry-run] [--json]
```

| Argument | Default | Description |
|----------|---------|-------------|
| `--vault` | first research vault | Vault name or ID |
| `--all` | | Refresh boards in all vaults |
| `--dry-run` | | Show what would change without writing |
| `--json` | | Machine-readable JSON output |

**Examples:**

```bash
obs board refresh                            # Refresh first research vault
obs board refresh --vault Research           # Specific vault
obs board refresh --all                      # All vaults
obs board refresh --dry-run                  # Preview changes
```

### obs board status

Show whether `_ACTION-BOARD.md` exists, when it was last refreshed, and
whether the vault has ghost drift.

```bash
obs board status [--vault <name>] [--all] [--json]
```

| Argument | Default | Description |
|----------|---------|-------------|
| `--vault` | all vaults | Vault name or ID |
| `--all` | | Show status for all vaults |
| `--json` | | Machine-readable JSON output |

**Examples:**

```bash
obs board status                 # Status for all vaults
obs board status --vault Research # Single vault
obs board status --json          # JSON output
```

**Output:**

```
  Research: board=✔ last=0d ago
  Documents: board=✘ last=never
```

---

## :microscope: Research Domain

!!! info "Shipped in v4.0.0"
    `obs research` ships in **v4.0.0** (nexus-cli absorption) — available to `brew install` users.

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

### obs research zotero cite

Generate an APA or BibTeX citation for a Zotero item.

```bash
obs research zotero cite <key> [--style apa|bibtex]
```

| Argument | Default | Description |
|----------|---------|-------------|
| `key` | required | Zotero item key |
| `--style` | `apa` | Citation style (`apa` or `bibtex`) |

### obs research zotero tags

List all tags with item counts.

```bash
obs research zotero tags [--limit N] [--json]
```

| Argument | Default | Description |
|----------|---------|-------------|
| `--limit` | `30` | Maximum tags to show |
| `--json` | | Machine-readable JSON output |

### obs research zotero collections

List all collections with item counts.

```bash
obs research zotero collections [--json]
```

### obs research zotero by-tag

Get all items tagged with a specific tag.

```bash
obs research zotero by-tag <tag> [--limit N] [--json]
```

| Argument | Default | Description |
|----------|---------|-------------|
| `tag` | required | Tag name to filter by |
| `--limit` | `20` | Maximum results |
| `--json` | | Machine-readable JSON output |

### obs research pdf search

Search full-text content of indexed PDFs.

```bash
obs research pdf search <query> [--limit N]
```

### obs research pdf extract

Extract text from a PDF file using `pdftotext`.

```bash
obs research pdf extract <path> [--pages RANGE] [--layout] [--json]
```

| Argument | Default | Description |
|----------|---------|-------------|
| `path` | required | Path to the PDF file |
| `--pages` | | Page range (e.g. `1-5`, `3`) |
| `--layout` | | Preserve visual layout instead of raw text |
| `--json` | | Machine-readable JSON output |

Requires `pdftotext` (`brew install poppler`).

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

### obs research manuscript batch-status

Update status for multiple manuscripts at once.

```bash
obs research manuscript batch-status <name> [<name>...] --status <value>
```

| Argument | Description |
|----------|-------------|
| `name` | One or more manuscript names |
| `--status` / `-s` | New status value (e.g. `under_review`, `archived`) |

### obs research manuscript batch-progress

Update progress for multiple manuscripts.

```bash
obs research manuscript batch-progress <name>:<progress> [<name>:<progress>...]
```

Each argument is `name:progress` (e.g. `paper1:75`). Progress is 0-100.

### obs research manuscript batch-archive

Archive multiple manuscripts by moving them to an `Archive/` subdirectory.

```bash
obs research manuscript batch-archive <name> [<name>...]
```

### obs research manuscript export

Export all manuscript metadata to a JSON or CSV file.

```bash
obs research manuscript export <output> [--format json|csv]
```

| Argument | Default | Description |
|----------|---------|-------------|
| `output` | required | Output file path |
| `--format` | `json` | Export format (`json` or `csv`) |

### obs research bib check

Check citations in a manuscript's bibliography file.

```bash
obs research bib check <name>
```

### obs research search

Unified cross-source search across vault notes, Zotero, and PDF sources.

```bash
obs research search <query> [--source vault|zotero|pdf|all] [--limit N] [--json]
```

| Argument | Default | Description |
|----------|---------|-------------|
| `query` | required | Search string |
| `--source` | `all` | Restrict to one source |
| `--limit` | `20` | Maximum results per source |
| `--json` | | Machine-readable JSON output |

Fans out to all configured research backends and returns a merged, scored result list.

### obs research graph

Export a vault's knowledge graph for use in visualization tools.

```bash
obs research graph <vault> [--format graphml|d3|json] [--output FILE] [--limit N] [--tags]
```

| Argument | Default | Description |
|----------|---------|-------------|
| `vault` | required | Vault name or ID |
| `--format` | `json` | Export format: `graphml` (Gephi), `d3` (D3.js JSON), `json` (nodes + edges) |
| `--output` | stdout | Write to file instead of stdout |
| `--limit` | `200` | Maximum notes to include |
| `--tags` | | Include tag nodes in the graph |

### obs research quarto build

Build a Quarto manuscript.

```bash
obs research quarto build <name> [--format FORMAT]
```

| Argument | Default | Description |
|----------|---------|-------------|
| `name` | required | Manuscript name or directory name |
| `--format` | `html` | Output format (maps to `quarto render --to`) |

### obs research quarto preview

Preview a Quarto manuscript in the browser.

```bash
obs research quarto preview <name> [--port PORT]
```

| Argument | Default | Description |
|----------|---------|-------------|
| `name` | required | Manuscript name or directory name |
| `--port` | `4848` | Preview server port |

### obs research learn

Interactive, guided tutorials for the `obs` CLI at three difficulty levels: `getting-started`,
`medium`, and `advanced`.

```bash
obs research learn <getting-started|medium|advanced> [--step N]
```

| Argument | Default | Description |
|----------|---------|-------------|
| `level` | required | Tutorial level: `getting-started`, `medium`, or `advanced` |
| `--step` | | Resume from a specific step number |

- **Getting Started** — installation check, config, command structure, first Zotero search,
  `--json` output.
- **Medium** — research (Zotero search → get → cite), knowledge (vault search → graph analyze),
  teaching (course list), and writing (manuscript list) workflows.
- **Advanced** — batch manuscript operations, graph exports (GraphML/D3), Claude JSON pipelines,
  bibliography checking, and Quarto automation.

Each step can show a command to try; when interactive, it prompts to confirm before continuing
and lets you pause and resume later with `--step`.

```bash
obs research learn getting-started
obs research learn medium
obs research learn advanced --step 3
```

---

## :zap: Quick Reference

| Command | Purpose |
|---------|---------|
| `obs` | List registered vaults |
| `obs search <query>` | Search notes by title |
| `obs discover <path>` | Find vaults in directory |
| `obs scan <path>` | Scan and register a vault |
| `obs stats` | Show statistics |
| `obs health <vault>` | Vault health dashboard |
| `obs bridge status` | Obsidian CLI bridge status |
| `obs trends <vault>` | Weekly activity trends |
| `obs stale <vault>` | Find stale high-importance notes |
| `obs daily-digest <vault>` | Bridge + trends + stale summary |
| `obs doctor` | Self-diagnostic checks |
| `obs board refresh` | Refresh research action board |
| `obs board status` | Show board refresh status |
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
| `obs research zotero cite <key>` | Generate APA/BibTeX citation |
| `obs research zotero tags` | List tags with counts |
| `obs research zotero collections` | List collections |
| `obs research zotero by-tag <tag>` | Items by tag |
| `obs research pdf search <q>` | Search PDF content |
| `obs research pdf extract <path>` | Extract text from PDF |
| `obs research course list` | List all courses |
| `obs research course show <name>` | Show course details |
| `obs research course lectures <name>` | List course lectures |
| `obs research manuscript list` | List manuscripts |
| `obs research manuscript show <name>` | Show manuscript details |
| `obs research manuscript stats` | Manuscript statistics |
| `obs research manuscript batch-status` | Bulk update status |
| `obs research manuscript batch-progress` | Bulk update progress |
| `obs research manuscript batch-archive` | Archive manuscripts |
| `obs research manuscript export` | Export metadata |
| `obs research bib check <name>` | Check citations |
| `obs research search <q>` | Cross-source search |
| `obs research graph <vault>` | Export knowledge graph |
| `obs research quarto build <name>` | Build Quarto manuscript |
| `obs research quarto preview <name>` | Preview Quarto manuscript |
| `obs research learn <level>` | Interactive tutorial (getting-started/medium/advanced) |

---

## :robot_face: Claude / MCP Integration

`obs` exposes **42 MCP tools** via `src/python/mcp_server.py` for use in Claude Desktop,
Claude Code, and Cowork. Once configured (see [Claude Integration](claude-integration.md)),
you can ask Claude natural-language questions about your vaults.

### MCP Tool Groups

**Vault** — `list_vaults`, `get_vault_stats`, `discover_vaults`

**Search** — `search_notes`, `find_similar_notes`

**Graph** — `get_hub_notes`, `get_orphaned_notes`, `get_broken_links`, `analyze_vault`

**Health** — `get_vault_health`

**Notes** — `list_notes`, `read_note`, `write_note`, `create_note`, `append_to_note`,
`insert_to_note`, `rename_note`, `delete_note`, `get_note_links`, `rescan_vault`

**AI** — `run_obs_ai` (bridges all `obs ai` subcommands)

### Example Claude prompts

```
"Search my research vault for causal inference"
"List orphaned notes in MyVault"
"Create a note titled 'Meeting 2026-06-15'"
"Read the note on causal mediation"
"Run a quality check on MyVault"
```

See [Claude Integration](claude-integration.md) for full setup instructions and all 42 tools.

---

## Next Steps

- [Cookbook](cookbook.md) -- Task-based recipes
- [Quick Reference](refcard.md) -- Command cheat sheet
- [Claude Integration](claude-integration.md) -- MCP server setup
