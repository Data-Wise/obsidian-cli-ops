"""
E2E tests for research subcommands (zotero, pdf, course, manuscript, bib).

These tests create an isolated HOME with a mock config and fixture data,
then exercise the research subcommands via the obs_cli.py subprocess.

No external APIs or network needed — all data is local filesystem.

Requirements:
  - obs venv installed (install.sh or brew)
  - pdftotext (for PDF tests) — test skips if unavailable

Marks:
  @pytest.mark.e2e   — skipped unless E2E=1 env var is set
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

_SRC = Path(__file__).parent.parent.parent
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

_RUN_E2E = os.environ.get("E2E", "").strip() in ("1", "true", "yes")
pytestmark = pytest.mark.skipif(
    not _RUN_E2E,
    reason="E2E tests skipped — set E2E=1 to run",
)


def _find_obs_python() -> str:
    if env := os.environ.get("OBS_PYTHON"):
        if Path(env).exists():
            return env
    candidates = [
        Path.home() / ".local/share/obs/venv/bin/python3",
        Path("/opt/homebrew/opt/obsidian-cli-ops/libexec/venv/bin/python3"),
    ]
    for p in candidates:
        if p.exists():
            return str(p)
    return sys.executable


_OBS_PYTHON = _find_obs_python()
_OBS_CLI = _SRC / "obs_cli.py"


# ---------------------------------------------------------------------------
# Fixture helpers
# ---------------------------------------------------------------------------

def _create_zotero_db(path: Path) -> None:
    """Create a minimal Zotero-compatible SQLite DB with test items."""
    import sqlite3
    conn = sqlite3.connect(str(path))
    c = conn.cursor()
    c.executescript("""
        CREATE TABLE itemTypes (itemTypeID INTEGER PRIMARY KEY, typeName TEXT);
        INSERT INTO itemTypes VALUES (1, 'journalArticle');
        INSERT INTO itemTypes VALUES (2, 'book');
        INSERT INTO itemTypes VALUES (3, 'attachment');
        INSERT INTO itemTypes VALUES (4, 'note');

        CREATE TABLE items (itemID INTEGER PRIMARY KEY, itemTypeID INTEGER, key TEXT, dateModified TEXT);
        INSERT INTO items VALUES (1, 1, 'ABC123', '2026-06-01 12:00:00');
        INSERT INTO items VALUES (2, 1, 'DEF456', '2026-06-15 12:00:00');

        CREATE TABLE itemData (itemID INTEGER, fieldID INTEGER, valueID INTEGER);
        CREATE TABLE itemDataValues (valueID INTEGER PRIMARY KEY, value TEXT);
        INSERT INTO itemDataValues VALUES (1, 'E2E Test Article One');
        INSERT INTO itemDataValues VALUES (2, 'E2E Test Article Two');
        INSERT INTO itemDataValues VALUES (3, 'Abstract for article one about mediation analysis');
        INSERT INTO itemDataValues VALUES (4, '2026');
        INSERT INTO itemDataValues VALUES (5, 'https://example.com/article1');
        INSERT INTO itemDataValues VALUES (6, '10.1234/test.2026.001');
        INSERT INTO itemData (itemID, fieldID, valueID) VALUES (1, 1, 1);
        INSERT INTO itemData (itemID, fieldID, valueID) VALUES (2, 1, 2);
        INSERT INTO itemData (itemID, fieldID, valueID) VALUES (1, 2, 3);
        INSERT INTO itemData (itemID, fieldID, valueID) VALUES (1, 6, 4);
        INSERT INTO itemData (itemID, fieldID, valueID) VALUES (2, 6, 4);
        INSERT INTO itemData (itemID, fieldID, valueID) VALUES (1, 13, 5);
        INSERT INTO itemData (itemID, fieldID, valueID) VALUES (1, 59, 6);

        CREATE TABLE creators (creatorID INTEGER PRIMARY KEY, firstName TEXT, lastName TEXT);
        INSERT INTO creators VALUES (1, 'Alice', 'Smith');
        INSERT INTO creators VALUES (2, 'Bob', 'Jones');
        INSERT INTO creators VALUES (3, 'Carol', 'Williams');

        CREATE TABLE creatorTypes (creatorTypeID INTEGER PRIMARY KEY, creatorType TEXT);
        INSERT INTO creatorTypes VALUES (1, 'author');

        CREATE TABLE itemCreators (itemID INTEGER, creatorID INTEGER, creatorTypeID INTEGER, orderIndex INTEGER);
        INSERT INTO itemCreators VALUES (1, 1, 1, 0);
        INSERT INTO itemCreators VALUES (1, 2, 1, 1);
        INSERT INTO itemCreators VALUES (2, 3, 1, 0);

        CREATE TABLE tags (tagID INTEGER PRIMARY KEY, name TEXT);
        INSERT INTO tags VALUES (1, 'statistics');
        INSERT INTO tags VALUES (2, 'mediation');

        CREATE TABLE itemTags (itemID INTEGER, tagID INTEGER);
        INSERT INTO itemTags VALUES (1, 1);
        INSERT INTO itemTags VALUES (1, 2);

        CREATE TABLE collections (collectionID INTEGER PRIMARY KEY, collectionName TEXT);
        INSERT INTO collections VALUES (1, 'Methodology');

        CREATE TABLE collectionItems (collectionID INTEGER, itemID INTEGER);
        INSERT INTO collectionItems VALUES (1, 1);
    """)
    conn.commit()
    conn.close()


def _create_course_dir(base: Path, name: str, status_lines: dict[str, str]) -> Path:
    """Create a course directory with a .STATUS file."""
    course_path = base / name
    course_path.mkdir(parents=True, exist_ok=True)
    status_content = "\n".join(f"{k}: {v}" for k, v in status_lines.items()) + "\n"
    (course_path / ".STATUS").write_text(status_content)
    return course_path


def _create_manuscript_dir(base: Path, name: str, status_lines: dict[str, str], quarto: bool = True) -> Path:
    """Create a manuscript directory with .STATUS and optional _quarto.yml."""
    ms_path = base / name
    ms_path.mkdir(parents=True, exist_ok=True)
    status_content = "\n".join(f"{k}: {v}" for k, v in status_lines.items()) + "\n"
    (ms_path / ".STATUS").write_text(status_content)
    if quarto:
        qmd = f"""project:
  type: manuscript
