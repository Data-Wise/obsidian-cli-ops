# Quick Reference Card

> **TL;DR** — Printable cheat sheet: every command, flag, provider, MCP tool.
> **How:** `obs` to start, `obs help --all` for full details.
> **Next:** [Cookbook](cookbook.md) for task-based recipes · [Reference Index](reference/index.md)
{ .tldr }

---

## :file_folder: Core Commands

| Command | Description |
|---------|-------------|
| `obs` | List all registered vaults |
| `obs search <q> [--vault V] [--limit N] [--json]` | Search notes by title |
| `obs stats [--vault V] [--json]` | Vault or global statistics |
| `obs discover <path> [--scan]` | Find Obsidian vaults |
| `obs scan <path> [--name N] [--analyze] [--prune]` | Scan & register a vault |
| `obs analyze <vault> [-v] [--json]` | Graph metrics (PageRank, centrality) |
| `obs health <vault> [--json]` | 4-dimension health dashboard |

## :floppy_disk: Database

| Command | Description |
|---------|-------------|
| `obs db init` | Initialize or rebuild the SQLite database (`~/.config/obs/vault_db.sqlite`) |

## :stethoscope: Monitoring & Diagnostics

| Command | Description |
|---------|-------------|
| `obs bridge status` | Obsidian CLI bridge status |
| `obs trends <vault> [--days N] [--json]` | Weekly activity trends |
| `obs stale <vault> [--limit N] [--json]` | Stale high-importance notes |
| `obs daily-digest <vault> [--days N] [--limit N] [--json]` | Bridge + trends + stale |
| `obs doctor [--vault V] [--layer L] [--json]` | 7-layer self-diagnostic |
| `obs board refresh [--vault V] [--all] [--dry-run] [--json]` | Generate `_ACTION-BOARD.md` |
| `obs board status [--vault V] [--all] [--json]` | Board refresh status |

## :robot: AI Commands

| Command | Description |
|---------|-------------|
| `obs ai status` / `setup` / `test` | Provider management |
| `obs ai similar <note> [--limit N] [--provider P]` | Semantically similar notes |
| `obs ai analyze <note> [--provider P]` | Deep note analysis |
| `obs ai duplicates <vault> [--threshold F]` | Potential duplicates |
| `obs ai suggest-links <note> [--limit N]` | New link suggestions |
| `obs ai gaps <vault>` | Knowledge gaps (stubs, orphans) |
| `obs ai summarize <vault> [--folder F] [--tag T]` | Vault-wide themes |
| `obs ai refactor <vault> [--dry-run] [--json]` | Reorganization plan |
| `obs ai merge-suggest <vault> [--threshold F] [--json]` | Merge candidates |
| `obs ai tag-suggest <target> [--apply] [--json]` | Tag suggestions |
| `obs ai quality <target> [--json]` | Note quality scoring |

## :gear: Config

| Command | Description |
|---------|-------------|
| `obs config show` / `validate` / `init` / `edit` | YAML config management |
| `obs config migrate [--dry-run]` | Convert legacy config |

## :books: Research Commands

| Command | Description |
|---------|-------------|
| `obs research zotero search <q> [--limit N] [--type T] [--tag T]` | Zotero library search |
| `obs research zotero get <key> [--format F]` | Item by Zotero key |
| `obs research zotero recent [--limit N]` | Recently modified |
| `obs research zotero cite <key> [--style S]` | APA/BibTeX citation |
| `obs research zotero tags [--limit N]` | Tags with counts |
| `obs research zotero collections` | List collections |
| `obs research zotero by-tag <tag> [--limit N]` | Items by tag |
| `obs research pdf search <q> [--limit N]` | Full-text PDF search |
| `obs research pdf extract <path> [--pages R] [--layout]` | Extract PDF text |
| `obs research course list / show / lectures` | Course management |
| `obs research manuscript list / show / stats` | Manuscript tracking |
| `obs research manuscript batch-status <n>... --status <s>` | Bulk status update |
| `obs research manuscript batch-progress <n>:<p>...` | Bulk progress update |
| `obs research manuscript batch-archive <n>...` | Archive manuscripts |
| `obs research manuscript export <out> [--format F]` | Export metadata |
| `obs research bib check <name>` | Citation completeness |
| `obs research search <q> [--source S] [--json]` | Cross-source search |
| `obs research graph <v> [--format F] [--output O] [--tags]` | Export knowledge graph |
| `obs research quarto build <n> [--format F]` | Build Quarto manuscript |
| `obs research quarto preview <n> [--port P]` | Preview Quarto manuscript |
| `obs research learn <level> [--step N]` | Interactive tutorial (getting-started/medium/advanced) |

## :wrench: Vault Management

| Command | Description |
|---------|-------------|
| `obs vault info <vault> [--json]` | Single vault metadata |
| `obs vault rename <vault> <new-name> [--json]` | Rename display name |
| `obs vault delete <vault> [--force] [--json]` | Remove from index (dry-run by default) |

