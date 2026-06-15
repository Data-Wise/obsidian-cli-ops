"""Tests for new AI feature functions (suggest-links, gaps, summarize)."""

import io
import json
import sys
import pytest
np = pytest.importorskip("numpy", reason="numpy not installed in this Python env")
from unittest.mock import patch, MagicMock, PropertyMock

from ai.features import (
    LinkSuggestion,
    KnowledgeGap,
    VaultSummary,
    suggest_links,
    find_gaps,
    summarize_vault,
    _get_cached_embedding,
)
from ai.obsidian_bridge import ObsidianBridge
from ai.models import AnalysisResult


class TestEmbeddingCache:
    """Tests for embedding caching logic."""

    def test_get_cached_embedding_computes_on_miss(self):
        mock_db = MagicMock()
        mock_db.get_embedding_with_mtime.return_value = None
        mock_router = MagicMock()
        mock_router.get_embedding.return_value = [0.1, 0.2, 0.3]

        result = _get_cached_embedding(
            "note-1", "content", 1234.5,
            mock_db, mock_router,
            provider_name="test", model_name="test-model",
        )
        assert result == [0.1, 0.2, 0.3]
        mock_router.get_embedding.assert_called_once_with("content")
        mock_db.save_embedding.assert_called_once()

    def test_get_cached_embedding_returns_cached(self):
        cached_vector = np.array([0.4, 0.5, 0.6], dtype=np.float32).tobytes()
        mock_db = MagicMock()
        mock_db.get_embedding_with_mtime.return_value = {
            'vector': cached_vector,
            'file_mtime': 1234.5,
            'updated_at': '2025-01-01',
        }
        mock_router = MagicMock()

        result = _get_cached_embedding(
            "note-1", "content", 1234.5,  # Same mtime = cache hit
            mock_db, mock_router,
            provider_name="test", model_name="test-model",
        )
        assert len(result) == 3
        mock_router.get_embedding.assert_not_called()

    def test_get_cached_embedding_invalidates_on_mtime_change(self):
        cached_vector = np.array([0.4, 0.5], dtype=np.float32).tobytes()
        mock_db = MagicMock()
        mock_db.get_embedding_with_mtime.return_value = {
            'vector': cached_vector,
            'file_mtime': 1000.0,  # Old mtime
            'updated_at': '2025-01-01',
        }
        mock_router = MagicMock()
        mock_router.get_embedding.return_value = [0.7, 0.8]

        result = _get_cached_embedding(
            "note-1", "content", 2000.0,  # New mtime != cached
            mock_db, mock_router,
            provider_name="test", model_name="test-model",
        )
        assert result == [0.7, 0.8]
        mock_router.get_embedding.assert_called_once()


class TestFindGaps:
    """Tests for find_gaps feature."""

    def test_finds_stub_notes(self):
        mock_db = MagicMock()
        mock_db.get_vault.return_value = {'id': 'v1', 'path': '/vault'}

        # Mock the connection context manager for stub query
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [
            {'id': 'n1', 'title': 'Stub Note', 'word_count': 50, 'in_degree': 5, 'pagerank': 0.1}
        ]
        mock_conn = MagicMock()
        mock_conn.execute.return_value = mock_cursor
        mock_db.get_connection.return_value.__enter__ = MagicMock(return_value=mock_conn)
        mock_db.get_connection.return_value.__exit__ = MagicMock(return_value=False)

        mock_db.get_orphaned_notes.return_value = []

        with patch('ai.obsidian_bridge.ObsidianBridge') as mock_bridge_cls:
            mock_bridge = MagicMock()
            mock_bridge.get_orphans.return_value = []
            mock_bridge_cls.return_value = mock_bridge

            gaps = find_gaps('v1', mock_db)

        stub_gaps = [g for g in gaps if 'Stub' in g.description]
        assert len(stub_gaps) >= 1
        assert '5 incoming links' in stub_gaps[0].description

    def test_returns_empty_for_missing_vault(self):
        mock_db = MagicMock()
        mock_db.get_vault.return_value = None

        with pytest.raises(ValueError, match="Vault not found"):
            find_gaps('missing', mock_db)


class TestSummarizeVault:
    """Tests for summarize_vault feature."""

    def test_returns_empty_summary_for_no_notes(self):
        mock_db = MagicMock()
        mock_db.get_vault.return_value = {'id': 'v1', 'path': '/vault'}
        mock_db.list_notes.return_value = []

        summary = summarize_vault('v1', mock_db)
        assert summary.note_count == 0
        assert "No notes found" in summary.summary_text

    def test_returns_summary_for_missing_vault(self):
        mock_db = MagicMock()
        mock_db.get_vault.return_value = None

        with pytest.raises(ValueError, match="Vault not found"):
            summarize_vault('missing', mock_db)