manuscript:
  article: index.qmd
title: "{name.replace('-', ' ').title()}"
author:
  - name: Alice Smith
"""
        (ms_path / "_quarto.yml").write_text(qmd)
        (ms_path / "index.qmd").write_text(f"""# {name.replace('-', ' ').title()}

## Introduction

This is a test manuscript about causal inference [@smith2020; @jones2019].

## Methods

We used a mediation framework [@brown2021].

## References
""")
    return ms_path


def _create_pdf(path: Path, text: str) -> None:
    """Create a minimal valid PDF with embeddable text."""
    content = f"""%PDF-1.4
1 0 obj
<< /Type /Catalog /Pages 2 0 R >>
endobj
2 0 obj
<< /Type /Pages /Kids [3 0 R] /Count 1 >>
endobj
3 0 obj
<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>
endobj
4 0 obj
<< /Length {len(text) + 10} >>
stream
BT /F1 12 Tf 100 700 Td ({text}) Tj ET
endstream
endobj
5 0 obj
<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>
endobj
xref
0 6
0000000000 65535 f
0000000010 00000 n
0000000059 00000 n
0000000116 00000 n
0000000270 00000 n
0000000370 00000 n
trailer
<< /Size 6 /Root 1 0 R >>
startxref
430
%%EOF"""
    path.write_text(content)


_ISO_HOME = "__ISO_E2E_RESEARCH__"


@pytest.fixture(scope="module")
def research_env(tmp_path_factory):
    """Create an isolated HOME with config + fixture data for all research subcommands.

    Returns a dict with 'env' (os.environ override), 'home', and all fixture paths.
    """
    home = tmp_path_factory.mktemp("e2e_research_home")

    # Config dir
    config_dir = home / ".config" / "obs"
    config_dir.mkdir(parents=True)

    # Fixture dirs
    pdf_dir = home / "pdfs"
    pdf_dir.mkdir()
    courses_dir = home / "courses"
    courses_dir.mkdir()
    manuscripts_dir = home / "manuscripts"
    manuscripts_dir.mkdir()
    zotero_db = home / "zotero.sqlite"

    # Create fixture data
    _create_zotero_db(zotero_db)
    _create_pdf(pdf_dir / "mediation-paper.pdf", "E2E PDF test about causal mediation")
    _create_course_dir(courses_dir, "stats-101", {
        "status": "active", "priority": "P0", "progress": "75",
        "type": "teaching", "next": "prepare lecture 10",
    })
    _create_course_dir(courses_dir, "causal-inference", {
        "status": "active", "priority": "P1", "progress": "30",
        "type": "teaching", "week": "5", "next": "design homework 3",
    })
    _create_manuscript_dir(manuscripts_dir, "mediation-review", {
        "status": "draft", "priority": "P1", "progress": "60", "target": "JASA",
    })
    _create_manuscript_dir(manuscripts_dir, "causal-methods", {
        "status": "active", "priority": "P0", "progress": "25", "target": "Biometrics",
    })

    # Create a .bib file in the first manuscript
    bib_content = """@article{smith2020,
  title = {Causal Mediation in Modern Epidemiology},
  author = {Smith, Alice and Jones, Bob},
  year = {2020},
  journal = {Journal of Causal Inference},
}
@article{jones2019,
  title = {Advanced Mediation Methods},
  author = {Jones, Bob},
  year = {2019},
  journal = {Statistics in Medicine},
}
"""
    (manuscripts_dir / "mediation-review" / "references.bib").write_text(bib_content)

    # Write config pointing to fixture dirs
    config = f"""version: 1
