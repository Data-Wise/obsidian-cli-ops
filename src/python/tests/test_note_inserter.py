"""Tests for core/note_inserter.py — heading-aware insertion (#40)."""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent / "core"))

from core.note_inserter import (
    append_table_row,
    find_heading_line,
    insert_after_heading,
    insert_before_heading,
    replace_section,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

SIMPLE_DOC = """\
# Title

Some intro text.

## Hits

| Col A | Col B |
|-------|-------|
| a     | b     |

## Notes

More content here.
"""

CODE_BLOCK_DOC = """\
# Real Heading

```python
## This looks like a heading but is inside a code block
```

## Actual Second Heading

Content.
"""


# ---------------------------------------------------------------------------
# find_heading_line
# ---------------------------------------------------------------------------

class TestFindHeadingLine:
    def test_found_returns_correct_line(self):
        line = find_heading_line(SIMPLE_DOC, "Hits")
        # "## Hits" is line index 5 in SIMPLE_DOC (0-indexed)
        assert line is not None
        lines = SIMPLE_DOC.splitlines()
        assert lines[line] == "## Hits"

    def test_case_insensitive_match(self):
        assert find_heading_line(SIMPLE_DOC, "hits") == find_heading_line(SIMPLE_DOC, "HITS")

    def test_heading_in_code_block_ignored(self):
        # The ## inside ``` should NOT be matched
        line = find_heading_line(CODE_BLOCK_DOC, "This looks like a heading but is inside a code block")
        assert line is None

    def test_not_found_returns_none(self):
        assert find_heading_line(SIMPLE_DOC, "Nonexistent Section") is None

    def test_finds_h1(self):
        line = find_heading_line(SIMPLE_DOC, "Title")
        assert line == 0


# ---------------------------------------------------------------------------
# insert_after_heading
# ---------------------------------------------------------------------------

class TestInsertAfterHeading:
    def test_content_appears_after_heading(self):
        result = insert_after_heading(SIMPLE_DOC, "Notes", "Inserted line.")
        lines = result.splitlines()
        notes_idx = next(i for i, l in enumerate(lines) if l == "## Notes")
        # "Inserted line." should appear after "## Notes" (skipping blank line)
        assert any("Inserted line." in l for l in lines[notes_idx + 1:notes_idx + 4])

    def test_missing_heading_raises(self):
        with pytest.raises(ValueError, match="not found"):
            insert_after_heading(SIMPLE_DOC, "Missing", "content")

    def test_original_content_preserved(self):
        result = insert_after_heading(SIMPLE_DOC, "Notes", "Extra.")
        assert "More content here." in result


# ---------------------------------------------------------------------------
# insert_before_heading
# ---------------------------------------------------------------------------

class TestInsertBeforeHeading:
    def test_content_appears_before_heading(self):
        result = insert_before_heading(SIMPLE_DOC, "Notes", "Before notes.")
        lines = result.splitlines()
        notes_idx = next(i for i, l in enumerate(lines) if l == "## Notes")
        # "Before notes." should appear somewhere before the heading
        assert any("Before notes." in l for l in lines[:notes_idx])

    def test_missing_heading_raises(self):
        with pytest.raises(ValueError, match="not found"):
            insert_before_heading(SIMPLE_DOC, "Ghost", "content")


# ---------------------------------------------------------------------------
# append_table_row
# ---------------------------------------------------------------------------

class TestAppendTableRow:
    def test_row_appended_to_table(self):
        result = append_table_row(SIMPLE_DOC, "Hits", "| x | y |")
        assert "| x | y |" in result

    def test_bare_row_gets_pipes(self):
        result = append_table_row(SIMPLE_DOC, "Hits", "x | y")
        assert "| x | y |" in result

    def test_existing_rows_preserved(self):
        result = append_table_row(SIMPLE_DOC, "Hits", "| c | d |")
        assert "| a     | b     |" in result
        assert "| c | d |" in result

    def test_no_table_raises(self):
        doc = "## Section\n\nNo table here.\n"
        with pytest.raises(ValueError, match="No table found"):
            append_table_row(doc, "Section", "| r |")


# ---------------------------------------------------------------------------
# replace_section
# ---------------------------------------------------------------------------

class TestReplaceSection:
    def test_section_content_replaced(self):
        result = replace_section(SIMPLE_DOC, "Notes", "New notes content.")
        assert "New notes content." in result
        assert "More content here." not in result

    def test_heading_itself_preserved(self):
        result = replace_section(SIMPLE_DOC, "Notes", "Replacement.")
        assert "## Notes" in result

    def test_stops_at_same_level_heading(self):
        doc = "## A\n\nContent A.\n\n## B\n\nContent B.\n"
        result = replace_section(doc, "A", "Replaced A.")
        assert "Replaced A." in result
        assert "Content B." in result  # ## B section untouched
        assert "Content A." not in result

    def test_missing_heading_raises(self):
        with pytest.raises(ValueError, match="not found"):
            replace_section(SIMPLE_DOC, "Phantom", "content")
