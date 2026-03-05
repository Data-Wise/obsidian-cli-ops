"""
Integration tests using real markdown vault fixtures.

Tests the scanner pipeline against a real (small) vault directory
with known wikilinks, tags, and broken links.
"""

import re
from pathlib import Path

import pytest

# Fixture vault is at tests/fixtures/test_vault/
FIXTURE_VAULT = Path(__file__).resolve().parent / "fixtures" / "test_vault"


class TestVaultFixtures:
    """Verify vault fixtures are well-formed and consistent."""

    def test_fixture_vault_exists(self):
        """Fixture vault directory should exist with .obsidian marker."""
        assert FIXTURE_VAULT.exists(), f"Fixture vault not found at {FIXTURE_VAULT}"
        assert (FIXTURE_VAULT / ".obsidian").exists(), "Missing .obsidian marker"

    def test_fixture_notes_count(self):
        """Should have exactly 5 markdown files."""
        md_files = list(FIXTURE_VAULT.glob("*.md"))
        assert len(md_files) == 5, f"Expected 5 notes, found {len(md_files)}: {[f.name for f in md_files]}"

    def test_all_notes_have_frontmatter(self):
        """Every note should have YAML frontmatter with title and tags."""
        for md_file in FIXTURE_VAULT.glob("*.md"):
            content = md_file.read_text()
            assert content.startswith("---"), f"{md_file.name} missing frontmatter"
            # Check frontmatter ends
            second_dash = content.find("---", 3)
            assert second_dash > 0, f"{md_file.name} has unclosed frontmatter"

    def test_wikilinks_parseable(self):
        """All wikilinks should match [[target]] or [[target|display]] format."""
        wikilink_re = re.compile(r'\[\[([^\]|]+)(?:\|([^\]]+))?\]\]')
        total_links = 0
        for md_file in FIXTURE_VAULT.glob("*.md"):
            content = md_file.read_text()
            links = wikilink_re.findall(content)
            total_links += len(links)
        # hub-note has 4, note-a has 1, note-b has 1, broken-link has 1 = 7
        assert total_links == 7, f"Expected 7 wikilinks, found {total_links}"

    def test_hub_note_has_most_links(self):
        """hub-note.md should have the most outgoing links (4)."""
        wikilink_re = re.compile(r'\[\[([^\]|]+)(?:\|([^\]]+))?\]\]')
        hub = (FIXTURE_VAULT / "hub-note.md").read_text()
        links = wikilink_re.findall(hub)
        assert len(links) == 4, f"Hub note should have 4 links, found {len(links)}"

    def test_broken_link_exists(self):
        """broken-link-note.md should reference a non-existent note."""
        wikilink_re = re.compile(r'\[\[([^\]|]+)(?:\|([^\]]+))?\]\]')
        broken = (FIXTURE_VAULT / "broken-link-note.md").read_text()
        links = [m[0] for m in wikilink_re.findall(broken)]
        assert "nonexistent-note" in links
        # Verify target doesn't exist as a file
        assert not (FIXTURE_VAULT / "nonexistent-note.md").exists()

    def test_orphan_note_no_outgoing(self):
        """note-c.md should have no outgoing wikilinks."""
        wikilink_re = re.compile(r'\[\[([^\]|]+)(?:\|([^\]]+))?\]\]')
        note_c = (FIXTURE_VAULT / "note-c.md").read_text()
        links = wikilink_re.findall(note_c)
        assert len(links) == 0, f"note-c should have 0 links, found {len(links)}"

    def test_tags_present(self):
        """Each note should have at least one tag in frontmatter."""
        for md_file in FIXTURE_VAULT.glob("*.md"):
            content = md_file.read_text()
            assert "tags:" in content, f"{md_file.name} missing tags in frontmatter"


# ============================================================================
# Scanner integration tests — scan fixtures into DB and verify
# ============================================================================

import asyncio
import shutil

FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures" / "test_vault"


@pytest.fixture
def vault_dir(tmp_path):
    """Copy fixture vault into a temporary directory and return its path."""
    dest = tmp_path / "test_vault"
    shutil.copytree(FIXTURES_DIR, dest)
    return dest


