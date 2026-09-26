# Claude / MCP Integration

> **TL;DR** (30 seconds)
> - **What:** Connect `obs` to Claude Desktop, Claude Code, or Cowork via MCP
> - **Why:** Ask Claude in plain English to search, analyze, and edit your vaults
> - **How:** Run `configure_mcp.py` (registers via the `claude` CLI), restart Claude
> - **Next:** Try *"List my Obsidian vaults"* in Claude Desktop
{ .tldr }

**Time:** ~2 minutes | **Level:** Beginner | **Version:** 4.5.1

---

## What You Get

Once connected, Claude can interact with every `obs` capability through natural language:

- **"Search my research vault for causal inference"** — searches note titles (bodies are not indexed)
- **"What are the most connected notes in MyVault?"** — PageRank hub detection
- **"Create a note called 'Meeting 2026-06-15'"** — note CRUD directly in Claude chat
- **"Check vault health for Research"** — 4-dimension health scores
- **"Run a quality check on all notes"** — `obs ai quality` via AI passthrough

The MCP server exposes **42 tools** and **4 resources** that map directly to `obs` commands.

---

## Prerequisites

- `obs` installed: `brew install data-wise/tap/obsidian-cli-ops`
- The `claude` CLI on `PATH` (ships with Claude Code / the unified desktop app)
- At least one vault registered: `obs discover ~/Documents --scan`

---

## Setup

### Step 1 — Run the registration script

```bash
python3 $(brew --prefix obsidian-cli-ops)/libexec/scripts/configure_mcp.py
```

This registers `obsidian-ops` with the `claude` CLI (`claude mcp add -s user`), which
writes to `~/.claude.json` (or a project-local `.mcp.json` if run from inside a
project). It's safe to re-run any time — e.g. after a `brew upgrade` — since it
removes and re-adds the entry each time.

!!! tip "From-source install"
    If you cloned the repo instead of using Homebrew, run `python3
    scripts/configure_mcp.py` from the repo root instead.

### Step 2 — Restart Claude Desktop / Claude Code

`Cmd+Q` → reopen (Claude Desktop), or restart the Code tab. MCP tools are only read
at startup, so a running session won't pick up a new or changed registration.

### Step 3 — Verify

```bash
claude mcp list
```

