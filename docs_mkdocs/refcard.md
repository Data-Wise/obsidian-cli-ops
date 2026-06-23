# Quick Reference Card

> **TL;DR** (30 seconds)
> - **What:** Printable cheat sheet — every command on one page
> - **Why:** Pin it, bookmark it, keep it open while you work
> - **How:** `obs` to start, `obs help --all` for full details
> - **Next:** [Cookbook](cookbook.md) for task-based recipes
{ .tldr }

---

## Core Commands

| Command | Description |
|---------|-------------|
| `obs` | List all registered vaults |
| `obs search <query>` | Search notes by title (all vaults) |
| `obs search <query> --vault <name>` | Limit title search to one vault |
| `obs search <query> --limit N` | Cap results (default 20) |
| `obs search <query> --json` | Machine-readable JSON output |
| `obs stats [vault]` | Show vault or global statistics |
| `obs discover <path>` | Find Obsidian vaults in a directory |
| `obs analyze <vault>` | Analyze vault graph metrics |
| `obs health <vault>` | Vault health dashboard (scores + recommendations) |

## AI Commands

| Command | Description |
|---------|-------------|
| `obs ai status` | Show AI provider availability |
| `obs ai setup` | Interactive provider setup wizard |
| `obs ai test` | Test all AI provider connections |
| `obs ai similar <note_id>` | Find semantically similar notes |
| `obs ai analyze <note_id>` | Deep AI analysis of a note |
| `obs ai duplicates <vault>` | Detect potential duplicate notes |
| `obs ai suggest-links <note_id>` | Suggest new links based on similarity |
| `obs ai gaps <vault>` | Find knowledge gaps in the vault |
| `obs ai summarize <vault>` | Summarize vault themes and stats |
| `obs ai refactor <vault>` | AI-powered vault reorganization suggestions |
| `obs ai merge-suggest <vault>` | Find note pairs that may be merge candidates |
| `obs ai tag-suggest <target>` | Suggest tags for untagged notes (vault or single note) |
| `obs ai quality <target>` | Score notes on quality (completeness, connectivity, metadata, freshness) |

## Config Commands

| Command | Description |
|---------|-------------|
| `obs config show` | Print current config and its source file |
| `obs config validate` | Validate config and report errors |
| `obs config migrate` | Convert legacy obs/nexus config to unified YAML |
| `obs config init` | Interactive wizard to create a fresh config |
| `obs config edit` | Open config file in `$EDITOR` |

## Research Commands

| Command | Description |
|---------|-------------|
| `obs research zotero search <query>` | Search Zotero library (`--limit N`, `--type T`, `--tag T`) |
| `obs research zotero get <key>` | Get a Zotero item by key (`--format F`) |
| `obs research zotero recent` | List recently modified Zotero items (`--limit N`) |
| `obs research pdf search <query>` | Search PDF content (`--limit N`) |
| `obs research course list` | List all courses |
| `obs research course show <name>` | Show course details |
| `obs research course lectures <name>` | List lectures for a course |
| `obs research manuscript list` | List all manuscripts (`--archived`) |
| `obs research manuscript show <name>` | Show manuscript details |
| `obs research manuscript stats` | Show manuscript statistics |
| `obs research bib check <name>` | Check citations in a manuscript |

## Utilities

| Command | Description |
|---------|-------------|
| `obs help` | Quick help (essential commands) |
| `obs help --all` | Full command reference |
| `obs version` | Show version |

## Global Flags

| Flag | Description |
|------|-------------|
| `--verbose` / `-v` | Enable verbose output |
| `--json` | Output as JSON (where supported) |

## AI Refactor Flags

| Flag | Description |
|------|-------------|
| `--dry-run` | Show scope without AI calls |
| `--provider NAME` | Force a specific AI provider |
| `--json` | Machine-readable JSON output |

## Vault Lookup

Commands accepting `<vault>` support flexible lookup:

```bash
obs stats MyVault        # By name
obs stats a812           # By ID prefix
obs analyze Research_Lab # By name
```

## AI Provider Priority

Auto-selection order (first available wins):

1. `gemini-api` (fastest, needs API key)
2. `anthropic-api` (highest quality, needs API key)
3. `ollama` (local, private)
4. `gemini-cli` (free, no API key)
5. `claude-cli` (free, no API key)

