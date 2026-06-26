import pytest
from pathlib import Path
import tempfile
from unittest.mock import Mock
import asyncio
import os
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from vault_scanner import VaultScanner, MarkdownParser
from db_manager import DatabaseManager

pytestmark = pytest.mark.asyncio

@pytest.fixture
def scanner(db_manager):
    """Fixture for the VaultScanner."""
    return VaultScanner(db_manager)

class TestVaultScannerEdgeCases:
    """Tests for edge cases and error handling in VaultScanner."""

    def test_scan_nonexistent_path(self, scanner):
        """Test scanning a path that does not exist."""
        async def run_test():
            with pytest.raises(FileNotFoundError):
                await scanner.scan_vault("/non/existent/path/to/vault")
        asyncio.run(run_test())

    def test_scan_a_file_instead_of_directory(self, scanner):
        """Test scanning a path that is a file, not a directory."""
        with tempfile.NamedTemporaryFile() as tmp_file:
            async def run_test():
                with pytest.raises(FileNotFoundError): # Or a more specific error
                    await scanner.scan_vault(tmp_file.name)
            asyncio.run(run_test())

    def test_scan_empty_directory(self, scanner, tmp_path):
        """Test scanning an empty directory that is not a vault."""
        async def run_test():
            stats = await scanner.scan_vault(str(tmp_path))
            assert stats['notes_scanned'] == 0
        asyncio.run(run_test())

    def test_scan_vault_with_no_markdown_files(self, scanner, tmp_path):
        """Test scanning a valid vault with no markdown files."""
        vault_path = tmp_path / "NoMarkdownVault"
        vault_path.mkdir()
        (vault_path / ".obsidian").mkdir()
        (vault_path / "some_other_file.txt").write_text("hello")

        async def run_test():
            stats = await scanner.scan_vault(str(vault_path))
            assert stats['notes_scanned'] == 0
        asyncio.run(run_test())

    def test_scan_with_unreadable_file(self, scanner, tmp_path):
        """Test that an unreadable file doesn't stop the whole scan."""
        vault_path = tmp_path / "UnreadableVault"
        vault_path.mkdir()
        (vault_path / ".obsidian").mkdir()
        
        # Create a readable file
        (vault_path / "note1.md").write_text("# Note 1")
        
        # Create an unreadable file
        unreadable_file = vault_path / "note2.md"
        unreadable_file.write_text("# Note 2")
        unreadable_file.chmod(0o000) # Make it unreadable

        async def run_test():
            # The scan should skip the unreadable file and continue
            stats = await scanner.scan_vault(str(vault_path))
            assert stats['notes_scanned'] == 1 # Only the readable file was scanned
            # The unreadable file must be COUNTED as a failure, not silently dropped
            assert stats['notes_failed'] == 1

        try:
            asyncio.run(run_test())
        finally:
            # Cleanup permissions so the test directory can be removed
            unreadable_file.chmod(0o600)

    def test_failed_note_is_counted_and_reported(self, scanner, tmp_path):
        """A note that fails to insert is counted + reported, and the scan completes.

        Regression guard for S4: previously `except Exception: continue` swallowed
        the failure, `notes_scanned` looked fine, and `complete_scan(..., 0)`
        hardcoded the error count to 0 — scan reported success while a note was lost.
        """
        vault_path = tmp_path / "FailVault"
        vault_path.mkdir()
        (vault_path / ".obsidian").mkdir()

        (vault_path / "good.md").write_text("# Good note")
        (vault_path / "bad.md").write_text("# Bad note")

        # Make add_note raise for exactly one path, succeed for the rest.
        real_add_note = scanner.db.add_note

        def flaky_add_note(*args, **kwargs):
            if kwargs.get('path') == "bad.md":
                raise ValueError("planted insert failure")
            return real_add_note(*args, **kwargs)

        scanner.db.add_note = Mock(side_effect=flaky_add_note)

        async def run_test():
            stats = await scanner.scan_vault(str(vault_path))
            # Scan still completes and indexes the good note
            assert stats['notes_scanned'] == 1
            # The bad note is counted as a failure, not silently dropped
            assert stats['notes_failed'] == 1
            # The failing path is reported back to the caller
            assert "bad.md" in stats['failed_paths']
            # The real error count is persisted to scan_history (not hardcoded 0)
            history = scanner.db.get_scan_history(stats['vault_id'], limit=1)
            assert history[0]['notes_failed'] == 1
            assert history[0]['status'] == 'completed'

        asyncio.run(run_test())