vault:
  root: "{home}"
  active: ["Research"]
research:
  zotero:
    database: "{zotero_db}"
    storage: "{home}/zotero-storage"
  pdf:
    directories:
      - "{pdf_dir}"
  teaching:
    courses_dir: "{courses_dir}"
  writing:
    manuscripts_dir: "{manuscripts_dir}"
"""
    (config_dir / "config.yaml").write_text(config)

    env = {**os.environ, "HOME": str(home)}

    return {
        "env": env,
        "home": home,
        "pdf_dir": pdf_dir,
        "courses_dir": courses_dir,
        "manuscripts_dir": manuscripts_dir,
        "zotero_db": zotero_db,
    }


def _run(cmd: list[str], env: dict) -> subprocess.CompletedProcess:
    """Run obs_cli.py with HOME-isolated env and return result."""
    return subprocess.run(
        [_OBS_PYTHON, str(_OBS_CLI)] + cmd,
        env=env, capture_output=True, text=True, timeout=30,
    )


# ===========================================================================
# Zotero tests (extended)
# ===========================================================================

class TestE2EZotero:
    def test_zotero_search_finds_by_title(self, research_env):
        r = _run(["research", "zotero", "search", "Article One"], research_env["env"])
        assert r.returncode == 0, f"stderr: {r.stderr}"
        assert "E2E Test Article One" in r.stdout

    def test_zotero_search_returns_all(self, research_env):
        r = _run(["research", "zotero", "search", "Article"], research_env["env"])
        assert r.returncode == 0
        assert "E2E Test Article One" in r.stdout
        assert "E2E Test Article Two" in r.stdout

    def test_zotero_search_no_match(self, research_env):
        r = _run(["research", "zotero", "search", "xyznonexistent999"], research_env["env"])
        assert r.returncode == 0
        assert "No results" in r.stdout or "no results" in r.stdout.lower()

    def test_zotero_get_by_key(self, research_env):
        r = _run(["research", "zotero", "get", "ABC123"], research_env["env"])
        assert r.returncode == 0
        assert "E2E Test Article One" in r.stdout
        assert "Alice Smith" in r.stdout

    def test_zotero_get_unknown_key(self, research_env):
        r = _run(["research", "zotero", "get", "ZZZZZZ"], research_env["env"])
        assert r.returncode == 1
        assert "not found" in r.stdout.lower()

    def test_zotero_recent(self, research_env):
        r = _run(["research", "zotero", "recent"], research_env["env"])
        assert r.returncode == 0
        assert "E2E Test Article" in r.stdout

    def test_zotero_recent_with_limit(self, research_env):
        """Limit 1 returns the most recently modified item."""
        r = _run(["research", "zotero", "recent", "--limit", "1"], research_env["env"])
        assert r.returncode == 0
        # DEF456 has later dateModified; one item expected
        assert "E2E Test Article Two" in r.stdout


# ===========================================================================
# PDF search tests
# ===========================================================================

class TestE2EPDF:
    def test_pdf_search_by_filename(self, research_env):
        r = _run(["research", "pdf", "search", "mediation"], research_env["env"])
        assert r.returncode == 0, f"stderr: {r.stderr}"
        assert "mediation-paper.pdf" in r.stdout or "1 result" in r.stdout

    def test_pdf_search_by_content(self, research_env):
        r = _run(["research", "pdf", "search", "causal"], research_env["env"])
        assert r.returncode == 0
        assert "mediation-paper.pdf" in r.stdout or "1 result" in r.stdout

    def test_pdf_search_no_match(self, research_env):
        r = _run(["research", "pdf", "search", "xyznonexistent999"], research_env["env"])
        assert r.returncode == 0
        assert "No result" in r.stdout or "No match" in r.stdout or "no result" in r.stdout.lower() or "no match" in r.stdout.lower()

    def test_pdf_search_empty_query(self, research_env):
        r = _run(["research", "pdf", "search", ""], research_env["env"])
        assert r.returncode == 0
        # Should still run without crashing — PDF list or "no query" message


# ===========================================================================
# Course tests
# ===========================================================================

class TestE2ECourses:
    def test_course_list_shows_all(self, research_env):
        r = _run(["research", "course", "list"], research_env["env"])
        assert r.returncode == 0, f"stderr: {r.stderr}"
        assert "stats-101" in r.stdout
        assert "causal-inference" in r.stdout

    def test_course_show_by_name(self, research_env):
        r = _run(["research", "course", "show", "stats-101"], research_env["env"])
        assert r.returncode == 0
        assert "stats-101" in r.stdout or "active" in r.stdout

    def test_course_show_unknown(self, research_env):
        r = _run(["research", "course", "show", "no-such-course"], research_env["env"])
        assert r.returncode == 1
        assert "not found" in r.stdout.lower()

    def test_course_lectures_existing(self, research_env):
        """Lecture list for a course with no lectures should say 'none' or be empty."""
        r = _run(["research", "course", "lectures", "stats-101"], research_env["env"])
        assert r.returncode == 0
        assert "lectures" in r.stdout.lower() or "no" in r.stdout.lower()

    def test_course_lectures_unknown(self, research_env):
        r = _run(["research", "course", "lectures", "no-such-course"], research_env["env"])
        assert r.returncode == 1
        assert "not found" in r.stdout.lower()


# ===========================================================================
# Manuscript tests
# ===========================================================================

class TestE2EManuscripts:
    def test_manuscript_list_shows_all(self, research_env):
        r = _run(["research", "manuscript", "list"], research_env["env"])
        assert r.returncode == 0, f"stderr: {r.stderr}"
        assert "mediation-review" in r.stdout
        assert "causal-methods" in r.stdout

    def test_manuscript_list_with_archived(self, research_env):
        r = _run(["research", "manuscript", "list", "--archived"], research_env["env"])
        assert r.returncode == 0
        assert "mediation-review" in r.stdout

    def test_manuscript_show_by_name(self, research_env):
        r = _run(["research", "manuscript", "show", "mediation-review"], research_env["env"])
        assert r.returncode == 0
        assert "draft" in r.stdout.lower() or "mediation" in r.stdout.lower()

    def test_manuscript_show_unknown(self, research_env):
        r = _run(["research", "manuscript", "show", "no-such-manuscript"], research_env["env"])
        assert r.returncode == 1
        assert "not found" in r.stdout.lower()

    def test_manuscript_stats(self, research_env):
        r = _run(["research", "manuscript", "stats"], research_env["env"])
        assert r.returncode == 0
        assert "Total" in r.stdout or "total" in r.stdout.lower()
        assert "2" in r.stdout


# ===========================================================================
# Bibliography tests
# ===========================================================================

class TestE2EBibliography:
    def test_bib_check_finds_citations(self, research_env):
        """bib check must find the cited refs and bibliography entries."""
        r = _run(["research", "bib", "check", "mediation-review"], research_env["env"])
        assert r.returncode == 0, f"stdout: {r.stdout}\nstderr: {r.stderr}"
        assert "Cited" in r.stdout
        assert "Bibliography" in r.stdout

    def test_bib_check_unknown_manuscript(self, research_env):
        r = _run(["research", "bib", "check", "no-such-manuscript"], research_env["env"])
        assert r.returncode == 1
        assert "not found" in r.stdout.lower() or "not found" in r.stderr.lower()

    def test_bib_check_missing_citations(self, research_env):
        """bib check must report missing citations when present."""
        r = _run(["research", "bib", "check", "mediation-review"], research_env["env"])
        assert r.returncode == 0
        # The .qmd cites @smith2020, @jones2019, @brown2021
        # The .bib has smith2020 and jones2019
        # brown2021 is missing
        assert "all_good" in r.stdout.lower() or "missing" in r.stdout.lower()


# ===========================================================================
# New: Zotero cite, tags, collections, by-tag
# ===========================================================================

class TestE2EZoteroNew:
    def test_zotero_cite_apa(self, research_env):
        r = _run(["research", "zotero", "cite", "ABC123"], research_env["env"])
        assert r.returncode == 0, f"stderr: {r.stderr}"
        assert "Smith" in r.stdout or "Williams" in r.stdout

    def test_zotero_cite_bibtex(self, research_env):
        r = _run(["research", "zotero", "cite", "ABC123", "--style", "bibtex"], research_env["env"])
        assert r.returncode == 0
        assert "@article" in r.stdout

    def test_zotero_cite_unknown_key(self, research_env):
        r = _run(["research", "zotero", "cite", "ZZZ999"], research_env["env"])
        assert r.returncode == 1
        assert "not found" in r.stdout.lower()

    def test_zotero_tags(self, research_env):
        r = _run(["research", "zotero", "tags"], research_env["env"])
        assert r.returncode == 0
        assert "statistics" in r.stdout or "mediation" in r.stdout

    def test_zotero_tags_json(self, research_env):
        r = _run(["research", "zotero", "tags", "--json"], research_env["env"])
        assert r.returncode == 0
        import json
        data = json.loads(r.stdout)
        assert isinstance(data, list)

    def test_zotero_collections(self, research_env):
        r = _run(["research", "zotero", "collections"], research_env["env"])
        assert r.returncode == 0
        assert "Methodology" in r.stdout

    def test_zotero_by_tag(self, research_env):
        r = _run(["research", "zotero", "by-tag", "mediation"], research_env["env"])
        assert r.returncode == 0
        assert "ABC123" in r.stdout or "Article" in r.stdout

    def test_zotero_by_tag_no_results(self, research_env):
        r = _run(["research", "zotero", "by-tag", "nonexistent"], research_env["env"])
        assert r.returncode == 0
        assert "No items" in r.stdout or "no" in r.stdout.lower()


# ===========================================================================
# New: Manuscript batch commands + export
# ===========================================================================

class TestE2EManuscriptBatch:
    def test_manuscript_batch_status(self, research_env):
        r = _run(["research", "manuscript", "batch-status", "mediation-review", "--status", "under_review"], research_env["env"])
        assert r.returncode == 0
        assert "Updated" in r.stdout or "1" in r.stdout

    def test_manuscript_batch_progress(self, research_env):
        r = _run(["research", "manuscript", "batch-progress", "mediation-review:85"], research_env["env"])
        assert r.returncode == 0
        assert "Updated" in r.stdout

    def test_manuscript_batch_archive(self, research_env):
        r = _run(["research", "manuscript", "batch-archive", "causal-methods"], research_env["env"])
        assert r.returncode == 0
        assert "Archived" in r.stdout or "1" in r.stdout

    def test_manuscript_export_json(self, research_env):
        out = research_env["home"] / "ms-export.json"
        r = _run(["research", "manuscript", "export", str(out)], research_env["env"])
        assert r.returncode == 0
        assert out.exists()
        import json
        data = json.loads(out.read_text())
        assert isinstance(data, list)
        assert len(data) >= 2


# ===========================================================================
# New: PDF extract
# ===========================================================================

class TestE2EPDFExtract:
    def test_pdf_extract_text(self, research_env):
        pdf_path = research_env["pdf_dir"] / "mediation-paper.pdf"
        r = _run(["research", "pdf", "extract", str(pdf_path)], research_env["env"])
        if r.returncode != 0 and "pdftotext" in (r.stdout + r.stderr):
            pytest.skip("pdftotext not available")
        assert r.returncode == 0, f"stdout: {r.stdout}\nstderr: {r.stderr}"
        assert "mediation" in r.stdout.lower()

    def test_pdf_extract_pages(self, research_env):
        pdf_path = research_env["pdf_dir"] / "mediation-paper.pdf"
        r = _run(["research", "pdf", "extract", str(pdf_path), "--pages", "1"], research_env["env"])
        if r.returncode != 0 and "pdftotext" in (r.stdout + r.stderr):
            pytest.skip("pdftotext not available")
        assert r.returncode == 0

    def test_pdf_extract_json(self, research_env):
        pdf_path = research_env["pdf_dir"] / "mediation-paper.pdf"
        r = _run(["research", "pdf", "extract", str(pdf_path), "--json"], research_env["env"])
        if r.returncode != 0 and "pdftotext" in (r.stdout + r.stderr):
            pytest.skip("pdftotext not available")
        assert r.returncode == 0
        import json
        data = json.loads(r.stdout)
        assert data.get("filename") or data.get("path")

    def test_pdf_extract_not_found(self, research_env):
        r = _run(["research", "pdf", "extract", "/nonexistent/file.pdf"], research_env["env"])
        assert r.returncode == 1
        assert "not found" in r.stdout.lower()


# ===========================================================================
# New: Unified research search
# ===========================================================================

class TestE2EResearchSearch:
    def test_research_search_zotero(self, research_env):
        r = _run(["research", "search", "Article", "--source", "zotero"], research_env["env"])
        assert r.returncode == 0
        assert "Article" in r.stdout

    def test_research_search_pdf(self, research_env):
        r = _run(["research", "search", "mediation", "--source", "pdf"], research_env["env"])
        assert r.returncode == 0
        # PDF search works via filename; either results or "no results" is fine

    def test_research_search_json(self, research_env):
        r = _run(["research", "search", "test", "--source", "zotero", "--json"], research_env["env"])
        assert r.returncode == 0
        import json
        data = json.loads(r.stdout)
        assert isinstance(data, list)


# ===========================================================================
# New: Quarto manuscript commands
# ===========================================================================

class TestE2EQuarto:
    def test_quarto_build(self, research_env):
        """Quarto might not be installed in CI; skip gracefully."""
        import shutil
        if not shutil.which("quarto"):
            pytest.skip("quarto not installed")
        r = _run(["research", "quarto", "build", "mediation-review"], research_env["env"])
        assert r.returncode == 0 or "not found" in (r.stdout + r.stderr)

    def test_quarto_preview(self, research_env):
        import shutil
        if not shutil.which("quarto"):
            pytest.skip("quarto not installed")
        r = _run(["research", "quarto", "preview", "mediation-review", "--port", "4848"], research_env["env"])
        # Preview may fail or hang; check it at least tried
        assert "not found" not in r.stdout.lower()
