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

**Version:** 3.2.1 | **Commands:** 18 | **AI Providers:** 5