class TestVaultScannerContentHashShortCircuit:
    """N1/N2: rescanning an UNCHANGED note must short-circuit on content_hash.

    The bug: `add_note` uses INSERT OR REPLACE, which deletes the conflicting
    row and fires ON DELETE CASCADE — wiping that note's `note_embeddings` row
    on EVERY rescan, because the scan loop re-add_note()s every file
    unconditionally. The fix compares the freshly-computed content_hash to the
    stored hash on `existing_note`; if unchanged, it skips add_note + the
    link/tag re-add entirely (counted as notes_unchanged).
    """

    def test_unchanged_note_preserves_embedding(self, scanner, tmp_path):
        """(a) An unchanged note keeps its note_embeddings row across a rescan."""
        scanner.db.ensure_embeddings_table()

        vault_path = tmp_path / "EmbVault"
        vault_path.mkdir()
        (vault_path / ".obsidian").mkdir()
        (vault_path / "note.md").write_text("# Note\n\nstable body #t [[other]]")

        async def run_test():
            stats = await scanner.scan_vault(str(vault_path))
            vault_id = stats['vault_id']
            note = scanner.db.get_note_by_path(vault_id, "note.md")

            # Simulate an AI op having cached an embedding for this note.
            scanner.db.save_embedding(
                note['id'], "gemini-api", "text-embedding-004",
                b"\x00\x01\x02\x03", 123.0
            )
            assert scanner.db.get_embedding(
                note['id'], "gemini-api", "text-embedding-004"
            ) is not None

            # Rescan with no content change.
            await scanner.scan_vault(str(vault_path))

            # The embedding row must survive (not cascade-wiped by REPLACE).
            assert scanner.db.get_embedding(
                note['id'], "gemini-api", "text-embedding-004"
            ) is not None

        asyncio.run(run_test())

    def test_unchanged_note_counted_as_notes_unchanged(self, scanner, tmp_path):
        """(b) An unchanged note is counted in notes_unchanged, not notes_updated."""
        vault_path = tmp_path / "UnchangedVault"
        vault_path.mkdir()
        (vault_path / ".obsidian").mkdir()
        (vault_path / "a.md").write_text("# A\n\nbody")

        async def run_test():
            first = await scanner.scan_vault(str(vault_path))
            assert first['notes_added'] == 1
            assert first.get('notes_unchanged', 0) == 0

            second = await scanner.scan_vault(str(vault_path))
            assert second['notes_unchanged'] == 1
            assert second['notes_updated'] == 0
            assert second['notes_added'] == 0
            assert second['notes_scanned'] == 1

        asyncio.run(run_test())

    def test_unchanged_note_leaves_links_and_tags_intact(self, scanner, tmp_path):
        """(c) Links and tags survive a no-op rescan of an unchanged note."""
        vault_path = tmp_path / "LinkTagVault"
        vault_path.mkdir()
        (vault_path / ".obsidian").mkdir()
        (vault_path / "src.md").write_text("# Src\n\n#topic and [[target]]")

        async def run_test():
            stats = await scanner.scan_vault(str(vault_path))
            vault_id = stats['vault_id']
            note = scanner.db.get_note_by_path(vault_id, "src.md")

            tags_before = scanner.db.get_note_tags(note['id'])
            links_before = scanner.db.get_outgoing_links(note['id'])
            assert "topic" in tags_before
            assert len(links_before) == 1

            await scanner.scan_vault(str(vault_path))

            assert scanner.db.get_note_tags(note['id']) == tags_before
            assert len(scanner.db.get_outgoing_links(note['id'])) == len(links_before)

        asyncio.run(run_test())

    def test_changed_note_still_replaces_and_updates(self, scanner, tmp_path):
        """A CHANGED note must still REPLACE + re-add (preserves the self-heal)."""
        scanner.db.ensure_embeddings_table()

        vault_path = tmp_path / "ChangedVault"
        vault_path.mkdir()
        (vault_path / ".obsidian").mkdir()
        note_file = vault_path / "m.md"
        note_file.write_text("# M\n\n#old [[oldtarget]]")

        async def run_test():
            stats = await scanner.scan_vault(str(vault_path))
            vault_id = stats['vault_id']
            note = scanner.db.get_note_by_path(vault_id, "m.md")
            scanner.db.save_embedding(
                note['id'], "gemini-api", "text-embedding-004",
                b"\x00\x01", 1.0
            )

            # Edit the content: tag/link change.
            note_file.write_text("# M\n\n#new [[newtarget]]")
            second = await scanner.scan_vault(str(vault_path))

            assert second['notes_updated'] == 1
            assert second.get('notes_unchanged', 0) == 0

            # Self-heal: old tag/link gone, new ones present.
            tags = scanner.db.get_note_tags(note['id'])
            assert "new" in tags
            assert "old" not in tags

            # REPLACE fired cascade — stale embedding is cleared for a changed note.
            assert scanner.db.get_embedding(
                note['id'], "gemini-api", "text-embedding-004"
            ) is None

        asyncio.run(run_test())


