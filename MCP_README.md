# Obsidian MCP Server

MCP (Model Context Protocol) server that gives Claude Desktop, Claude Code, and Cowork
direct access to your Obsidian vaults — search, graph analysis, health scoring, note
read/write, and AI features, all via natural language.

**Version:** 4.6.0 | **Tools:** 44 | **Protocol:** FastMCP (stdio)

---

## Setup

### 1. Install obsidian-cli-ops (if not already installed)

```bash
brew install data-wise/tap/obsidian-cli-ops
```

The MCP server (`src/python/mcp_server.py`) and all required dependencies
(`mcp==1.27.2` + transitive) are included in the Homebrew venv.

### 2. Register with the `claude` CLI

```bash
python3 $(brew --prefix obsidian-cli-ops)/libexec/scripts/configure_mcp.py
```

This calls `claude mcp add -s user`, writing the `obsidian-ops` entry to
`~/.claude.json` (or a project-local `.mcp.json` if run inside a project). Safe to
re-run any time, including after `brew upgrade` — it removes and re-adds the entry.

From a source checkout instead of Homebrew: `python3 scripts/configure_mcp.py`
from the repo root.

### 3. Restart Claude Desktop

`Cmd+Q` → reopen. The `obsidian-ops` server appears in the tool panel.

### 4. Verify

```bash
claude mcp list
```

`obsidian-ops` should show **✔ Connected**. Then ask Claude: *"List my Obsidian
vaults"* — it should call `list_vaults()` and return results.

---

## Available Tools (44)

> **`vault_id` accepts a vault name, full ID, or unambiguous ID prefix.** You don't
> need the exact hash ID — `get_vault_stats("ResearchVault")` works the same as
> `get_vault_stats("a1b2c3…")`. An ambiguous prefix returns a disambiguation message.

### Vault Tools

| Tool | Description |
|------|-------------|
| `list_vaults()` | List all registered vaults with stats |
| `get_vault_stats(vault_id)` | Detailed stats for a vault |
| `discover_vaults(path, scan=False)` | Find Obsidian vaults in a directory; `scan=True` also registers the ones not yet indexed |
| `rename_vault(vault_id, new_name)` | Rename a vault's display name (path/ID unchanged); rejects name collisions |
| `delete_vault(vault_id, confirm)` | Remove a vault from the index — `confirm=True` required; default is dry-run. Files on disk are untouched |

### Search Tools

| Tool | Description |
|------|-------------|
| `search_notes(query, vault_id, limit)` | Search note **titles** (bodies are not indexed) |
| `find_similar_notes(note_id, limit, threshold)` | Semantically similar notes |

### Graph Analysis Tools

| Tool | Description |
|------|-------------|
| `get_hub_notes(vault_id, limit)` | Most-connected notes (PageRank) |
| `get_orphaned_notes(vault_id, limit)` | Notes with no links |
| `get_broken_links(vault_id)` | Unresolved wikilinks |
| `analyze_vault(vault_id)` | Full graph metrics (PageRank, centrality, clusters) |

### Health Tools

| Tool | Description |
|------|-------------|
| `get_vault_health(vault_id)` | 4-dimension score: connectivity (30%), link integrity (25%), structure (25%), freshness (20%) |

### Note CRUD Tools

| Tool | Description |
|------|-------------|
| `list_notes(vault_id, limit, offset, tag, sort_by)` | Paginated note listing with tag filtering |
| `read_note(note_id)` | Read full note content + frontmatter |
| `write_note(note_id, content, create_backup)` | Overwrite note (backup created by default) |
| `create_note(vault_id, title, content, folder, tags)` | Create a new note |
| `append_to_note(note_id, content, separator)` | Append text to an existing note |
| `list_templates(vault_id)` | List the vault's note templates |
| `create_from_template(vault_id, template, dest, variables)` | Create a note from a template (no overwrite, stays in vault) |
| `rename_note(note_id, new_title)` | Rename note (warns about wikilink breakage) |
| `delete_note(note_id, confirm)` | Delete note — `confirm=True` required; default is dry-run |
| `get_note_links(note_id)` | Incoming + outgoing links for a note |
| `rescan_vault(vault_id, prune=False)` | Re-scan vault to pick up file system changes. Default is additive; `prune=True` also sweeps notes deleted or renamed on disk out of the index (cascading to their links, tags, metrics, and embeddings). Unchanged notes are skipped via content-hash, preserving the embedding cache |

### AI Passthrough Tool

| Tool | Description |
|------|-------------|
| `run_obs_ai(command, target, options)` | Bridge to `obs ai` subcommands: `similar`, `analyze`, `duplicates`, `suggest-links`, `gaps`, `summarize`, `refactor`, `merge-suggest`, `tag-suggest`, `quality` |

### Bridge Tools

| Tool | Description |
|------|-------------|
| `get_bridge_status()` | Whether the official Obsidian CLI is installed + app running, with current capabilities |
| `server_info()` | Running obs MCP server identity: `server_version`, `installed_version`, `started_at`, `restart_recommended` (true when the in-process server is stale after an upgrade) |

### Temporal Tools

| Tool | Description |
|------|-------------|
| `get_trends(vault_id, days)` | Weekly activity trends (notes created/modified per week); `days` lookback (default 90) |
| `get_stale_notes(vault_id, limit)` | Most stale high-importance notes (pagerank × age) |
| `get_daily_digest(vault_id, days, limit)` | Combined morning briefing: bridge status + trends + top stale notes |

