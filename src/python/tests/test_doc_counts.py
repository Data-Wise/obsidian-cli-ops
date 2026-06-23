"""Doc count-consistency gate — drift cannot merge.

Mirrors ``test_version_consistency.py`` but for COUNTS (MCP tools/resources, AI
providers) instead of the version string. Born from v4.0.0 shipping "25 MCP
tools" while ``mcp_server.py`` exposed 38. Shares its logic with
``scripts/validate-counts.sh`` and the ``obs doctor`` ``doc-counts`` check via
the single source module ``core.doc_counts``.
"""

from core.doc_counts import source_counts, find_mismatches


class TestDocCounts:
    """Stated counts in user-facing docs must match the source of truth."""

    def test_source_counts_sane(self):
        """Source counts are positive and internally plausible."""
        c = source_counts()
        assert c["mcp_tools"] > 0, "no @mcp.tool found in mcp_server.py"
        assert c["mcp_resources"] >= 0
        assert c["ai_providers"] > 0
        assert c["mcp_tools"] >= c["mcp_resources"]
        assert c["unit_tests"] > 0, "no unit test functions counted"
        assert c["e2e_tests"] >= 0

    def test_static_test_count_assumption_holds(self):
        """Sentinel: gated test files must not parametrize / dynamically generate.

        ``unit_tests``/``e2e_tests`` are derived by statically counting
        ``def test_`` — which equals pytest's collected count ONLY without
        parametrize. If this fails, a gated file gained parametrize: upgrade the
        deriver in ``core.doc_counts`` (e.g. to a collection-based count) or add
        the file to ``_STATIC_COUNT_EXCLUDE``.

        Detection is AST-based, not textual — so this file naming "parametrize"
        in its own prose/strings never flags itself (only real decorators and a
        real ``pytest_generate_tests`` def count).
        """
        import ast

        from core.doc_counts import _STATIC_COUNT_EXCLUDE, _TESTS_DIR

        def _uses_dynamic_generation(path) -> bool:
            tree = ast.parse(path.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if (
                    isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
                    and node.name == "pytest_generate_tests"
                ):
                    return True
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    for dec in node.decorator_list:
                        target = dec.func if isinstance(dec, ast.Call) else dec
                        attr = getattr(target, "attr", None) or getattr(
                            target, "id", None
                        )
                        if attr == "parametrize":
                            return True
            return False

        gated = [
            p
            for p in _TESTS_DIR.glob("test_*.py")
            if p.name not in _STATIC_COUNT_EXCLUDE
        ]
        gated += list((_TESTS_DIR / "e2e").glob("test_*.py"))
        offenders = [p.name for p in gated if _uses_dynamic_generation(p)]
        assert not offenders, (
            "static test-count deriver invalidated by parametrize in: "
            f"{offenders} — upgrade core.doc_counts test counting or exclude them."
        )

    def test_docs_match_source(self):
        """THE GATE: every documented count matches the source of truth.

        If this fails, run ``scripts/validate-counts.sh --fix``.
        """
        mismatches = find_mismatches()
        detail = "\n".join(
            f"  {m.file}:{m.line}  {m.metric} says {m.stated} (expected {m.expected})"
            f"\n      {m.text}"
            for m in mismatches
        )
        assert not mismatches, (
            f"{len(mismatches)} doc count mismatch(es) — "
            f"fix with `scripts/validate-counts.sh --fix`:\n{detail}"
        )

    def test_drift_is_detected(self):
        """Sanity: a deliberately-wrong source count surfaces mismatches —
        proves the gate actually bites (not vacuously passing)."""
        real = source_counts()
        bogus = {**real, "mcp_tools": real["mcp_tools"] + 999}
        assert find_mismatches(bogus), (
            "find_mismatches did not flag a fabricated count — the gate is inert"
        )

    def test_doctor_doc_counts_check_passes(self):
        """The `obs doctor` doc-counts check reports pass when docs are aligned."""
        from core.doctor import run_checks

        results = [r for r in run_checks(layers=["docs"]) if r.id == "doc-counts"]
        assert results, "doctor did not emit a doc-counts check"
        assert results[0].status == "pass", (
            f"doc-counts not passing: {results[0].message}"
        )