`obsidian-ops` should show as **✔ Connected**. Then ask Claude: **"List my Obsidian
vaults"** — it should call `list_vaults()` and return your vault list. If something's
off, see [Troubleshooting](#troubleshooting) below, or run `obs doctor --layer mcp`
for a full diagnostic.

---

## All 42 MCP Tools

### Vault Tools

| Tool | Arguments | Description |
|------|-----------|-------------|
| `list_vaults` | — | List all registered vaults with note/link counts |
| `get_vault_stats` | `vault_id` | Detailed statistics for a vault |
| `discover_vaults` | `path`, `scan=False` | Find Obsidian vaults in a directory tree. Default is **find-only** (index unchanged); `scan=True` registers + scans each vault not yet registered (named after its folder; already-registered vaults are skipped, never renamed) |
| `rename_vault` | `vault_id`, `new_name` | Rename a vault's display name (path/ID unchanged); rejects name collisions |
| `delete_vault` | `vault_id`, `confirm=False` | Remove a vault from the index — `confirm=True` required; default is **dry-run**. Files on disk untouched |

### Search Tools

| Tool | Arguments | Description |
|------|-----------|-------------|
| `search_notes` | `query`, `vault_id`, `limit` | Search note **titles** (bodies are not indexed) |
| `find_similar_notes` | `note_id`, `limit`, `threshold` | Semantically similar notes by embedding |

### Graph Analysis Tools

| Tool | Arguments | Description |
|------|-----------|-------------|
| `get_hub_notes` | `vault_id`, `limit` | Most-connected notes (PageRank) |
| `get_orphaned_notes` | `vault_id`, `limit` | Notes with no incoming or outgoing links |
| `get_broken_links` | `vault_id` | Unresolved wikilinks |
| `analyze_vault` | `vault_id` | Full graph metrics: PageRank, centrality, clustering |

### Health Tools

| Tool | Arguments | Description |
|------|-----------|-------------|
| `get_vault_health` | `vault_id` | 4-dimension score: connectivity (30%), link integrity (25%), structure (25%), freshness (20%) |

### Note CRUD Tools

| Tool | Arguments | Description |
|------|-----------|-------------|
| `list_notes` | `vault_id`, `limit`, `offset`, `tag`, `sort_by` | Paginated note listing with tag filter |
| `read_note` | `note_id` | Read full note content and frontmatter |
| `write_note` | `note_id`, `content`, `create_backup=True` | Overwrite note (backup created by default) |
| `create_note` | `vault_id`, `title`, `content`, `folder`, `tags` | Create a new note |
| `append_to_note` | `note_id`, `content`, `separator` | Append text to an existing note |
| `insert_to_note` | `note_id`, `content`, `after_heading`, `before_heading`, `as_table_row`, `replace_section` | Insert at a heading-relative position |
| `rename_note` | `note_id`, `new_title` | Rename note (warns about wikilink breakage) |
| `delete_note` | `note_id`, `confirm=False` | Delete note — `confirm=True` required; default is **dry-run** |
| `get_note_links` | `note_id` | Incoming + outgoing links |
| `rescan_vault` | `vault_id` | Re-scan vault to pick up file system changes |

### AI Passthrough Tool

| Tool | Arguments | Description |
|------|-----------|-------------|
| `run_obs_ai` | `command`, `target`, `options` | Runs any `obs ai` subcommand |

**`command` values:** `similar`, `analyze`, `duplicates`, `suggest-links`, `gaps`,
`summarize`, `refactor`, `merge-suggest`, `tag-suggest`, `quality`

### Bridge Tools

| Tool | Arguments | Description |
|------|-----------|-------------|
| `get_bridge_status` | — | Check whether the Obsidian official CLI is installed and the app is running |
| `server_info` | — | Running obs MCP server version + `restart_recommended` (flags a stale in-process server after an upgrade) |

### Temporal Tools

| Tool | Arguments | Description |
|------|-----------|-------------|
| `get_trends` | `vault_id`, `days=90` | Weekly activity trends (notes created/modified per week) |
| `get_stale_notes` | `vault_id`, `limit=20` | Most stale high-importance notes |
| `get_daily_digest` | `vault_id`, `days=90`, `limit=5` | Combined digest: bridge status + trends + top stale notes |

### Temporal Workflows

Track vault evolution over time — velocity, stale notes, and daily snapshots.

**Daily digest:**
> *"Give me a morning digest of my Research vault"*

```
Claude calls: get_daily_digest("Research")
Returns: notes created/modified today, new orphans, pending-link notes
```

**Stale note hunt:**
> *"Find Research notes that need attention"*

```
Claude calls: get_stale_notes("Research", limit=20)
Returns: notes ranked by staleness_score (pagerank × age), with days_since_modified
```

**Growth trends:**
> *"How fast is my Research vault growing? Show me the last 30 days"*

```
Claude calls: get_trends("Research", days=30)
Returns:
  total_notes: 847
  velocity_notes_per_week: 2.8
  buckets: [{week: "2026-06-16", notes_created: 3, notes_modified: 5}, ...]
```

See the [Monitoring & Health tutorial](tutorials/monitoring-and-health.md) for a complete workflow.

### Diagnostics Tool

| Tool | Arguments | Description |
|------|-----------|-------------|
| `diagnose` | `vault_id`, `layers` | Self-diagnostic checks; returns a structured health report |

### Research Tools

These 13 tools provide access to Zotero, PDFs, courses, and manuscripts **when the MCP server runs on the same machine as your data**.

| Tool | Arguments | Description |
|------|-----------|-------------|
| `unified_search` | `query`, `limit=20` | Unified search across vault + Zotero + PDFs |
| `zotero_search` | `query`, `limit=20`, `item_type=""`, `tag=""` | Search Zotero library by title/author/year |
| `zotero_get` | `key`, `format="apa"` | Get full Zotero item details |
| `zotero_cite` | `key`, `format="apa"` | Format a citation in APA/MLA/Chicago |
| `zotero_recent` | `limit=10` | Most recently modified Zotero items |
| `pdf_search` | `query`, `limit=10` | Full-text search across PDFs |
| `course_list` | — | List all Quarto-based courses |
| `course_show` | `name` | Details for a specific course |
| `course_lectures` | `name` | Lectures in a course |
| `manuscript_list` | `include_archived=False` | List manuscripts (pass `True` to include archived) |
| `manuscript_show` | `name` | Details for a manuscript |
| `manuscript_stats` | — | Aggregate word counts + status breakdown |
| `bib_check` | `manuscript_name` | Check citation completeness |

!!! note "Research tools require local data"
    All 13 research MCP tools are accessible from Claude Desktop. They require that the Zotero SQLite, PDF directories, and Quarto projects exist on the same machine as the MCP server. `unified_search` works universally without any local-path configuration. For terminal usage, see the [Research Setup tutorial](tutorials/research-setup.md).

---

## MCP Resources

Resources provide structured data that Claude can read directly:

| URI | Description |
|-----|-------------|
| `vault://{vault_id}/stats` | Live vault statistics |
| `vault://{vault_id}/health` | Live health scores |
| `obsidian://overview` | Cross-vault summary |
| `note://{note_id}` | Note content |

---

## Example Workflows

### Daily vault check

> **You:** "Show me the health of my Research vault, then list the top 5 orphaned notes"

Claude calls `get_vault_health("Research")` → `get_orphaned_notes("Research", limit=5)` and
summarizes the results with recommendations.

### Research assistant

> **You:** "Search my causal inference vault for notes about mediation analysis, then find
> notes similar to the top result"

Claude chains `search_notes` → `find_similar_notes` and presents a connected cluster of
related notes.

### Note creation from conversation

> **You:** "I just had a meeting about the collider bias paper. Create a note in my Research
> vault called 'Collider Bias Meeting 2026-06-15' with these key points: [...]"

Claude calls `create_note("Research", "Collider Bias Meeting 2026-06-15", content=...)`.

### Vault reorganization

> **You:** "Find knowledge gaps in MyVault and suggest which orphaned notes to link"

Claude calls `run_obs_ai("gaps", "MyVault")` → `get_orphaned_notes` and synthesizes a
linking plan with specific recommendations.

---

## Safety Notes

!!! warning "Write operations"
    The note CRUD tools (`write_note`, `create_note`, `append_to_note`, `rename_note`,
    `delete_note`) modify vault files. Claude will describe what it's about to do before
    calling any write tool — review before confirming.

- **`delete_note`** defaults to dry-run (`confirm=False`). Claude must pass `confirm=True`
  to actually delete. You'll see the dry-run result first.
- **`write_note`** creates a `.bak` backup automatically.
- **`rename_note`** warns you if other notes link to the note being renamed.

---

## Troubleshooting

### "obsidian-ops" doesn't appear in Claude Desktop

1. Confirm the registration actually succeeded: `claude mcp list` should list
   `obsidian-ops`. If it's missing, re-run
   `python3 $(brew --prefix obsidian-cli-ops)/libexec/scripts/configure_mcp.py`.
2. Confirm `obs` is installed: `obs version`
3. Restart Claude Desktop fully (`Cmd+Q`, not just closing the window) — MCP tools
   are only read at startup.
4. Run `obs doctor --layer mcp` for a full diagnostic (config location, entry
   present, interpreter resolves and is executable).

!!! note "Older config still has a `nexus` entry?"
    Pre-v4.0.0 installs used the MCP client key `nexus`; it was renamed to
    `obsidian-ops`. `claude mcp remove nexus -s user` cleans up the stale entry
    if `configure_mcp.py` didn't already replace it.

### `ModuleNotFoundError: mcp`

The registered interpreter is outside the obs venv. Force the correct one, then
re-register:

```bash
export OBS_PYTHON=/opt/homebrew/opt/obsidian-cli-ops/libexec/venv/bin/python3
python3 $(brew --prefix obsidian-cli-ops)/libexec/scripts/configure_mcp.py
```

Or reinstall: `brew reinstall obsidian-cli-ops`

### Tools return "vault not found"

The vault isn't registered in the obs database. Fix with:

```bash
obs discover ~/Documents --scan
obs  # verify vault appears
```

### Test the server directly

```bash
# Should exit 0 with no output (no client connected = normal)
/opt/homebrew/opt/obsidian-cli-ops/libexec/venv/bin/python3 \
  ~/projects/dev-tools/obsidian-cli-ops/src/python/mcp_server.py

# Interactive inspector (requires npx)
npx @modelcontextprotocol/inspector \
  /opt/homebrew/opt/obsidian-cli-ops/libexec/venv/bin/python3 \
  ~/projects/dev-tools/obsidian-cli-ops/src/python/mcp_server.py
```

---

## Plugin Skills (optional)

The repo ships a small Claude Code plugin in `plugin/` with two skills that tell Claude
which MCP tool fits a research, writing, teaching or vault task, with the `obs research`
CLI as fallback:

| Skill | Covers |
|-------|--------|
| `research-writing` | Zotero search/cite, PDF full text, manuscript status, bibliography checks |
| `teaching-vault` | Courses and lectures, Quarto build/preview, vault search, orphans, stale notes |

The plugin contains no MCP server config; register the server with `configure_mcp.py`
(Step 1) first. Load the plugin from a source checkout for a session:

```bash
claude --plugin-dir ~/projects/dev-tools/obsidian-cli-ops/plugin
```

Check what it loaded with `claude --plugin-dir <path> plugin details obsidian-ops`.
The Homebrew install does not include `plugin/`.

## Roadmap

The Claude integration is being built in three phases:

| Phase | Status | Description |
|-------|--------|-------------|
| **A — Claude Desktop MCP** | ✅ since v3.3.0 | 38 tools, venv-aware, note CRUD |
| **B — Cowork Plugin** | 🔜 TBD | `.plugin` bundle with skills + MCP for Cowork |
| **C — Claude Code Plugin** | 🔜 future | `bin/` wrapper, hooks, marketplace distribution |

See `PROPOSAL-claude-integration-2026-06-15.md` for full proposal and open questions.

---

## See Also

- [CLI Reference](cli-reference.md) — All `obs` commands
- [Quick Reference](refcard.md) — MCP tools cheat sheet
- [MCP_README.md](https://github.com/Data-Wise/obsidian-cli-ops/blob/main/MCP_README.md) — Setup guide in the repo