## :link: Other

| Command | Description |
|---------|-------------|
| `obs link [dir] [--vault-root P] [--mirror M]` | Create `.obs/sync.yml` mirror map |
| `obs research board [--out F] [--kind K] [--dry-run]` | Legacy research board renderer |
| `obs help [--all]` | Show help |
| `obs version` | Show version |

## :zap: Global Flags

| Flag | Used with |
|------|-----------|
| `--json` | `stats`, `health`, `analyze`, `doctor`, `board`, all AI subcommands |
| `--verbose` / `-v` | `scan`, `analyze`, `discover` |
| `--dry-run` | `ai refactor`, `board refresh`, `research board`, `config migrate`, `vault delete` |

---

## :robot_face: AI Provider Priority

Auto-selection order (first available wins):

| # | Provider | Speed | Privacy | Setup |
|---|----------|-------|---------|-------|
| 1 | `gemini-api` | Fast | API key | `obs ai setup` |
| 2 | `anthropic-api` | Best quality | API key | `obs ai setup` |
| 3 | `ollama` | Medium | 100% local | Local install |
| 4 | `gemini-cli` | Fast | API call | Pre-installed |
| 5 | `claude-cli` | Fast | API call | Pre-installed |

Override: `obs ai similar <note> --provider ollama`

## :mag: Vault Lookup

Commands accepting `<vault>` support flexible lookup:

```bash
obs stats MyVault        # By display name
obs stats a812           # By ID prefix (first 4+ chars)
```

## :memo: Common Workflows

```bash
# First-time setup
brew install data-wise/tap/obsidian-cli-ops
obs discover ~/Documents --scan
obs health MyVault

# Weekly board refresh
obs board refresh --dry-run && obs board refresh

# Full health pipeline
obs doctor                            # diagnose
obs ai refactor MyVault --dry-run     # preview
obs ai refactor MyVault               # plan
obs ai merge-suggest MyVault          # merge candidates
obs ai tag-suggest MyVault --apply    # auto-tag
obs scan MyVault --prune && obs analyze MyVault  # re-check

# Research pipeline
obs research zotero search "topic" --limit 10
obs research pdf search "topic"
obs research manuscript stats
obs research bib check my-paper

# Export everything as JSON
obs stats --vault MyVault --json
obs health MyVault --json
obs ai quality MyVault --json
obs doctor --json
```

---

## :link: Claude / MCP Tools (v3.3.0)

42 MCP tools in 10 groups. Setup: [Claude Integration](claude-integration.md)

| Group | Tools |
|-------|-------|
| **Vault** | `list_vaults`, `get_vault_stats`, `discover_vaults` |
| **Search** | `search_notes`, `find_similar_notes` |
| **Graph** | `get_hub_notes`, `get_orphaned_notes`, `get_broken_links`, `analyze_vault` |
| **Health** | `get_vault_health` |
| **Notes** | `list_notes`, `read_note`, `write_note`, `create_note`, `append_to_note`, `insert_to_note`, `rename_note`, `delete_note`, `get_note_links`, `rescan_vault` |
| **AI** | `run_obs_ai` (all 11 subcommands) |
| **Bridge** | `get_bridge_status` |
| **Temporal** | `get_trends`, `get_stale_notes`, `get_daily_digest` |
| **Diagnostics** | `diagnose` |
| **Research** | `zotero_search`, `zotero_get`, `pdf_search`, `course_list`, `course_show`, `course_lectures`, `manuscript_list`, `manuscript_show`, `manuscript_stats`, `bib_check`, `unified_search`, `server_info`, `get_note_links` |

**Example Claude prompts:**

```
"Search my research vault for causal inference"
"List orphaned notes in MyVault"
"Create a note called 'Meeting 2026-06-15' in Research"
"Check vault health and list top 3 issues"
"Find notes that might be merged"
```

---

## :bookmark: Native Obsidian CLI (v1.12.4+)

`obs` (graph + AI) + `obsidian` (note CRUD) = complete terminal workflow.

| Command | Description |
|---------|-------------|
| `obsidian` | Interactive TUI file browser |
| `obsidian files` | List all files |
| `obsidian read file="NAME"` | Read by wikilink |
| `obsidian create name="TITLE"` | Create note |
| `obsidian search query="TEXT"` | Full-text search |
| `obsidian daily` / `daily:append` | Daily note |
| `obsidian tags` / `tags:rename` | Tag management |
| `obsidian backlinks file="NAME"` | Incoming links |
| `obsidian orphans` | Zero-link notes |
| `obsidian properties file="NAME"` | Read frontmatter |

Requires Obsidian running (Settings → General → Command line interface).
See the [official docs](https://help.obsidian.md/cli).

---

**Version:** 4.3.0 | **Commands:** 63 | **MCP Tools:** 42 | **AI Providers:** 5
