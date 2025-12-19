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
def db_manager():
    """Fixture for an in-memory database."""
    return DatabaseManager(db_path=":memory:")

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
        
        try:
            asyncio.run(run_test())
        finally:
            # Cleanup permissions so the test directory can be removed
            unreadable_file.chmod(0o600)

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

        # It should parse the content, but the frontmatter might be empty or part of content
        note_data = MarkdownParser.parse_file(file_path)
        assert note_data is not None
        assert "Unclosed" in note_data.content # frontmatter becomes content
        assert note_data.title == "invalid_fm" # Falls back to filename

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