class TestVaultScannerPrune:
    """S1/S2: opt-in --prune mark-and-sweep of deleted/renamed notes.

    seen_paths collects every file present on disk this scan (added before the
    try, so a failed-but-present note is NOT pruned — no S4 regression). After
    the loop, if prune and seen_paths is non-empty, rows whose path is absent
    from disk are deleted (cascade cleans children). Empty seen_paths skips the
    sweep so a bad/empty vault path never wipes the index.
    """

    def test_prune_deletes_only_unseen_rows(self, scanner, tmp_path):
        """A note deleted on disk is removed; surviving notes are untouched."""
        vault_path = tmp_path / "PruneVault"
        vault_path.mkdir()
        (vault_path / ".obsidian").mkdir()
        (vault_path / "keep.md").write_text("# Keep\n\nbody")
        (vault_path / "gone.md").write_text("# Gone\n\nbody")

        async def run_test():
            stats = await scanner.scan_vault(str(vault_path))
            vault_id = stats['vault_id']
            assert len(scanner.db.list_notes(vault_id)) == 2

            # Delete one file on disk.
            (vault_path / "gone.md").unlink()

            # Without prune, the ghost row survives.
            no_prune = await scanner.scan_vault(str(vault_path))
            assert no_prune.get('notes_pruned', 0) == 0
            assert len(scanner.db.list_notes(vault_id)) == 2

            # With prune, only the unseen row is removed.
            pruned = await scanner.scan_vault(str(vault_path), prune=True)
            assert pruned['notes_pruned'] == 1
            remaining = scanner.db.list_notes(vault_id)
            assert len(remaining) == 1
            assert remaining[0]['path'] == "keep.md"

        asyncio.run(run_test())

    def test_rename_leaves_exactly_one_row(self, scanner, tmp_path):
        """a.md -> b.md with --prune leaves exactly one row, no a.md ghost."""
        vault_path = tmp_path / "RenameVault"
        vault_path.mkdir()
        (vault_path / ".obsidian").mkdir()
        (vault_path / "a.md").write_text("# A\n\nbody")

        async def run_test():
            stats = await scanner.scan_vault(str(vault_path))
            vault_id = stats['vault_id']

            # Rename on disk.
            (vault_path / "a.md").rename(vault_path / "b.md")

            result = await scanner.scan_vault(str(vault_path), prune=True)
            assert result['notes_pruned'] == 1
            notes = scanner.db.list_notes(vault_id)
            assert len(notes) == 1
            assert notes[0]['path'] == "b.md"
            assert scanner.db.get_note_by_path(vault_id, "a.md") is None

        asyncio.run(run_test())

    def test_empty_seen_paths_skips_sweep(self, scanner, tmp_path):
        """A vault that yields no files must NOT wipe its existing index."""
        vault_path = tmp_path / "EmptyVault"
        vault_path.mkdir()
        (vault_path / ".obsidian").mkdir()
        (vault_path / "n1.md").write_text("# N1\n\nbody")
        (vault_path / "n2.md").write_text("# N2\n\nbody")

        async def run_test():
            stats = await scanner.scan_vault(str(vault_path))
            vault_id = stats['vault_id']
            assert len(scanner.db.list_notes(vault_id)) == 2

            # Remove every markdown file (simulates a bad/unmaterialized path).
            (vault_path / "n1.md").unlink()
            (vault_path / "n2.md").unlink()

            result = await scanner.scan_vault(str(vault_path), prune=True)
            # Safety guard: sweep skipped, index intact.
            assert result['notes_pruned'] == 0
            assert len(scanner.db.list_notes(vault_id)) == 2

        asyncio.run(run_test())

    def test_failed_note_present_on_disk_is_not_pruned(self, scanner, tmp_path):
        """A note that fails to parse but still exists on disk is NOT pruned."""
        vault_path = tmp_path / "FailPresentVault"
        vault_path.mkdir()
        (vault_path / ".obsidian").mkdir()
        (vault_path / "ok.md").write_text("# OK\n\nbody")
        (vault_path / "bad.md").write_text("# Bad\n\nbody")

        async def run_test():
            stats = await scanner.scan_vault(str(vault_path))
            vault_id = stats['vault_id']
            assert len(scanner.db.list_notes(vault_id)) == 2

            # Make bad.md fail to parse on the next scan.
            from unittest.mock import patch
            real_parse = scanner.parser.parse_file

            def flaky_parse(p):
                if p.name == "bad.md":
                    raise ValueError("boom")
                return real_parse(p)

            with patch.object(scanner.parser, "parse_file", side_effect=flaky_parse):
                result = await scanner.scan_vault(str(vault_path), prune=True)

            # bad.md exists on disk so it stays in seen_paths and is NOT pruned.
            assert result['notes_failed'] == 1
            assert result['notes_pruned'] == 0
            assert scanner.db.get_note_by_path(vault_id, "bad.md") is not None

        asyncio.run(run_test())

    def test_prune_cascade_removes_child_rows(self, scanner, tmp_path):
        """Pruning a note cascades to its links/tags child rows."""
        vault_path = tmp_path / "CascadeVault"
        vault_path.mkdir()
        (vault_path / ".obsidian").mkdir()
        (vault_path / "keep.md").write_text("# Keep\n\nbody")
        (vault_path / "rich.md").write_text("# Rich\n\n#topic and [[target]]")

        async def run_test():
            stats = await scanner.scan_vault(str(vault_path))
            vault_id = stats['vault_id']
            rich = scanner.db.get_note_by_path(vault_id, "rich.md")
            assert len(scanner.db.get_outgoing_links(rich['id'])) == 1
            assert "topic" in scanner.db.get_note_tags(rich['id'])

            (vault_path / "rich.md").unlink()
            result = await scanner.scan_vault(str(vault_path), prune=True)
            assert result['notes_pruned'] == 1

            # Child rows are gone via ON DELETE CASCADE.
            assert scanner.db.get_outgoing_links(rich['id']) == []
            assert scanner.db.get_note_tags(rich['id']) == []

        asyncio.run(run_test())


