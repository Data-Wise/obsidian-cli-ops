# Research Domain Setup

Connect `obs` to your research stack — Zotero, PDFs, courses, and manuscripts — for a unified terminal workflow.

**Time:** ~15 minutes | **Level:** 🔵 Intermediate | **Steps:** 6

**Prerequisites:** Complete [Getting Started](getting-started.md). Have Zotero desktop installed if using Zotero integration.

---

## What Is the Research Domain?

The `obs research` commands, added in v4.0.0 (nexus-cli absorption), give `obs` a window into your research materials:

| Subcommand | What it accesses |
|------------|-----------------|
| `obs research zotero` | Zotero local SQLite database (offline, no API key) |
| `obs research pdf` | Full-text search across PDF directories |
| `obs research course` | Quarto-based course projects |
| `obs research manuscript` | Quarto manuscript projects |
| `obs research bib` | Citation completeness in manuscripts |

These commands are **CLI-only** — they do not go through the MCP server. Use them from your terminal; for vault+research unified search from Claude Desktop, see `unified_search` in the [Claude Integration guide](../claude-integration.md).

---

## Step 1: Create the Config File

`obs research` reads from `~/.config/obs/config.yaml`. Create one if you haven't already:

```bash
obs config show   # shows current config or "no config file found"
```

If no config exists:

```bash
obs config init   # creates ~/.config/obs/config.yaml with defaults
```

---

## Step 2: Configure Zotero (optional)

Zotero stores its database locally at `~/Zotero/zotero.sqlite`. Point `obs` at it:

```bash
obs config set research.zotero.database ~/Zotero/zotero.sqlite
obs config set research.zotero.storage ~/Zotero/storage
```

Verify:

```bash
obs config show
# research.zotero.database: /Users/you/Zotero/zotero.sqlite
# research.zotero.storage:  /Users/you/Zotero/storage
```

Test the connection:

```bash
obs research zotero recent --limit 5
```

Expected: a table of your 5 most recently modified Zotero items with key, title, authors, and year.

!!! warning "Zotero must not be open during heavy reads"
    Zotero locks its SQLite database when running. For read-only commands like `obs research zotero search`, this is usually fine — but if you see a lock error, quit Zotero first.

---

## Step 3: Configure PDF Directories (optional)

Point `obs` at directories containing research PDFs:

```bash
obs config set research.pdf_directories '["~/Documents/papers", "~/Downloads"]'
```

Or edit `~/.config/obs/config.yaml` directly:

```yaml
research:
  pdf_directories:
    - ~/Documents/papers
    - ~/Downloads
```

Test:

```bash
obs research pdf search "causal inference" --limit 5
```

Expected: matching PDF files with title, path, and matching text snippet. Returns `0 results` if no PDFs are found — check your paths with `obs config show`.

!!! tip "PDF search requires pdfminer.six"
    `obs research pdf search` uses `pdfminer.six` for text extraction. It's included in the `obs` venv. If you see an import error, run `./install.sh` to reprovision the venv.

---

## Step 4: Configure Courses (optional)

`obs` discovers Quarto-based course projects from a courses directory:

```bash
obs config set research.teaching.courses_dir ~/projects/courses
```

Your courses directory should contain subdirectories, each a Quarto project with a `_quarto.yml` file and lecture `.qmd` files.

```bash
obs research course list        # list all courses
obs research course show stats  # show details for the "stats" course
obs research course lectures stats  # list lectures in the "stats" course
```

Expected output for `course list`:

```
┌────────────────────────────────────────────────────────────┐
│  Course      Lectures  Assignments  Status                 │
├────────────────────────────────────────────────────────────┤
│  stats       12        3            active                  │
│  causal      8         2            active                  │
└────────────────────────────────────────────────────────────┘
```

---

## Step 5: Configure Manuscripts (optional)

`obs` reads Quarto manuscript projects from a manuscripts directory:

```bash
obs config set research.writing.manuscripts_dir ~/projects/manuscripts
```

Each manuscript should be a directory containing `_quarto.yml` and a `.STATUS` file (optional but recommended for status tracking).

```bash
obs research manuscript list              # all manuscripts
obs research manuscript list --status draft  # filter by status
obs research manuscript show collider     # details for "collider" manuscript
obs research manuscript stats             # aggregate word counts, status breakdown
```

Expected for `manuscript stats`:

```
Manuscripts: 4 total (2 draft, 1 in-review, 1 published)
Total word count: 42,831
Active word count: 31,204 (2 manuscripts)
```

---

## Step 6: Check Bibliography Completeness

Once manuscripts are configured, verify citation completeness:

```bash
obs research bib check collider
```

This reads the `.bib` file(s) referenced in the manuscript's `_quarto.yml` and checks:
- All `@cite{key}` references in `.qmd` files resolve to a `.bib` entry
- No orphaned `.bib` entries (cited in bib but not in text)

Expected output:

```
✅ collider: 23 citations, all resolved
   Orphaned entries: 0
```

!!! tip "Combine research + vault for a full picture"
    Use `obs research zotero search` to find papers, then `obs search` to find your vault notes about them. The MCP `unified_search` tool does both at once from Claude Desktop.

---

## What's Next

| Goal | Resource |
|------|----------|
| Search vault + Zotero together from Claude | [Claude Integration](../claude-integration.md) — `unified_search` |
| Monitor vault health over time | [Monitoring Tutorial](monitoring-and-health.md) |
| Full research command reference | [CLI Reference — Research section](../cli-reference.md#research-domain) |
