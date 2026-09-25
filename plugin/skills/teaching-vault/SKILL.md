---
name: teaching-vault
description: Use when working with the user's courses or Obsidian vault knowledge through obs — listing courses and lectures, building or previewing a course's Quarto site, searching or reading vault notes, finding orphaned, stale or recently changed notes, or following a note's links. Routes each task to the obsidian-ops MCP tools first and the obs CLI second.
---

# Teaching and vault knowledge with obs

Prefer the **obsidian-ops MCP tools**. Fall back to the obs CLI when the MCP server is not
connected, and for Quarto builds, which have no MCP tool.

## Courses

| Task | MCP tool | CLI fallback |
|------|----------|--------------|
| List courses | `course_list()` | `obs research course list` |
| One course's status | `course_show(name)` | `obs research course show <name>` |
| A course's lectures | `course_lectures(name)` | `obs research course lectures <name>` |
| Build the Quarto site | — | `obs research quarto build <name> [--format F]` |
| Preview the Quarto site | — | `obs research quarto preview <name> [--port P]` |

`name` is the course directory name, not a path.

**Weekly lecture prep.** `course_show(name)` for the current week and next step, then
`course_lectures(name)` for what comes next. Suggest `obs research quarto preview <name>` for
the user to run; preview starts a local server, so do not start it yourself unless asked.

Each course is a directory under `research.teaching.courses_dir` with a `.STATUS` file:

```yaml
status: active
priority: 1
progress: 60
next: Prepare Week 8 lecture
week: 7
```

## Vault knowledge

| Task | MCP tool | CLI fallback |
|------|----------|--------------|
| Registered vaults | `list_vaults()` | `obs` |
| Search note titles | `search_notes(query, vault_id, limit)` | `obs search "<q>" [--vault V]` |
| Read a note | `read_note(note_id)` | — |
| A note's links and backlinks | `get_note_links(note_id)` | — |
| Notes nothing links to | `get_orphaned_notes(vault_id, limit)` | count only: `obs stats <vault>` |
| Notes not touched in a while | `get_stale_notes(vault_id, limit)` | `obs stale <vault> [--limit N]` |
| What changed recently | `get_daily_digest(vault_id, days, limit)` | `obs daily-digest <vault> [--days N]` |
| Vault health | `get_vault_health(vault_id)` | `obs health <vault> [--json]` |
| Search vault + Zotero + PDFs | `unified_search(query, limit)` | `obs research search "<q>" --source all` |

`search_notes` matches **titles only**: note bodies are not indexed. To find a term inside
notes, `search_notes` a likely title, then `read_note`.

`vault_id` accepts a vault name, full ID, or unambiguous ID prefix.

**Research discovery.** `unified_search` a topic to see vault notes, Zotero items and PDF hits
side by side, then `read_note` the most relevant notes.

**Vault cleanup.** `get_orphaned_notes` and `get_stale_notes`, grouped by folder. Report
candidates only: never delete or move notes unless the user asks for that specific note.

**Index out of date.** If a note the user just edited or created is missing, the index is
stale. `rescan_vault(vault_id)` refreshes it; pass `prune=True` only after deletes or renames.
A vault missing from `list_vaults()` entirely is not registered: find it with
`discover_vaults(path)`, then register it with `discover_vaults(path, scan=True)`.

## When something is not configured

Courses read `research.teaching.courses_dir` in `~/.config/obs/config.yaml`; say which key is
missing (`obs config show`, `obs config validate`). For vault or index problems, run
`obs doctor` (`--layer vault|sync|mcp` to narrow it) and report what it flags.
