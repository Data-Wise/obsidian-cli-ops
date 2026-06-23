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
