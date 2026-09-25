---
name: research-writing
description: Use when working with the user's research literature or manuscripts through obs — searching or citing Zotero items, finding text in PDFs, checking a manuscript's bibliography for missing or unused citations, or reviewing manuscript status and progress. Routes each task to the obsidian-ops MCP tools first and the `obs research` CLI second.
---

# Research and writing with obs

obs reads the user's Zotero library, PDF folders and manuscript directories. Prefer the
**obsidian-ops MCP tools**: they return formatted text and need no shell. Fall back to the
`obs research …` CLI only when the MCP server is not connected or the task needs a flag the
tool lacks.

## Task → tool

| Task | MCP tool | CLI fallback |
|------|----------|--------------|
| Find papers on a topic | `zotero_search(query, limit, item_type, tag)` | `obs research zotero search "<q>" [--limit N] [--type T] [--tag T]` |
| Item details by key | `zotero_get(key, format)` | `obs research zotero get <key>` |
| Format a citation | `zotero_cite(key, format)` — `apa` or `bibtex` | `obs research zotero cite <key> [--style apa\|bibtex]` |
| Recently added items | `zotero_recent(limit)` | `obs research zotero recent [--limit N]` |
| Items with a tag | `zotero_search(query="", tag=…)` | `obs research zotero by-tag <tag> [--limit N]` |
| Tags / collections | — | `obs research zotero tags [--limit N]` · `obs research zotero collections` |
| Search PDF full text | `pdf_search(query, limit)` | `obs research pdf search "<q>" [--limit N]` |
| Search everything at once | `unified_search(query, limit)` | `obs research search "<q>" [--source vault\|zotero\|pdf\|all]` |
| List manuscripts | `manuscript_list(include_archived)` | `obs research manuscript list [--archived]` |
| One manuscript's status | `manuscript_show(name)` | `obs research manuscript show <name>` |
| Portfolio summary | `manuscript_stats()` | `obs research manuscript stats` |
| Missing / unused citations | `bib_check(manuscript_name)` | `obs research bib check <name>` |

`name` arguments take the manuscript directory name (exact or partial match), not a path.

## Workflows

**Literature review.** `zotero_search` the topic, then group the hits by method or design in
your answer. Cite with `zotero_cite(key, "bibtex")` for each item the user keeps. Use
`pdf_search` when the user needs a quotation or detail from the paper body; Zotero metadata
does not include full text.

**Reading list.** `zotero_recent(limit=20)`, then present the items as a checklist
(`- [ ] Title (Year)`).

**Pre-submission check.** Run these in order and report each result:
1. `manuscript_show(name)` for status, progress and target journal.
2. `bib_check(name)` for citations used but missing from the `.bib`, and entries never cited.
3. For each missing key, `zotero_search` the key or author-year to find the item, then
   `zotero_cite(key, "bibtex")` so the user can paste it into the `.bib`.

`bib_check` recognizes Pandoc/Quarto (`@key`, `[@key]`) and LaTeX (`\cite{key}`,
`\citep{key}`) citations.

**Manuscript dashboard.** `manuscript_list()` lists every active manuscript with its status
and progress; `manuscript_stats()` gives counts by status.

## Manuscript conventions

Each manuscript is a directory under `research.writing.manuscripts_dir` with a `.STATUS`
file that obs reads:

```yaml
status: draft        # idea | planning | active | draft | revision | under review | complete | paused
priority: 2
progress: 45
next: Revise Methods section
target: JASA
```

## When a tool says "not configured"

The research domains read `~/.config/obs/config.yaml`. The error names the missing key:

| Message mentions | Add to config |
|------------------|---------------|
| Zotero | `research.zotero` |
| PDF | `research.pdf.directories` |
| Writing / manuscripts | `research.writing.manuscripts_dir` |

Tell the user which key is missing; check with `obs config show` and `obs config validate`.
Never guess a path and write it into their config.
