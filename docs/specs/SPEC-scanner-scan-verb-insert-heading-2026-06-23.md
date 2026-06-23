# SPEC: Scanner fix + obs scan verb + insert_to_note heading-aware insertion

**Date:** 2026-06-23  
**Issues:** #51 (bug) + #52 (feat) + #40 (feat)  
**PR strategy:** Single PR (user decision — bundle all 3)  
**Status:** Shipped (PR #57, dev branch)

---

## Summary

Three quality-of-life improvements surfaced from live MCP/tripwire testing (Discussion #55):

| # | Type | One-liner |
|---|------|-----------|
| #51 | bug | Empty-title note crashes scanner with `NOT NULL` on `notes.title` |
| #52 | feat | `obs scan <vault>` verb + stale-index warnings on read commands |
| #40 | feat | `insert_to_note` MCP tool — heading-aware insertion (4 modes) |

---

## Issue #51 — Empty-title guard in `vault_scanner.py`

### Root cause

`NoteData.title: str` has no default. `_extract_title()` has a 3-tier fallback:

1. `frontmatter['title']` 
2. First `# H1` heading
3. `file_path.stem`

A file named `.md` (stem = `""`) falls through all 3 tiers and yields `""`, which violates the `notes.title NOT NULL` constraint in SQLite, causing an unhandled exception that **silently drops the note from the index**.

### Fix

**File:** `src/python/vault_scanner.py`

```python
import hashlib  # add at top

@staticmethod
def _extract_title(file_path: Path, content: str, frontmatter: Dict) -> str:
    """Extract title from frontmatter, first heading, or filename."""
    if 'title' in frontmatter:
        return frontmatter['title']

    match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
    if match:
        return match.group(1).strip()

    stem = file_path.stem
    if stem:
        return stem

    # Final guard: dotfiles or edge cases where all 3 tiers yield empty string.
    # Use a stable short hash so the generated title is deterministic across rescans.
    path_hash = hashlib.md5(str(file_path).encode()).hexdigest()[:6]
    return f"Untitled-{path_hash}"
```

### Design decisions

- **Generate, never drop:** Index the note with a fallback title. Dropping notes silently is worse than a weird title — the note becomes invisible to the user.
- **Deterministic hash:** `Untitled-a3f9c1` is stable across rescans so repeated scans don't create phantom duplicates.
- **No AI auto-title at scan time:** Too expensive for a scanner that processes ~100 notes/second. AI enrichment is Issue #54's scope.

### Tests (pytest)

| Test | Fixture | Assert |
|------|---------|--------|
| `test_extract_title_frontmatter` | fm with `title:` | returns fm title |
| `test_extract_title_h1` | no fm, H1 present | returns H1 text |
| `test_extract_title_filename` | no fm, no H1, normal filename | returns stem |
| `test_extract_title_dotfile` | file named `.md` (stem = "") | returns `Untitled-{hash}`, not empty |
| `test_scanner_indexes_untitled_note` | real vault fixture with `.md` file | full scan completes, note appears in DB |

---

## Issue #52 — `obs scan` verb + staleness warnings

### Design

#### New CLI command: `obs scan <vault>`

Explicit, visible rescan — user can see it happening. `obs analyze` becomes **graph-only** (no implicit scan). Separates "refresh data" from "compute metrics".

```
obs scan <vault>        # Full rescan with progress bar
obs scan <vault> --check  # Report staleness only, no scan
```

#### Python CLI subcommand

**File:** `src/python/obs_cli.py`

```python
# New subcommand handler
def cmd_scan(args):
    vault = resolve_vault(args.vault)
    staleness = check_index_staleness(vault["id"])
    if args.check:
        print(f"Index age: {staleness.age_hours:.1f}h  "
              f"{'⚠️ STALE' if staleness.is_stale else '✅ fresh'}")
        return
    asyncio.run(vault_manager.scan_vault(vault["path"], vault["name"]))
    print(f"✅ Scanned: {vault['name']}")
```

#### ZSH wrapper

**File:** `src/obs.zsh`

```zsh
obs_scan() {
    local vault
    vault=$(_obs_resolve_vault "$1") || return 1
    $OBS_PYTHON "$python_cli" scan "$vault" "${@:2}"
}
# In dispatcher case:
"scan") obs_scan "$@" ;;
```

#### Staleness check utility

**File:** `src/python/core/vault_manager.py`

```python
from dataclasses import dataclass

@dataclass
class StalenessResult:
    is_stale: bool
    age_hours: float
    last_scanned: Optional[str]   # ISO timestamp or None

def check_index_staleness(vault_id: str, threshold_hours: float = 24.0) -> StalenessResult:
    """Check if vault index is older than threshold_hours."""
    vault = db.get_vault(vault_id)
    if not vault or not vault.get("last_scanned"):
        return StalenessResult(is_stale=True, age_hours=float("inf"), last_scanned=None)
    
    last = datetime.fromisoformat(vault["last_scanned"])
    if last.tzinfo is None:
        last = last.replace(tzinfo=timezone.utc)
    age = (datetime.now(timezone.utc) - last).total_seconds() / 3600
    return StalenessResult(
        is_stale=age > threshold_hours,
        age_hours=age,
        last_scanned=vault["last_scanned"],
    )
```

#### Staleness warnings on read commands

Inject at the top of `search`, `analyze`, `health` command handlers in `obs_cli.py`:

```python
def _warn_if_stale(vault_id: str) -> None:
    result = check_index_staleness(vault_id)
    if result.is_stale:
        age = f"{result.age_hours:.0f}h" if result.age_hours < 168 else f"{result.age_hours/24:.0f}d"
        print(f"⚠️  Index is {age} old — run `obs scan {vault_id}` to refresh", 
              file=sys.stderr)
```

The warning goes to **stderr** so it doesn't pollute `--json` output.

#### Config

**File:** `~/.config/obs/config.yaml` (existing config system)

```yaml
staleness_warning_hours: 24  # set to 0 to disable
```

Read via `config_loader.py` `get("staleness_warning_hours", 24)`.

### Design decisions

- **analyze stays graph-only:** `obs analyze` will no longer run an implicit scan. Users who relied on analyze-as-scan must now run `obs scan` first. This is a **breaking change in behavior** (not API) — document in CHANGELOG.
- **Stderr for warnings:** Keeps `--json` output clean for machine consumers.
- **`--check` flag:** Lets CI/cron scripts poll staleness without mutating state.
- **Configurable threshold:** Power users with large vaults may want a 7-day window.

### Tests (pytest)

| Test | Assert |
|------|--------|
| `test_staleness_fresh` | vault scanned 1h ago → is_stale=False |
| `test_staleness_stale` | vault scanned 48h ago → is_stale=True |
| `test_staleness_never_scanned` | no last_scanned → is_stale=True, age_hours=inf |
| `test_scan_cmd_rescans_vault` | mock scan_vault called once |
| `test_scan_check_flag_no_scan` | --check → no scan, staleness printed |

---

## Issue #40 — `insert_to_note` MCP tool (heading-aware insertion)

### New MCP tool signature

**File:** `src/python/mcp_server.py`

```python
@mcp.tool()
def insert_to_note(
    note_id: str,
    content: str,
    after_heading: Optional[str] = None,
    before_heading: Optional[str] = None,
    as_table_row: bool = False,
    replace_section: Optional[str] = None,
) -> str:
    """
    Insert content into a note at a heading-relative position.

    Exactly one of after_heading, before_heading, or replace_section must be
    set, or none (= EOF append, like append_to_note).

    Args:
        note_id: Note ID from search_notes() or list_notes().
        content: Markdown content to insert.
        after_heading: Heading text (exact match, case-insensitive) to insert after.
        before_heading: Heading text to insert before.
        as_table_row: When True and after_heading is set, appends content as a
                      table row to the table found under that heading.
        replace_section: Heading text — replaces all content between this heading
                         and the next same-level heading with `content`.
    """
```

### Backend: heading resolver

**File:** `src/python/core/note_inserter.py` (new file)

```python
from markdown_it import MarkdownIt
from typing import Optional

_md = MarkdownIt()

def find_heading_line(text: str, heading_text: str) -> Optional[int]:
    """Return 0-indexed line number of the heading, or None if not found.
    
    Uses markdown-it-py AST to correctly skip headings inside fenced code blocks.
    Matching is case-insensitive and strips leading #s from inline tokens.
    """
    tokens = _md.parse(text)
    lines = text.splitlines()
    for i, tok in enumerate(tokens):
        if tok.type == "heading_open" and i + 1 < len(tokens):
            inline = tokens[i + 1]
            heading_content = "".join(
                child.content for child in (inline.children or [])
            ).strip()
            if heading_content.lower() == heading_text.lower():
                return tok.map[0]   # 0-indexed line
    return None


def insert_after_heading(text: str, heading: str, content: str) -> str:
    """Insert content on the line after the blank line following a heading."""
    line_idx = find_heading_line(text, heading)
    if line_idx is None:
        raise ValueError(f"Heading not found: '{heading}'")
    lines = text.splitlines(keepends=True)
    # Skip blank lines immediately after the heading
    insert_at = line_idx + 1
    while insert_at < len(lines) and lines[insert_at].strip() == "":
        insert_at += 1
    lines.insert(insert_at, content.rstrip("\n") + "\n\n")
    return "".join(lines)


def insert_before_heading(text: str, heading: str, content: str) -> str:
    """Insert content on the line before a heading."""
    line_idx = find_heading_line(text, heading)
    if line_idx is None:
        raise ValueError(f"Heading not found: '{heading}'")
    lines = text.splitlines(keepends=True)
    lines.insert(line_idx, content.rstrip("\n") + "\n\n")
    return "".join(lines)


def append_table_row(text: str, heading: str, row: str) -> str:
    """Append a Markdown table row under a heading."""
    line_idx = find_heading_line(text, heading)
    if line_idx is None:
        raise ValueError(f"Heading not found: '{heading}'")
    lines = text.splitlines(keepends=True)
    # Find the last table row under this heading
    last_table_line = None
    for i in range(line_idx + 1, len(lines)):
        stripped = lines[i].strip()
        if stripped.startswith("|") and stripped.endswith("|"):
            last_table_line = i
        elif last_table_line is not None and stripped == "":
            break   # blank line after table = end of table
    if last_table_line is None:
        raise ValueError(f"No table found under heading '{heading}'")
    # Ensure row is pipe-delimited
    if not row.strip().startswith("|"):
        row = f"| {row} |"
    lines.insert(last_table_line + 1, row.rstrip("\n") + "\n")
    return "".join(lines)


def replace_section(text: str, heading: str, content: str) -> str:
    """Replace content between heading and the next same-level heading."""
    tokens = _md.parse(text)
    lines = text.splitlines(keepends=True)
    start_line = end_line = None
    target_level = None
    
    for i, tok in enumerate(tokens):
        if tok.type == "heading_open":
            inline = tokens[i + 1]
            heading_content = "".join(
                child.content for child in (inline.children or [])
            ).strip()
            if heading_content.lower() == heading.lower() and start_line is None:
                start_line = tok.map[1]   # line AFTER the heading
                target_level = tok.tag    # "h1", "h2", etc.
            elif start_line is not None and tok.tag == target_level:
                end_line = tok.map[0]
                break
    
    if start_line is None:
        raise ValueError(f"Heading not found: '{heading}'")
    end_line = end_line or len(lines)
    
    new_lines = lines[:start_line] + [content.rstrip("\n") + "\n"] + lines[end_line:]
    return "".join(new_lines)
```

### Validation in MCP tool

```python
# Exactly one mode must be set
modes_set = sum([
    after_heading is not None,
    before_heading is not None,
    replace_section is not None,
])
if modes_set > 1:
    return "❌ Only one of after_heading, before_heading, replace_section may be set."
if as_table_row and after_heading is None:
    return "❌ as_table_row requires after_heading to locate the table."
```

### Design decisions

- **New tool, not extended `append_to_note`:** User chose clean separation. `append_to_note` stays EOF-only (no breaking change to existing callers). `insert_to_note` handles all heading-relative operations.
- **markdown-it-py AST:** Correctly handles heading-like text inside fenced code blocks. Already a transitive dep via `rich` — no new install requirement.
- **New `note_inserter.py` module:** Keeps `mcp_server.py` thin (presentation) and enables unit testing the parser logic without an MCP context.
- **`replace_section` scope:** Stops at the next heading of the **same level** — i.e., `## Hits` is replaced only until the next `##`, not until the next `#`. This is the least-surprising behaviour.

### Tests (pytest)

| Test | Assert |
|------|--------|
| `test_find_heading_line_found` | correct 0-indexed line returned |
| `test_find_heading_line_in_code_block_ignored` | heading inside ` ``` ` not matched |
| `test_insert_after_heading` | content appears on line after heading |
| `test_insert_before_heading` | content appears on line before heading |
| `test_append_table_row_under_heading` | row appended to table, pipe-delimited |
| `test_replace_section_between_headings` | content between h2s replaced |
| `test_insert_heading_not_found_error` | ValueError raised |
| `test_insert_to_note_mcp_tool` | full MCP round-trip with mock DB |

---

## Documentation & Discoverability

- [ ] CLI reference: add `obs scan` to `docs_mkdocs/reference/cli-reference.md`
- [ ] Refcard: add `obs scan` row to `docs_mkdocs/reference/refcard.md`
- [ ] MCP reference: add `insert_to_note` to `docs_mkdocs/developer/mcp-server.md`
- [ ] CHANGELOG `[Unreleased]`: entries for #51 fix, `obs scan` verb, `insert_to_note`
- [ ] CLAUDE.md: update command count (25 → 26 with `obs scan`), MCP tools (38 → 39 with `insert_to_note`)
- [ ] `.STATUS`: update test counts (+13 new tests → 476 pytest)
- [ ] Breaking-change note: `obs analyze` no longer runs implicit scan

---

## File Inventory

| File | Change |
|------|--------|
| `src/python/vault_scanner.py` | Add `import hashlib`; update `_extract_title()` final fallback |
| `src/python/obs_cli.py` | Add `scan` subcommand; `_warn_if_stale()` injected into search/analyze/health |
| `src/python/core/vault_manager.py` | Add `check_index_staleness()` + `StalenessResult` dataclass |
| `src/python/core/note_inserter.py` | **NEW FILE** — heading parser + 4 insertion modes |
| `src/python/mcp_server.py` | Add `insert_to_note` MCP tool |
| `src/obs.zsh` | Add `obs_scan()` function + dispatcher case |
| `src/python/tests/test_vault_scanner.py` | 5 new tests (#51) |
| `src/python/tests/test_staleness.py` | **NEW** — 5 staleness tests (#52) |
| `src/python/tests/test_note_inserter.py` | **NEW** — 8 heading-insert tests (#40) |
| `docs_mkdocs/reference/cli-reference.md` | Add `obs scan` |
| `docs_mkdocs/developer/mcp-server.md` | Add `insert_to_note` |
| `CHANGELOG.md` | `[Unreleased]` entries |

---

## Acceptance Criteria

- [ ] `obs scan <any_vault>` rescans with a progress bar, exits 0
- [ ] `obs search <vault> <query>` on a 25h-stale index emits a stderr warning
- [ ] A vault containing a `.md` dotfile scans without crashing; note appears in `obs stats`
- [ ] `insert_to_note(note_id, "| row |", after_heading="Hits", as_table_row=True)` appends to the `## Hits` table
- [ ] `insert_to_note` called with two modes simultaneously returns an error (not a crash)
- [ ] All 476 pytest pass (463 baseline + 13 new); 69 Jest unchanged
- [ ] `obs scan --check <vault>` prints staleness without rescanning

---

## Estimated effort

| Issue | Core | Tests | Docs | Total |
|-------|------|-------|------|-------|
| #51 | ~15 min | ~20 min | ~5 min | **~40 min** |
| #52 | ~45 min | ~30 min | ~15 min | **~90 min** |
| #40 | ~90 min | ~45 min | ~20 min | **~155 min** |
| **Total** | | | | **~4.8h** |
