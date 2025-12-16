"""Tests for AI features module."""

import pytest
from unittest.mock import patch, MagicMock
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(__file__).rsplit('/', 2)[0])

from ai.features import (
    find_similar_notes,
    analyze_note,
    find_duplicates,
    compare_notes,
    _cosine_similarity,
    _get_note_content,
    SimilarityMatch,
    DuplicateGroup,
)
from ai.providers.base import AnalysisResult, ComparisonResult


class TestCosineSimilarity:
    """Tests for cosine similarity calculation."""

    def test_identical_vectors(self):
        """Test identical vectors have similarity 1.0."""
        vec = [1.0, 2.0, 3.0]
        assert _cosine_similarity(vec, vec) == pytest.approx(1.0)

    def test_orthogonal_vectors(self):
        """Test orthogonal vectors have similarity 0.0."""
        vec1 = [1.0, 0.0]
        vec2 = [0.0, 1.0]
        assert _cosine_similarity(vec1, vec2) == pytest.approx(0.0)

    def test_opposite_vectors(self):
        """Test opposite vectors have similarity -1.0."""
        vec1 = [1.0, 0.0]
        vec2 = [-1.0, 0.0]
        assert _cosine_similarity(vec1, vec2) == pytest.approx(-1.0)

    def test_zero_vector(self):
        """Test zero vector returns 0.0."""
        vec1 = [1.0, 2.0, 3.0]
        vec2 = [0.0, 0.0, 0.0]
        assert _cosine_similarity(vec1, vec2) == 0.0
        assert _cosine_similarity(vec2, vec1) == 0.0

    def test_similar_vectors(self):
        """Test similar vectors have high similarity."""
        vec1 = [1.0, 2.0, 3.0]
        vec2 = [1.1, 2.1, 3.1]
        sim = _cosine_similarity(vec1, vec2)
        assert sim > 0.99


class TestSimilarityMatch:
    """Tests for SimilarityMatch dataclass."""

    def test_creation(self):
        """Test creating a SimilarityMatch."""
        match = SimilarityMatch(
            note_id="note123",
            title="Test Note",
            path="folder/test.md",
            similarity=0.85,
            reason="High similarity"
        )

        assert match.note_id == "note123"
        assert match.title == "Test Note"
        assert match.path == "folder/test.md"
        assert match.similarity == 0.85
        assert match.reason == "High similarity"

    def test_default_reason(self):
        """Test default reason is empty."""
        match = SimilarityMatch(
            note_id="note123",
            title="Test Note",
            path="test.md",
            similarity=0.5
        )
        assert match.reason == ""


class TestDuplicateGroup:
    """Tests for DuplicateGroup dataclass."""

    def test_creation(self):
        """Test creating a DuplicateGroup."""
        notes = [
            {"id": "note1", "title": "Note 1", "path": "note1.md"},
            {"id": "note2", "title": "Note 2", "path": "note2.md"},
        ]
        group = DuplicateGroup(
            notes=notes,
            similarity=0.95,
            reason="Duplicate content"
        )

        assert len(group.notes) == 2
        assert group.similarity == 0.95
        assert group.reason == "Duplicate content"


class TestFindSimilarNotes:
    """Tests for find_similar_notes function."""

    def test_note_not_found(self):
        """Test error when note not found."""
        mock_db = MagicMock()
        mock_db.get_note.return_value = None

        with pytest.raises(ValueError, match="Note not found"):
            find_similar_notes("nonexistent", mock_db)

    def test_vault_not_found(self):
        """Test error when vault not found."""
        mock_db = MagicMock()
        mock_db.get_note.return_value = {"id": "note1", "vault_id": "v1"}
        mock_db.get_vault.return_value = None

        with pytest.raises(ValueError, match="Vault not found"):
            find_similar_notes("note1", mock_db)

    @patch('ai.features._get_note_content')
    @patch('ai.features.get_ai_client')
    def test_no_other_notes(self, mock_client, mock_content):
        """Test empty result when no other notes exist."""
        mock_db = MagicMock()
        mock_db.get_note.return_value = {
            "id": "note1",
            "vault_id": "v1",
            "path": "note1.md"
        }
        mock_db.get_vault.return_value = {"path": "/vault"}
        mock_db.list_notes.return_value = [{"id": "note1"}]  # Only source note

        mock_content.return_value = "Some content"
        mock_router = MagicMock()
        mock_router.get_embedding.return_value = [1.0, 0.0, 0.0]
        mock_client.return_value = mock_router

        result = find_similar_notes("note1", mock_db)
        assert result == []

    @patch('ai.features._get_note_content')
    @patch('ai.features.get_ai_client')
    def test_finds_similar_notes(self, mock_client, mock_content):
        """Test finding similar notes."""
        mock_db = MagicMock()
        mock_db.get_note.return_value = {
            "id": "note1",
            "vault_id": "v1",
            "path": "note1.md"
        }
        mock_db.get_vault.return_value = {"path": "/vault"}
        mock_db.list_notes.return_value = [
            {"id": "note1", "title": "Note 1", "path": "note1.md"},
            {"id": "note2", "title": "Note 2", "path": "note2.md"},
            {"id": "note3", "title": "Note 3", "path": "note3.md"},
        ]

        mock_content.return_value = "A" * 100  # Long enough content

        mock_router = MagicMock()
        # Source embedding
        mock_router.get_embedding.return_value = [1.0, 0.0, 0.0]
        # Similar embeddings for other notes
        mock_router.get_embeddings_batch.return_value = [
            [0.95, 0.3, 0.0],  # Similar to source
            [0.1, 0.9, 0.0],   # Different from source
        ]
        mock_client.return_value = mock_router

        result = find_similar_notes("note1", mock_db, limit=5, min_similarity=0.5)

        # Should find note2 (similar) but not note3 (different)
        assert len(result) == 1
        assert result[0].note_id == "note2"


