# Claude / MCP Integration

> **TL;DR** (30 seconds)
> - **What:** Connect `obs` to Claude Desktop, Claude Code, or Cowork via MCP
> - **Why:** Ask Claude in plain English to search, analyze, and edit your vaults
> - **How:** Add one JSON block to `claude_desktop_config.json`, restart Claude
> - **Next:** Try *"List my Obsidian vaults"* in Claude Desktop
{ .tldr }

**Time:** ~5 minutes | **Level:** Intermediate | **Version:** 3.3.0

---

## What You Get

Once connected, Claude can interact with every `obs` capability through natural language:

- **"Search my research vault for causal inference"** — full-text search across notes
- **"What are the most connected notes in MyVault?"** — PageRank hub detection
- **"Create a note called 'Meeting 2026-06-15'"** — note CRUD directly in Claude chat
- **"Check vault health for Research"** — 4-dimension health scores
- **"Run a quality check on all notes"** — `obs ai quality` via AI passthrough

The MCP server exposes **20 tools** and **4 resources** that map directly to `obs` commands.

---

## Prerequisites

- `obs` installed: `brew install data-wise/tap/obsidian-cli-ops`
- Claude Desktop (any recent version)
- At least one vault registered: `obs discover ~/Documents --scan`

---

## Setup

### Step 1 — Edit Claude Desktop config

Open (or create) `~/Library/Application Support/Claude/claude_desktop_config.json`
and add the `obsidian-ops` entry inside `"mcpServers"`:

```json
{
  "mcpServers": {
    "obsidian-ops": {
      "command": "/bin/zsh",
      "args": [
        "-c",
        "OBS_PYTHON=\"${OBS_PYTHON:-}\"; if [ -z \"$OBS_PYTHON\" ]; then for c in \"$HOME/.local/share/obs/venv/bin/python3\" \"/opt/homebrew/opt/obsidian-cli-ops/libexec/venv/bin/python3\" \"/opt/homebrew/Cellar/obsidian-cli-ops/3.3.0/libexec/venv/bin/python\"; do [ -x \"$c\" ] && OBS_PYTHON=\"$c\" && break; done; fi; exec \"${OBS_PYTHON:-python3}\" /Users/YOUR_USERNAME/projects/dev-tools/obsidian-cli-ops/src/python/mcp_server.py"
      ],
      "env": {}
    }
  }
}
```

Replace `YOUR_USERNAME` with your macOS username (run `whoami` in Terminal).

!!! tip "From-source install"
    If you cloned the repo instead of using Homebrew, replace the path with the absolute
    path to `src/python/mcp_server.py` in your checkout.

### Step 2 — Restart Claude Desktop

`Cmd+Q` → reopen. The `obsidian-ops` server should appear in the tool panel.

### Step 3 — Verify

Ask Claude: **"List my Obsidian vaults"**

Claude should call `list_vaults()` and return your vault list. If nothing happens, see
[Troubleshooting](#troubleshooting) below.

---

## All 20 MCP Tools

### Vault Tools

| Tool | Arguments | Description |
|------|-----------|-------------|
| `list_vaults` | — | List all registered vaults with note/link counts |
| `get_vault_stats` | `vault_id` | Detailed statistics for a vault |
| `discover_vaults` | `path` | Find Obsidian vaults in a directory tree |

### Search Tools

| Tool | Arguments | Description |
|------|-----------|-------------|
| `search_notes` | `query`, `vault_id`, `limit` | Full-text search across notes |
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

1. Validate your JSON: `python3 -m json.tool ~/Library/"Application Support"/Claude/claude_desktop_config.json`
2. Check the zsh one-liner manually in Terminal — paste the `command`+`args` values
3. Confirm `obs` is installed: `obs version`
4. Restart Claude Desktop fully (`Cmd+Q`, not just closing the window)

### `ModuleNotFoundError: mcp`

The launcher resolved to a Python outside the obs venv. Force the correct interpreter:

```bash
export OBS_PYTHON=/opt/homebrew/opt/obsidian-cli-ops/libexec/venv/bin/python3
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

## Roadmap

The Claude integration is being built in three phases:

| Phase | Status | Description |
|-------|--------|-------------|
| **A — Claude Desktop MCP** | ✅ v3.3.0 | 20 tools, venv-aware, note CRUD |
| **B — Cowork Plugin** | 🔜 v3.4.0 | `.plugin` bundle with skills + MCP for Cowork |
| **C — Claude Code Plugin** | 🔜 future | `bin/` wrapper, hooks, marketplace distribution |

See `PROPOSAL-claude-integration-2026-06-15.md` for full proposal and open questions.

---

## See Also

- [CLI Reference](cli-reference.md) — All `obs` commands
- [Quick Reference](refcard.md) — MCP tools cheat sheet
- [MCP_README.md](https://github.com/Data-Wise/obsidian-cli-ops/blob/main/MCP_README.md) — Setup guide in the repo
