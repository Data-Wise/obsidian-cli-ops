"""Heading-aware note insertion using markdown-it-py AST."""

from __future__ import annotations

from typing import Optional

from markdown_it import MarkdownIt

_md = MarkdownIt()


def find_heading_line(text: str, heading_text: str) -> Optional[int]:
    """Return 0-indexed line number of a heading, or None if not found.

    Uses the markdown-it-py AST so headings inside fenced code blocks are
    correctly ignored. Matching is case-insensitive.
    """
    tokens = _md.parse(text)
    for i, tok in enumerate(tokens):
        if tok.type == "heading_open" and i + 1 < len(tokens):
            inline = tokens[i + 1]
            heading_content = "".join(
                child.content for child in (inline.children or [])
            ).strip()
            if heading_content.lower() == heading_text.lower():
                return tok.map[0]
    return None


def insert_after_heading(text: str, heading: str, content: str) -> str:
    """Insert content immediately after the blank line(s) following a heading."""
    line_idx = find_heading_line(text, heading)
    if line_idx is None:
        raise ValueError(f"Heading not found: '{heading}'")
    lines = text.splitlines(keepends=True)
    insert_at = line_idx + 1
    while insert_at < len(lines) and lines[insert_at].strip() == "":
        insert_at += 1
    lines.insert(insert_at, content.rstrip("\n") + "\n\n")
    return "".join(lines)


def insert_before_heading(text: str, heading: str, content: str) -> str:
    """Insert content on the line immediately before a heading."""
    line_idx = find_heading_line(text, heading)
    if line_idx is None:
        raise ValueError(f"Heading not found: '{heading}'")
    lines = text.splitlines(keepends=True)
    lines.insert(line_idx, content.rstrip("\n") + "\n\n")
    return "".join(lines)


def append_table_row(text: str, heading: str, row: str) -> str:
    """Append a Markdown table row to the table found under a heading."""
    line_idx = find_heading_line(text, heading)
    if line_idx is None:
        raise ValueError(f"Heading not found: '{heading}'")
    lines = text.splitlines(keepends=True)
    last_table_line = None
    for i in range(line_idx + 1, len(lines)):
        stripped = lines[i].strip()
        if stripped.startswith("|") and stripped.endswith("|"):
            last_table_line = i
        elif last_table_line is not None and stripped == "":
            break
    if last_table_line is None:
        raise ValueError(f"No table found under heading '{heading}'")
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
                start_line = tok.map[1]  # line AFTER the heading
                target_level = tok.tag   # "h1", "h2", etc.
            elif start_line is not None and tok.tag == target_level:
                end_line = tok.map[0]
                break

    if start_line is None:
        raise ValueError(f"Heading not found: '{heading}'")
    end_line = end_line or len(lines)

    new_lines = lines[:start_line] + [content.rstrip("\n") + "\n"] + lines[end_line:]
    return "".join(new_lines)