Override with `--provider`:

```bash
obs ai similar <note_id> --provider ollama
obs ai refactor MyVault --provider anthropic-api
```

!!! tip "Start here"
    New to `obs`? Run these 3 commands: `obs` → `obs stats MyVault` → `obs analyze MyVault`. That's it.

## Common Workflows

```bash
# First-time setup (isolated venv, no manual pip)
./install.sh
python3 src/python/obs_cli.py db init
obs discover ~/Documents --scan

# Daily check
obs
obs health MyVault

# AI analysis
obs ai status
obs ai refactor MyVault --dry-run
obs ai refactor MyVault

# Quality features (v3.2.0)
obs ai merge-suggest MyVault              # Find merge candidates
obs ai tag-suggest MyVault --apply        # Suggest + auto-apply tags
obs ai quality MyVault                    # Score all notes

# Export for scripting
obs stats --vault MyVault --json
obs ai quality MyVault --json | python3 -m json.tool
```

---

??? info "Vault lookup shortcut"
    Any command accepting `<vault>` also accepts an ID prefix — type just the first 4 characters instead of the full name.

---

## Claude / MCP Tools (v3.3.0)

Ask Claude natural-language questions about your vaults. Requires one-time Claude Desktop setup
— see [Claude Integration](claude-integration.md).

| MCP Tool | Description |
|----------|-------------|
| `list_vaults()` | List all registered vaults |
| `get_vault_stats(vault_id)` | Vault statistics |
| `discover_vaults(path)` | Find vaults in a directory |
| `search_notes(query, vault_id)` | Full-text search |
| `find_similar_notes(note_id)` | Semantically similar notes |
| `get_hub_notes(vault_id)` | Most-connected notes |
| `get_orphaned_notes(vault_id)` | Notes with no links |
| `get_broken_links(vault_id)` | Unresolved wikilinks |
| `analyze_vault(vault_id)` | Graph metrics |
| `get_vault_health(vault_id)` | 4-dimension health score |
| `list_notes(vault_id)` | Paginated note listing |
| `read_note(note_id)` | Read note content |
| `write_note(note_id, content)` | Overwrite note (auto-backup) |
| `create_note(vault_id, title, content)` | Create new note |
| `append_to_note(note_id, content)` | Append to note |
| `rename_note(note_id, new_title)` | Rename note |
| `delete_note(note_id, confirm=True)` | Delete note (dry-run by default) |
| `run_obs_ai(command, target)` | All `obs ai` subcommands |

**Example Claude prompts:**

```
"Search my research vault for causal inference"
"List orphaned notes in MyVault"
"Create a note called 'Meeting 2026-06-15'"
"Check vault health for Research"
"Run a quality check on all notes in MyVault"
```

---

## Native Obsidian CLI (v1.12.4+)

Obsidian ships its own CLI for note-level operations. Use it alongside `obs` for a complete workflow.

!!! tip "Two tools, zero overlap"
    `obs` = graph analysis + AI insights. `obsidian` = note CRUD + search + tags. They complement each other.

| Command | Description |
|---------|-------------|
| `obsidian` | Interactive TUI file browser |
| `obsidian files` | List all files in vault |
| `obsidian read file="NAME"` | Read a note by wikilink |
| `obsidian create name="TITLE"` | Create a new note |
| `obsidian search query="TEXT"` | Full-text search |
| `obsidian daily` | Open today's daily note |
| `obsidian daily:append content="TEXT"` | Quick capture to daily note |
| `obsidian tags` | List all tags |
| `obsidian tags:rename old=X new=Y` | Rename tags vault-wide |
| `obsidian backlinks file="NAME"` | Find incoming links |
| `obsidian orphans` | Notes with zero links |
| `obsidian properties file="NAME"` | Read YAML frontmatter |
| `obsidian properties:set file="NAME" key=val` | Set a property |

??? info "Requires Obsidian running"
    The native CLI communicates with a running Obsidian instance. Enable it in Settings → General → Command line interface.

See the [official docs](https://help.obsidian.md/cli) for the full command list.

---

**Version:** 4.0.0 | **Commands:** 35 (19 core + 16 nexus-cli absorption) | **MCP Tools:** 25 | **AI Providers:** 5