class TestAnalyzeNote:
    """Tests for analyze_note function."""

    def test_note_not_found(self):
        """Test error when note not found."""
        mock_db = MagicMock()
        mock_db.get_note.return_value = None

        with pytest.raises(ValueError, match="Note not found"):
            analyze_note("nonexistent", mock_db)

    @patch('ai.features._get_note_content')
    @patch('ai.features.get_ai_client')
    def test_analyzes_note(self, mock_client, mock_content):
        """Test successful note analysis."""
        mock_db = MagicMock()
        mock_db.get_note.return_value = {
            "id": "note1",
            "vault_id": "v1",
            "path": "note1.md",
            "title": "Test Note"
        }
        mock_db.get_vault.return_value = {"path": "/vault"}

        mock_content.return_value = "# Test Note\n\nSome content here."

        expected_result = AnalysisResult(
            topics=["testing"],
            themes=["development"],
            quality={"completeness": 7, "clarity": 8}
        )

        mock_router = MagicMock()
        mock_router.analyze_note.return_value = expected_result
        mock_client.return_value = mock_router

        result = analyze_note("note1", mock_db)

        assert result == expected_result
        mock_router.analyze_note.assert_called_once()


class TestFindDuplicates:
    """Tests for find_duplicates function."""

    def test_vault_not_found(self):
        """Test error when vault not found."""
        mock_db = MagicMock()
        mock_db.get_vault.return_value = None

        with pytest.raises(ValueError, match="Vault not found"):
            find_duplicates("nonexistent", mock_db)

    def test_too_few_notes(self):
        """Test empty result with less than 2 notes."""
        mock_db = MagicMock()
        mock_db.get_vault.return_value = {"path": "/vault"}
        mock_db.list_notes.return_value = [{"id": "note1"}]

        result = find_duplicates("v1", mock_db)
        assert result == []

    @patch('ai.features._get_note_content')
    @patch('ai.features.get_ai_client')
    def test_finds_duplicates(self, mock_client, mock_content):
        """Test finding duplicate notes."""
        mock_db = MagicMock()
        mock_db.get_vault.return_value = {"path": "/vault"}
        mock_db.list_notes.return_value = [
            {"id": "note1", "title": "Note 1", "path": "note1.md"},
            {"id": "note2", "title": "Note 2", "path": "note2.md"},
            {"id": "note3", "title": "Note 3", "path": "note3.md"},
        ]

        mock_content.return_value = "A" * 100

        mock_router = MagicMock()
        # Embeddings: note1 and note2 are duplicates
        mock_router.get_embeddings_batch.return_value = [
            [1.0, 0.0, 0.0],   # note1
            [0.99, 0.1, 0.0],  # note2 - very similar to note1
            [0.0, 1.0, 0.0],   # note3 - different
        ]
        mock_client.return_value = mock_router

        result = find_duplicates("v1", mock_db, threshold=0.9)

        # Should find one duplicate group (note1, note2)
        assert len(result) == 1
        assert len(result[0].notes) == 2


class TestCompareNotes:
    """Tests for compare_notes function."""

    def test_note1_not_found(self):
        """Test error when first note not found."""
        mock_db = MagicMock()
        mock_db.get_note.return_value = None

        with pytest.raises(ValueError, match="Note not found"):
            compare_notes("note1", "note2", mock_db)

    def test_note2_not_found(self):
        """Test error when second note not found."""
        mock_db = MagicMock()
        mock_db.get_note.side_effect = [
            {"id": "note1", "vault_id": "v1"},
            None
        ]

        with pytest.raises(ValueError, match="Note not found"):
            compare_notes("note1", "note2", mock_db)

    @patch('ai.features._get_note_content')
    @patch('ai.features.get_ai_client')
    def test_compares_notes(self, mock_client, mock_content):
        """Test successful note comparison."""
        mock_db = MagicMock()
        mock_db.get_note.side_effect = [
            {"id": "note1", "vault_id": "v1", "path": "note1.md", "title": "Note 1"},
            {"id": "note2", "vault_id": "v1", "path": "note2.md", "title": "Note 2"},
        ]
        mock_db.get_vault.return_value = {"path": "/vault"}

        mock_content.return_value = "Some content"

        expected_result = ComparisonResult(
            similarity_score=0.75,
            reason="Similar topics",
            should_merge=False
        )

        mock_router = MagicMock()
        mock_router.compare_notes.return_value = expected_result
        mock_client.return_value = mock_router

        result = compare_notes("note1", "note2", mock_db)

        assert result == expected_result
        mock_router.compare_notes.assert_called_once()


class TestGetNoteContent:
    """Tests for _get_note_content helper."""

    def test_file_not_exists(self):
        """Test None returned when file doesn't exist."""
        note = {"path": "nonexistent.md"}
        result = _get_note_content(note, "/nonexistent/vault")
        assert result is None

    @patch('pathlib.Path.exists')
    @patch('pathlib.Path.read_text')
    def test_file_exists(self, mock_read, mock_exists):
        """Test content returned when file exists."""
        mock_exists.return_value = True
        mock_read.return_value = "# Test Content"

        note = {"path": "test.md"}
        result = _get_note_content(note, "/vault")

        assert result == "# Test Content"

    @patch('pathlib.Path.exists')
    @patch('pathlib.Path.read_text')
    def test_read_error(self, mock_read, mock_exists):
        """Test None returned on read error."""
        mock_exists.return_value = True
        mock_read.side_effect = IOError("Read error")

        note = {"path": "test.md"}
        result = _get_note_content(note, "/vault")

        assert result is None
