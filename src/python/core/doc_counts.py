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
"providers"/"unit"/"E2E" adjacent to the number, so a bare "25" elsewhere never
false-positives.

The unit-test count is gated as a **round-down-to-10 floor** (``unit_tests_floor``
= ``(unit // 10) * 10``), surfaced in docs as "340+ unit". This keeps the exact
``!=`` machinery while making the friction low: adding tests inside a decade
(342→349) never trips CI, yet a gross under/over-claim ("314+" when reality is
340) still fails. ``unit_tests`` itself is derived by statically counting
``def test_`` defs — exact only while the counted files use no
``@pytest.mark.parametrize`` / dynamic generation, which ``test_doc_counts.py``
enforces with an AST sentinel. ``test_mcp_server.py`` (which parametrizes) and
the E2E suite are excluded from the floor gate; the exact MCP/E2E/total numbers
live in ``testing/overview.md`` as an ungated inventory, and ``mcp_tools`` covers
the meaningful MCP number.
"""

from __future__ import annotations

import ast
import re
from dataclasses import dataclass
from pathlib import Path

# repo root: this file is src/python/core/doc_counts.py -> parents[3] == root
PROJECT_ROOT = Path(__file__).resolve().parents[3]
_MCP_SERVER = PROJECT_ROOT / "src" / "python" / "mcp_server.py"
_OBS_CLI = PROJECT_ROOT / "src" / "python" / "obs_cli.py"
_AI_PROVIDERS = PROJECT_ROOT / "src" / "python" / "ai" / "providers"
_TESTS_DIR = PROJECT_ROOT / "src" / "python" / "tests"

# Files whose ``def test_`` count is gated statically. ``test_mcp_server.py`` is
# excluded — it parametrizes, so static counting would diverge from collection.
_STATIC_COUNT_EXCLUDE = ("test_mcp_server.py",)

_TEST_DEF = re.compile(r"^[ \t]*def test_", re.MULTILINE)


def _count_test_functions(path: Path) -> int:
    """Count ``def test_`` definitions in a file (0 if it does not exist).

    Equals pytest's collected count only when the file uses no parametrize /
    dynamic generation — guaranteed for gated files by the sentinel in
    ``tests/test_doc_counts.py``.
    """
    if not path.exists():
        return 0
    return len(_TEST_DEF.findall(path.read_text(encoding="utf-8")))


def _count_obs_commands(path: Path = _OBS_CLI) -> int:
    """Count **runnable** ``obs`` commands (leaf subcommands) from argparse.

    A "command" is any terminal ``obs ...`` invocation a user can actually run —
    e.g. ``obs scan``, ``obs ai duplicates``, ``obs research board``. Group
    parsers that only hold subcommands (``ai``, ``config``, ``research``, ``db``,
    ``bridge``, and the nested ``zotero``/``pdf``/``course``/``manuscript``/
    ``bib`` families) are NOT counted themselves — only their leaves are.

    Derived statically from ``obs_cli.py`` (AST), so it cannot drift from code:
      * every ``X.add_parser('name')`` defines a command ``name``;
      * a parser is a *group* (excluded) iff its assigned variable later
        receives ``.add_subparsers()``.
    Returns ``leaves = all add_parser names − group names`` (0 if unparseable).
    """
    if not path.exists():
        return 0
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except (OSError, SyntaxError):
        return 0

    # Parser variables that nest subcommands (i.e. groups).
    parsers_with_subs: set[str] = set()
    # command-name -> variable it was assigned to (only assigned add_parser calls).
    assigned: dict[str, str] = {}
    all_names: list[str] = []

    for node in ast.walk(tree):
        if not (isinstance(node, ast.Call)
                and isinstance(node.func, ast.Attribute)):
            continue
        attr = node.func.attr
        if attr == "add_subparsers" and isinstance(node.func.value, ast.Name):
            parsers_with_subs.add(node.func.value.id)
        elif attr == "add_parser" and node.args and isinstance(node.args[0], ast.Constant):
            all_names.append(node.args[0].value)

    for node in ast.walk(tree):
        if (isinstance(node, ast.Assign) and isinstance(node.value, ast.Call)
                and isinstance(node.value.func, ast.Attribute)
                and node.value.func.attr == "add_parser"
                and node.value.args
                and isinstance(node.value.args[0], ast.Constant)):
            for t in node.targets:
                if isinstance(t, ast.Name):
                    assigned[node.value.args[0].value] = t.id

    group_names = {name for name, var in assigned.items() if var in parsers_with_subs}
    return sum(1 for n in all_names if n not in group_names)


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
    unit_tests = 0
    if _TESTS_DIR.is_dir():
        unit_tests = sum(
            _count_test_functions(p)
            for p in _TESTS_DIR.glob("test_*.py")
            if p.name not in _STATIC_COUNT_EXCLUDE
        )
    e2e_dir = _TESTS_DIR / "e2e"
    e2e_tests = 0
    if e2e_dir.is_dir():
        e2e_tests = sum(_count_test_functions(p) for p in e2e_dir.glob("test_*.py"))
    return {
        "mcp_tools": mcp_tools,
        "mcp_resources": mcp_resources,
        "ai_providers": ai_providers,
        "obs_commands": _count_obs_commands(),
        "unit_tests": unit_tests,
        "e2e_tests": e2e_tests,
        # Gated value: round down to 10 so "340+" tolerates additions within a
        # decade but still catches gross drift. See module docstring.
        "unit_tests_floor": (unit_tests // 10) * 10,
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
    # Runnable obs commands (leaf subcommands). Anchored on a bold "Commands"
    # label, the "obs commands" noun, or the "(N top-level …)" breakdown so the
    # many contextual "3 commands" / "10 commands" learning-level mentions never
    # match. See _count_obs_commands for the definition.
    "obs_commands": (
        r"\*\*Commands:?\*\*:?\s*(\d+)",
        r"all (\d+) `?obs`? commands",
        r"(\d+) commands \(17 top-level",
    ),
    # Unit-test FLOOR — anchored on "N+ unit" so bare totals ("454 pytest"),
    # exact inventory cells ("342"), and "113 MCP unit" never match.
    "unit_tests_floor": (
        r"(\d+)\+\s+unit",
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
        print(f"\033[32m✓ counts aligned\033[0m  commands={counts['obs_commands']} "
              f"tools={counts['mcp_tools']} resources={counts['mcp_resources']} "
              f"providers={counts['ai_providers']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