@pytest.fixture
def scanned_db(vault_dir, db_manager):
    """Scan the fixture vault into an in-memory database and return (db, vault_id)."""
    from vault_scanner import VaultScanner

    scanner = VaultScanner(db_manager)
    asyncio.run(scanner.scan_vault(str(vault_dir), vault_name="fixture-vault"))

    vaults = db_manager.list_vaults()
    assert len(vaults) == 1, "Expected exactly one vault after scan"
    vault_id = vaults[0]["id"]
    return db_manager, vault_id


class TestFixtureVaultScan:
    """Scanner integration tests using the fixture vault."""

    def test_fixture_vault_note_count(self, scanned_db):
        """Scanner should find exactly 5 notes."""
        db, vault_id = scanned_db
        notes = db.list_notes(vault_id)
        assert len(notes) == 5, (
            f"Expected 5 notes in fixture vault, got {len(notes)}"
        )

    def test_fixture_vault_detects_orphan(self, scanned_db):
        """note-c has no outgoing links and no resolved incoming links,
        so it should appear in the orphaned_notes view."""
        db, vault_id = scanned_db
        orphans = db.get_orphaned_notes(vault_id)
        orphan_titles = [o["title"] for o in orphans]
        assert "Note C" in orphan_titles, (
            f"Expected 'Note C' in orphans, got {orphan_titles}"
        )

    def test_fixture_vault_detects_broken_link(self, scanned_db):
        """broken-link-note.md references [[nonexistent-note]].
        The target should not resolve to any note path stem."""
        db, vault_id = scanned_db

        notes = db.list_notes(vault_id)
        note_paths_stems = {Path(n["path"]).stem for n in notes}

        broken_note = next(
            n for n in notes if n["title"] == "Broken Link Note"
        )
        outgoing = db.get_outgoing_links(broken_note["id"])
        assert len(outgoing) > 0, "Expected at least one outgoing link"

        unresolved = [
            lnk for lnk in outgoing
            if lnk["target_path"] not in note_paths_stems
        ]
        assert len(unresolved) > 0, (
            "Expected at least one unresolved (broken) link"
        )
        assert any(
            "nonexistent" in lnk["target_path"] for lnk in unresolved
        ), "Expected 'nonexistent-note' among unresolved targets"

    def test_fixture_vault_hub_detection(self, scanned_db):
        """hub-note.md links to all 4 other notes; it should have the
        highest out-degree."""
        db, vault_id = scanned_db

        notes = db.list_notes(vault_id)
        hub_note = next(n for n in notes if n["title"] == "Hub Note")
        hub_links = db.get_outgoing_links(hub_note["id"])

        assert len(hub_links) == 4, (
            f"Expected hub-note to have 4 outgoing links, got {len(hub_links)}"
        )

        # Verify hub has the most outgoing links
        max_outgoing = 0
        max_note_title = ""
        for n in notes:
            out = db.get_outgoing_links(n["id"])
            if len(out) > max_outgoing:
                max_outgoing = len(out)
                max_note_title = n["title"]

        assert max_note_title == "Hub Note", (
            f"Expected 'Hub Note' to have the most outgoing links, "
            f"but '{max_note_title}' has {max_outgoing}"
        )

    def test_note_a_links_to_note_b(self, scanned_db):
        """Verify [[note-b]] wikilink in note-a is stored correctly."""
        db, vault_id = scanned_db
        notes = db.list_notes(vault_id)
        note_a = next(n for n in notes if n["title"] == "Note A")
        links = db.get_outgoing_links(note_a["id"])
        targets = [lnk["target_path"] for lnk in links]
        assert "note-b" in targets

    def test_note_b_links_to_note_c(self, scanned_db):
        """Verify [[note-c]] wikilink in note-b is stored correctly."""
        db, vault_id = scanned_db
        notes = db.list_notes(vault_id)
        note_b = next(n for n in notes if n["title"] == "Note B")
        links = db.get_outgoing_links(note_b["id"])
        targets = [lnk["target_path"] for lnk in links]
        assert "note-c" in targets

    def test_note_c_has_no_outgoing_links(self, scanned_db):
        """note-c (orphan) should have zero outgoing links in DB."""
        db, vault_id = scanned_db
        notes = db.list_notes(vault_id)
        note_c = next(n for n in notes if n["title"] == "Note C")
        links = db.get_outgoing_links(note_c["id"])
        assert len(links) == 0