class TestLinkSuggestion:
    """Tests for LinkSuggestion dataclass."""

    def test_creation(self):
        s = LinkSuggestion(
            source_title="Note A",
            target_title="Note B",
            target_path="note-b.md",
            similarity=0.85,
            reason="High similarity",
        )
        assert s.source_title == "Note A"
        assert s.similarity == 0.85


class TestKnowledgeGap:
    """Tests for KnowledgeGap dataclass."""

    def test_creation(self):
        g = KnowledgeGap(
            description="Missing topic coverage",
            related_notes=["note-1.md"],
            suggested_action="Create a note about X",
        )
        assert "Missing" in g.description
        assert len(g.related_notes) == 1


class TestVaultSummary:
    """Tests for VaultSummary dataclass."""

    def test_creation(self):
        s = VaultSummary(
            note_count=100,
            themes=["python", "testing"],
            orphan_count=5,
            summary_text="100 notes",
        )
        assert s.note_count == 100
        assert len(s.themes) == 2


class TestObsidianBridgeVerbose:
    """Tests for ObsidianBridge verbose logging."""

    def test_verbose_logs_when_unavailable(self):
        bridge = ObsidianBridge(verbose=True)
        bridge._available = False  # Force unavailable

        captured = io.StringIO()
        old_stderr = sys.stderr
        sys.stderr = captured
        try:
            bridge.is_available()
        finally:
            sys.stderr = old_stderr

        assert "[verbose] Obsidian CLI not available" in captured.getvalue()

    def test_no_verbose_output_when_disabled(self):
        bridge = ObsidianBridge(verbose=False)
        bridge._available = False

        captured = io.StringIO()
        old_stderr = sys.stderr
        sys.stderr = captured
        try:
            bridge.is_available()
        finally:
            sys.stderr = old_stderr

        assert captured.getvalue() == ""

    def test_default_verbose_is_false(self):
        bridge = ObsidianBridge()
        assert bridge._verbose is False


class TestSuggestLinksVerbose:
    """Tests that suggest_links verbose logs embedding computation."""

    def test_verbose_logs_embedding_computation(self):
        mock_db = MagicMock()
        mock_db.get_note.return_value = {'id': 'n1', 'vault_id': 'v1', 'title': 'My Note', 'path': 'note.md'}
        mock_db.get_vault.return_value = {'id': 'v1', 'path': '/tmp/vault'}
        # Need at least one candidate so we don't hit early return before verbose print
        mock_db.list_notes.return_value = [
            {'id': 'n1', 'vault_id': 'v1', 'title': 'My Note', 'path': 'note.md'},
            {'id': 'n2', 'vault_id': 'v1', 'title': 'Other', 'path': 'other.md'},
        ]

        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = []
        mock_conn.execute.return_value = mock_cursor
        mock_db.get_connection.return_value.__enter__ = MagicMock(return_value=mock_conn)
        mock_db.get_connection.return_value.__exit__ = MagicMock(return_value=False)

        mock_router = MagicMock()
        mock_router.get_embedding.return_value = [0.1, 0.2, 0.3]

        with patch('ai.features._get_note_content', return_value='Some content here for testing'), \
             patch('ai.features.get_ai_client', return_value=mock_router), \
             patch('ai.features._get_cached_embedding', return_value=np.array([0.1, 0.2, 0.3])), \
             patch('os.path.getmtime', return_value=1000.0), \
             patch('pathlib.Path.exists', return_value=False):

            captured = io.StringIO()
            old_stderr = sys.stderr
            sys.stderr = captured
            try:
                suggest_links('n1', mock_db, verbose=True)
            finally:
                sys.stderr = old_stderr

            assert "[verbose] Computing embedding for My Note" in captured.getvalue()


class TestFindGapsVerbose:
    """Tests that find_gaps passes verbose to ObsidianBridge."""

    def test_verbose_passed_to_bridge(self):
        mock_db = MagicMock()
        mock_db.get_vault.return_value = {'id': 'v1', 'path': '/vault'}

        # Mock the connection for stub query
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = []
        mock_conn = MagicMock()
        mock_conn.execute.return_value = mock_cursor
        mock_db.get_connection.return_value.__enter__ = MagicMock(return_value=mock_conn)
        mock_db.get_connection.return_value.__exit__ = MagicMock(return_value=False)
        mock_db.get_orphaned_notes.return_value = []

        with patch('ai.obsidian_bridge.ObsidianBridge') as mock_bridge_cls:
            mock_bridge = MagicMock()
            mock_bridge.get_orphans.return_value = []
            mock_bridge_cls.return_value = mock_bridge

            find_gaps('v1', mock_db, verbose=True)

            mock_bridge_cls.assert_called_once_with(verbose=True)