### Diagnostics Tools

| Tool | Description |
|------|-------------|
| `diagnose(vault_id, layers)` | Self-diagnostic across 5 layers: `python`, `database`, `vault`, `mcp`, `icloud` |

### Research Tools

> Require `research.*` config in `~/.config/obs/config.yaml` (from the nexus-cli absorption); report "not configured" when absent.

| Tool | Description |
|------|-------------|
| `unified_search(query, limit)` | Cross-source fan-out search: vault + Zotero + PDF, grouped by source |
| `zotero_search(query, limit, item_type, tag)` | Search Zotero library by title, author, or abstract |
| `zotero_get(key, format)` | Get a Zotero item by key (`format`: `apa`, `bibtex`, `full`) |
| `zotero_recent(limit)` | List recently modified Zotero items |
| `zotero_cite(key, format)` | Citation string for a Zotero item (`format`: `apa`, `bibtex`) |
| `pdf_search(query, limit)` | Search PDF documents in configured directories (filename + content) |
| `course_list()` | List teaching courses with status and progress |
| `course_show(name)` | Details for a specific course (exact or partial name) |
| `course_lectures(name)` | List lectures for a course |
| `manuscript_list(include_archived)` | List research manuscripts with status, progress, word count |
| `manuscript_show(name)` | Details for a specific manuscript |
| `manuscript_stats()` | Aggregate statistics across all manuscripts |
| `bib_check(manuscript_name)` | Bibliography consistency check (missing/unused citation keys) |

### MCP Resources

| Resource URI | Description |
|--------------|-------------|
| `vault://{vault_id}/stats` | Live vault statistics |
| `vault://{vault_id}/health` | Live health scores |
| `obsidian://overview` | Cross-vault summary |
| `note://{note_id}` | Note content |

---

## Example Prompts

```
"List my Obsidian vaults"
"Search my research vault for causal inference"
"What are the most connected notes in MyVault?"
"Show me orphaned notes in my research vault"
"Read the note titled 'causal mediation'"
"Create a note called 'Meeting Notes 2026-06-15' in my work vault"
"Append today's summary to my daily note"
"Check vault health for Research"
"Find knowledge gaps in MyVault"
"Run a quality check on all notes in MyVault"
"Find notes that are candidates for merging"
"Suggest tags for untagged notes in Research"
```

---

## Architecture

The MCP server is a thin passthrough layer over the existing three-layer architecture:

```
Claude Desktop / Claude Code / Cowork
           ↓  MCP / stdio
     mcp_server.py   (FastMCP, 44 tools)
           ↓  subprocess or direct import
   obs_cli.py / core/   (business logic)
           ↓
     SQLite + vault files
```

Tools in the Vault, Search, Graph, and Note groups call `obs_cli.py` via subprocess
(ensuring correct venv isolation). The AI tool bridges `obs ai` subcommands with
`--json` for structured output.

---

## Safety Notes

- **`delete_note`** requires `confirm=True` — defaults to dry-run (returns what would be deleted without deleting)
- **`write_note`** creates a `.bak` backup by default (`create_backup=True`)
- **`rename_note`** warns if other notes link to the renamed note (wikilinks will break until updated)
- The MCP server is **read/write** — Claude can create and modify vault files when using note tools

---

## Troubleshooting

### Server doesn't appear in Claude Desktop

1. Confirm registration succeeded: `claude mcp list` should list `obsidian-ops`. If
   not, re-run `python3 $(brew --prefix obsidian-cli-ops)/libexec/scripts/configure_mcp.py`.
2. Run `obs doctor --layer mcp` for a full diagnostic (config location, entry
   present, interpreter resolves and is executable).
3. Restart Claude Desktop fully (`Cmd+Q`, not just closing the window) — MCP tools
   are only read at startup.

### `ModuleNotFoundError: mcp`

The registered interpreter resolved to a Python outside the obs venv. Force the
correct one, then re-register:

```bash
export OBS_PYTHON=/opt/homebrew/opt/obsidian-cli-ops/libexec/venv/bin/python3
python3 $(brew --prefix obsidian-cli-ops)/libexec/scripts/configure_mcp.py
```

Or reinstall: `brew reinstall obsidian-cli-ops`

### Tools return errors about vault not found

Run `obs` in Terminal to verify vaults are registered.
If not: `obs discover ~/Documents --scan`

`vault_id` resolves by vault **name**, full **ID**, or unambiguous **ID prefix**, so a
plain name like `"ResearchVault"` works. A "Vault not found" then means no vault by that
name/ID exists; an "Ambiguous vault" message means an ID prefix matched more than one —
pass a longer prefix or the name.

---

## Development

```bash
# Test the server starts cleanly (exit 0 = good, no client = expected)
/opt/homebrew/opt/obsidian-cli-ops/libexec/venv/bin/python3 src/python/mcp_server.py

# Inspect available tools interactively
npx @modelcontextprotocol/inspector \
  /opt/homebrew/opt/obsidian-cli-ops/libexec/venv/bin/python3 \
  src/python/mcp_server.py
```

See `PROPOSAL-claude-integration-2026-06-15.md` for the full integration roadmap
(Phase 2: Cowork plugin; Phase 3: Claude Code plugin with hooks).
