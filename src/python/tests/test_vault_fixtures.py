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