class TestMarkdownParserEdgeCases:
    """Tests for edge cases in the MarkdownParser."""

    def test_parse_empty_file(self, tmp_path):
        """Test parsing an empty markdown file."""
        file_path = tmp_path / "empty.md"
        file_path.touch()
        
        note_data = MarkdownParser.parse_file(file_path)
        assert note_data.title == "empty"
        assert note_data.content == ""
        assert note_data.word_count == 0
        assert not note_data.tags
        assert not note_data.wikilinks

    def test_parse_file_with_invalid_frontmatter(self, tmp_path):
        """Test parsing a file with broken YAML frontmatter."""
        file_content = "---\ntitle: Unclosed\nkey: [a, b\n---\n# Content"
        file_path = tmp_path / "invalid_fm.md"
        file_path.write_text(file_content)

        # Invalid YAML should raise an error
        import yaml
        with pytest.raises(yaml.parser.ParserError):
            MarkdownParser.parse_file(file_path)

    def test_parse_file_with_null_bytes(self, tmp_path):
        """Test parsing a file containing null bytes."""
        file_path = tmp_path / "null_byte.md"
        with open(file_path, "wb") as f:
            f.write(b"# Title\n\nSome text\x00with a null byte.")
        
        try:
            note_data = MarkdownParser.parse_file(file_path)
            assert "Title" in note_data.title
            assert "Some text" in note_data.content
        except Exception as e:
            pytest.fail(f"Parsing file with null byte raised an exception: {e}")


class TestExtractTitle:
    """Tests for MarkdownParser._extract_title — the dotfile crash fix (#51)."""

    def test_normal_stem_returned(self, tmp_path):
        """Regular filename: stem is used as fallback title."""
        f = tmp_path / "my-note.md"
        f.write_text("some content")
        note = MarkdownParser.parse_file(f)
        assert note.title == "my-note"

    def test_frontmatter_title_takes_priority(self, tmp_path):
        """frontmatter title wins over stem and H1."""
        f = tmp_path / "ignored-stem.md"
        f.write_text("---\ntitle: 'FM Title'\n---\n# H1 Title\n")
        note = MarkdownParser.parse_file(f)
        assert note.title == "FM Title"

    def test_h1_used_when_no_frontmatter(self, tmp_path):
        """H1 heading is used when frontmatter has no title."""
        f = tmp_path / "no-fm.md"
        f.write_text("# Heading Title\n\nsome content")
        note = MarkdownParser.parse_file(f)
        assert note.title == "Heading Title"

    def test_dotfile_stem_used_as_title(self, tmp_path):
        """Dotfile '.md': stem is '.md' (truthy), so it becomes the title directly.
        The Untitled-<hash> branch only fires for files with a truly empty stem,
        which cannot occur on real filesystems — it's a belt-and-suspenders guard."""
        f = tmp_path / ".md"
        f.write_text("content with no title")
        note = MarkdownParser.parse_file(f)
        assert note.title == ".md"

    def test_dotfile_hash_is_stable(self, tmp_path):
        """Same dotfile path always produces the same hash-based title."""
        f = tmp_path / ".md"
        f.write_text("content")
        title1 = MarkdownParser._extract_title(f, "content", {})
        title2 = MarkdownParser._extract_title(f, "content", {})
        assert title1 == title2