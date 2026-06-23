"""Documentation count-consistency: the single source of truth for "how many".

Motivation: v4.0.0 shipped docs claiming "25 MCP tools" while ``mcp_server.py``
exposed 38 — no gate caught it. This module derives the authoritative counts
from CODE (not from prose) and finds doc surfaces whose stated numbers disagree.

It is the shared core for three thin consumers (zero duplication, per the
project's three-layer rule):
  - ``scripts/validate-counts.sh``  — CLI wrapper / ``--fix``
  - ``core.doctor._check_doc_counts`` — the ``obs doctor`` ``doc-counts`` check
  - ``tests/test_doc_counts.py``    — the CI gate (drift cannot merge)

Anchored patterns only — every regex requires the word "tools"/"resources"/
"providers" adjacent to the number, so a bare "25" elsewhere never false-positives.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

# repo root: this file is src/python/core/doc_counts.py -> parents[3] == root
PROJECT_ROOT = Path(__file__).resolve().parents[3]
_MCP_SERVER = PROJECT_ROOT / "src" / "python" / "mcp_server.py"
_AI_PROVIDERS = PROJECT_ROOT / "src" / "python" / "ai" / "providers"


# ---------------------------------------------------------------------------
# Source of truth (derived from code, never from docs)
# ---------------------------------------------------------------------------

def source_counts() -> dict[str, int]:
    """Return the authoritative counts derived from source code."""
    server = _MCP_SERVER.read_text(encoding="utf-8") if _MCP_SERVER.exists() else ""
    mcp_tools = len(re.findall(r"^\s*@mcp\.tool", server, re.MULTILINE))
    mcp_resources = len(re.findall(r"^\s*@mcp\.resource", server, re.MULTILINE))
    ai_providers = 0
    if _AI_PROVIDERS.is_dir():
        ai_providers = sum(
            1
            for p in _AI_PROVIDERS.glob("*.py")
            if p.stem not in ("__init__", "base")
        )
    return {
        "mcp_tools": mcp_tools,
        "mcp_resources": mcp_resources,
        "ai_providers": ai_providers,
    }


# ---------------------------------------------------------------------------
# Surfaces + anchored patterns
# ---------------------------------------------------------------------------

# Doc files that cite these counts. Relative to PROJECT_ROOT.
# NOTE: .STATUS and CHANGELOG/changelog are deliberately EXCLUDED — they are
# append-only logs full of historical counts ("v3.3.0 … 20 tools", "9 MCP tools
# resolved …") that are correct-for-their-time and must not be flagged. Only
# current-state, user-facing surfaces are gated.
SURFACES: tuple[str, ...] = (
    "README.md",
    "MCP_README.md",
    "CLAUDE.md",
    "docs_mkdocs/index.md",
    "docs_mkdocs/cli-reference.md",
    "docs_mkdocs/refcard.md",
    "docs_mkdocs/claude-integration.md",
    "docs_mkdocs/workflows.md",
    "docs_mkdocs/developer/architecture.md",
    "docs_mkdocs/developer/api-reference.md",
    "docs_mkdocs/developer/testing/overview.md",
    "docs_mkdocs/tutorials/index.md",
    "docs_mkdocs/tutorials/claude-mcp.md",
    "docs/user/cli-reference.md",
)

# metric_key -> list of regexes, each with ONE capture group = the stated number.
# Every pattern anchors on the noun so bare numbers never match.
_PATTERNS: dict[str, tuple[str, ...]] = {
    "mcp_tools": (
        r"(\d+)\s+MCP tools",
        r"\*\*MCP Tools\*\*:?\s*(\d+)",
        r"MCP Tools:\*\*\s*(\d+)",
        r"\*\*Tools:\*\*\s*(\d+)",
        r"Available Tools \((\d+)\)",
        r"exposes \*{0,2}(\d+) tools",
        r"all (\d+) tools",
        r"all (\d+) MCP tools",
        r"FastMCP, (\d+) tools",
        r"(\d+) tools · \d+ resources",
        r"(\d+) MCP tools in \d+ groups",
        r"setup \((\d+) tools\)",
    ),
    "mcp_resources": (
        r"· (\d+) resources",
        r"and \*{0,2}(\d+)\*{0,2} resources",
        r"(\d+) tools and (\d+) resources",  # 2nd group handled below
    ),
    "ai_providers": (
        r"\*\*AI Providers:\*\*\s*(\d+)",
        r"\*\*AI Providers\*\*:?\s*(\d+)",
        r"(\d+) AI [Pp]roviders",
    ),
}

# Lines that legitimately cite a historical/other count — never flagged.
# (Release-notes sections, the changelog, and the spec describing the bug.)
_SKIP_SUBSTRINGS: tuple[str, ...] = (
    "since v3.3.0",   # historical capability note
    "25 core",        # "38 (25 core + 13 research)" — the 25 is a sub-count
)


@dataclass(frozen=True)
class Mismatch:
    """One doc line whose stated count disagrees with the source of truth."""

    file: str
    line: int
    metric: str
    stated: int
    expected: int
    text: str


def _resource_value(metric: str, m: re.Match) -> int | None:
    """Extract the count for ``metric`` from a regex match, handling the
    two-group "(N) tools and (M) resources" resource pattern."""
    if metric == "mcp_resources" and m.re.groups == 2:
        return int(m.group(2))
    return int(m.group(1))


def find_mismatches(counts: dict[str, int] | None = None) -> list[Mismatch]:
    """Scan all surfaces; return every stated count that disagrees with source."""
    counts = counts or source_counts()
    out: list[Mismatch] = []
    for rel in SURFACES:
        path = PROJECT_ROOT / rel
        if not path.exists():
            continue
        for i, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if any(s in raw for s in _SKIP_SUBSTRINGS):
                continue
            for metric, patterns in _PATTERNS.items():
                expected = counts[metric]
                for pat in patterns:
                    for m in re.finditer(pat, raw):
                        stated = _resource_value(metric, m)
                        if stated is None:
                            continue
                        if stated != expected:
                            out.append(
                                Mismatch(rel, i, metric, stated, expected, raw.strip())
                            )
    return out


def apply_fixes(counts: dict[str, int] | None = None) -> int:
    """Rewrite surfaces so every stated count matches source. Returns # of fixes.

    Replaces only the captured number inside each anchored match, so unrelated
    numbers on the same line are never touched.
    """
    counts = counts or source_counts()
    fixed = 0
    for rel in SURFACES:
        path = PROJECT_ROOT / rel
        if not path.exists():
            continue
        lines = path.read_text(encoding="utf-8").splitlines(keepends=True)
        changed = False
        for idx, raw in enumerate(lines):
            if any(s in raw for s in _SKIP_SUBSTRINGS):
                continue
            new = raw
            for metric, patterns in _PATTERNS.items():
                expected = str(counts[metric])
                grp = 2 if metric == "mcp_resources" else 1

                def _sub(m: re.Match, _g=grp, _exp=expected) -> str:
                    if m.group(_g) == _exp:
                        return m.group(0)
                    s, e = m.span(_g)
                    return m.group(0)[: s - m.start()] + _exp + m.group(0)[e - m.start():]

                for pat in patterns:
                    if re.search(pat, new) and pat.count("(\\d+)") >= grp:
                        new = re.sub(pat, _sub, new)
            if new != raw:
                lines[idx] = new
                changed = True
                fixed += 1
        if changed:
            path.write_text("".join(lines), encoding="utf-8")
    return fixed


def main(argv: list[str] | None = None) -> int:
    """CLI: report count mismatches; ``--fix`` to auto-correct, ``--quiet`` for
    exit-code-only. Exit 0 = aligned, 1 = drift found."""
    import sys

    argv = sys.argv[1:] if argv is None else argv
    quiet = "--quiet" in argv
    do_fix = "--fix" in argv
    counts = source_counts()

    if do_fix:
        n = apply_fixes(counts)
        if not quiet:
            print(f"validate-counts: applied {n} fix(es) to match source {counts}")

    ms = find_mismatches(counts)
    if ms:
        if not quiet:
            print(f"\033[31m✗ {len(ms)} count mismatch(es)\033[0m  (source: {counts})")
            for m in ms:
                print(f"  {m.file}:{m.line}  {m.metric} says {m.stated} (expected {m.expected})")
                print(f"      {m.text}")
            print("  fix with: scripts/validate-counts.sh --fix")
        return 1
    if not quiet:
        print(f"\033[32m✓ counts aligned\033[0m  tools={counts['mcp_tools']} "
              f"resources={counts['mcp_resources']} providers={counts['ai_providers']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
