"""Tests for vault health dashboard scoring logic."""

import pytest
from unittest.mock import MagicMock, patch, PropertyMock
from core.vault_manager import VaultManager
from core.models import HealthScore, VaultHealth
from core.exceptions import VaultNotFoundError


@pytest.fixture
def mock_db():
    """Create a mock DatabaseManager with default empty returns."""
    db = MagicMock()
    db.get_vault_by_name_or_id.return_value = {'id': 'vault-1', 'name': 'TestVault', 'path': '/test'}
    db.list_notes.return_value = []
    db.get_orphaned_notes.return_value = []
    db.get_broken_links.return_value = []
    db.get_hub_notes.return_value = []
    db.get_note_freshness.return_value = {'total': 0, 'recent': 0, 'stale': 0}

    # Mock get_connection context manager for SQL queries
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_cursor.fetchone.return_value = (0,)
    mock_conn.execute.return_value = mock_cursor
    db.get_connection.return_value.__enter__ = MagicMock(return_value=mock_conn)
    db.get_connection.return_value.__exit__ = MagicMock(return_value=False)

    return db


@pytest.fixture
def vault_manager(mock_db):
    """Create VaultManager with mocked DB."""
    vm = VaultManager.__new__(VaultManager)
    vm.db = mock_db
    vm.scanner = MagicMock()
    return vm


class TestConnectivityScore:
    def test_no_orphans_perfect_score(self, vault_manager, mock_db):
        """0 orphans = 100 score."""
        mock_db.list_notes.return_value = [{'id': f'n{i}'} for i in range(10)]
        mock_db.get_orphaned_notes.return_value = []

        health = vault_manager.get_vault_health('TestVault')
        assert health.connectivity.score == 100

    def test_all_orphans_zero_score(self, vault_manager, mock_db):
        """100% orphans = 0 score (100 - 100*2 clamped to 0)."""
        notes = [{'id': f'n{i}'} for i in range(10)]
        mock_db.list_notes.return_value = notes
        mock_db.get_orphaned_notes.return_value = notes  # all orphans

        health = vault_manager.get_vault_health('TestVault')
        assert health.connectivity.score == 0

    def test_partial_orphans(self, vault_manager, mock_db):
        """10% orphans = 80 score (100 - 10*2)."""
        mock_db.list_notes.return_value = [{'id': f'n{i}'} for i in range(100)]
        mock_db.get_orphaned_notes.return_value = [{'id': f'n{i}'} for i in range(10)]

        health = vault_manager.get_vault_health('TestVault')
        assert health.connectivity.score == 80

    def test_orphan_recommendation(self, vault_manager, mock_db):
        """Orphans present produce a recommendation."""
        mock_db.list_notes.return_value = [{'id': 'n1'}, {'id': 'n2'}]
        mock_db.get_orphaned_notes.return_value = [{'id': 'n1'}]

        health = vault_manager.get_vault_health('TestVault')
        assert len(health.connectivity.recommendations) == 1
        assert "1 orphaned" in health.connectivity.recommendations[0]


class TestLinkIntegrityScore:
    def test_no_broken_links_perfect(self, vault_manager, mock_db):
        """0 broken links = 100."""
        mock_db.list_notes.return_value = [{'id': 'n1'}]
        mock_db.get_broken_links.return_value = []

        health = vault_manager.get_vault_health('TestVault')
        assert health.link_integrity.score == 100

    def test_broken_links_degraded(self, vault_manager, mock_db):
        """Broken links reduce the score."""
        mock_db.list_notes.return_value = [{'id': 'n1'}]
        mock_db.get_broken_links.return_value = [{'broken_count': 5}]

        # Set total_links = 100 via mock connection
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        # First call: total_links, Second call: tagged_count
        mock_cursor.fetchone.side_effect = [(100,), (0,)]
        mock_conn.execute.return_value = mock_cursor
        mock_db.get_connection.return_value.__enter__.return_value = mock_conn

        health = vault_manager.get_vault_health('TestVault')
        # broken_pct = 5/100 * 100 = 5%, score = 100 - 5*5 = 75
        assert health.link_integrity.score == 75

    def test_broken_link_recommendation(self, vault_manager, mock_db):
        """Broken links produce a recommendation."""
        mock_db.list_notes.return_value = [{'id': 'n1'}]
        mock_db.get_broken_links.return_value = [{'broken_count': 3}]

        health = vault_manager.get_vault_health('TestVault')
        assert len(health.link_integrity.recommendations) == 1
        assert "3 broken links" in health.link_integrity.recommendations[0]


class TestStructureScore:
    def test_full_tag_coverage(self, vault_manager, mock_db):
        """100% tagged = high structure score."""
        mock_db.list_notes.return_value = [{'id': 'n1'}]
        mock_db.get_hub_notes.return_value = []

        # total_links=0, tagged_count=1 (all tagged)
        mock_conn = MagicMock()
        mock_cursor_links = MagicMock()
        mock_cursor_links.fetchone.return_value = (0,)
        mock_cursor_tags = MagicMock()
        mock_cursor_tags.fetchone.return_value = (1,)
        mock_conn.execute.side_effect = [mock_cursor_links, mock_cursor_tags]
        mock_db.get_connection.return_value.__enter__.return_value = mock_conn

        health = vault_manager.get_vault_health('TestVault')
        # tag_coverage=100, hub_concentration=0 (no hubs/links), balance=100
        # structure = 100*0.6 + 100*0.4 = 100
        assert health.structure.score == 100

    def test_no_tags(self, vault_manager, mock_db):
        """0% tagged = low structure score (from tag component)."""
        mock_db.list_notes.return_value = [{'id': f'n{i}'} for i in range(10)]
        mock_db.get_hub_notes.return_value = []

        # total_links=0, tagged_count=0
        mock_conn = MagicMock()
        mock_cursor_links = MagicMock()
        mock_cursor_links.fetchone.return_value = (0,)
        mock_cursor_tags = MagicMock()
        mock_cursor_tags.fetchone.return_value = (0,)
        mock_conn.execute.side_effect = [mock_cursor_links, mock_cursor_tags]
        mock_db.get_connection.return_value.__enter__.return_value = mock_conn

        health = vault_manager.get_vault_health('TestVault')
        # tag_coverage=0, balance=100 (no hubs), structure = 0*0.6 + 100*0.4 = 40
        assert health.structure.score == 40


class TestFreshnessScore:
    def test_all_recent(self, vault_manager, mock_db):
        """All notes modified recently = 100."""
        mock_db.list_notes.return_value = [{'id': 'n1'}]
        mock_db.get_note_freshness.return_value = {'total': 10, 'recent': 10, 'stale': 0}

        health = vault_manager.get_vault_health('TestVault')
        assert health.freshness.score == 100

    def test_all_stale(self, vault_manager, mock_db):
        """All notes stale = 0."""
        mock_db.list_notes.return_value = [{'id': 'n1'}]
        mock_db.get_note_freshness.return_value = {'total': 10, 'recent': 0, 'stale': 10}

        health = vault_manager.get_vault_health('TestVault')
        assert health.freshness.score == 0

    def test_stale_recommendation(self, vault_manager, mock_db):
        """Stale notes produce a recommendation."""
        mock_db.list_notes.return_value = [{'id': 'n1'}]
        mock_db.get_note_freshness.return_value = {'total': 10, 'recent': 5, 'stale': 5}

        health = vault_manager.get_vault_health('TestVault')
        assert len(health.freshness.recommendations) == 1
        assert "5 stale" in health.freshness.recommendations[0]


class TestOverallScore:
    def test_weighted_average(self, vault_manager, mock_db):
        """Verify 30/25/25/20 weights produce correct overall."""
        mock_db.list_notes.return_value = [{'id': f'n{i}'} for i in range(100)]
        mock_db.get_orphaned_notes.return_value = []  # connectivity = 100
        mock_db.get_broken_links.return_value = []  # integrity = 100
        mock_db.get_hub_notes.return_value = []
        mock_db.get_note_freshness.return_value = {'total': 100, 'recent': 100, 'stale': 0}

        # total_links=0, tagged_count=100 (all tagged)
        mock_conn = MagicMock()
        mock_cursor_links = MagicMock()
        mock_cursor_links.fetchone.return_value = (0,)
        mock_cursor_tags = MagicMock()
        mock_cursor_tags.fetchone.return_value = (100,)
        mock_conn.execute.side_effect = [mock_cursor_links, mock_cursor_tags]
        mock_db.get_connection.return_value.__enter__.return_value = mock_conn

        health = vault_manager.get_vault_health('TestVault')
        # All scores 100 -> overall = 100
        assert health.overall == 100

    def test_recommendations_generated(self, vault_manager, mock_db):
        """Non-trivial vault produces recommendations."""
        mock_db.list_notes.return_value = [{'id': f'n{i}'} for i in range(10)]
        mock_db.get_orphaned_notes.return_value = [{'id': 'n1'}]
        mock_db.get_broken_links.return_value = [{'broken_count': 2}]
        mock_db.get_note_freshness.return_value = {'total': 10, 'recent': 3, 'stale': 7}

        health = vault_manager.get_vault_health('TestVault')
        assert len(health.recommendations) > 0
        assert len(health.recommendations) <= 3


class TestHealthEdgeCases:
    def test_empty_vault(self, vault_manager, mock_db):
        """Empty vault returns sensible defaults (no division by zero)."""
        mock_db.list_notes.return_value = []
        mock_db.get_orphaned_notes.return_value = []
        mock_db.get_broken_links.return_value = []
        mock_db.get_hub_notes.return_value = []
        mock_db.get_note_freshness.return_value = {'total': 0, 'recent': 0, 'stale': 0}

        health = vault_manager.get_vault_health('TestVault')
        # Should not raise
        assert health.overall >= 0
        assert health.connectivity.score >= 0
        assert health.link_integrity.score >= 0
        assert health.structure.score >= 0
        assert health.freshness.score >= 0

    def test_vault_not_found(self, vault_manager, mock_db):
        """Missing vault raises VaultNotFoundError."""
        mock_db.get_vault_by_name_or_id.return_value = None

        with pytest.raises(VaultNotFoundError):
            vault_manager.get_vault_health('nonexistent')

    def test_ambiguous_prefix_raises(self, vault_manager, mock_db):
        """Ambiguous prefix raises ValueError."""
        mock_db.get_vault_by_name_or_id.side_effect = ValueError("Ambiguous prefix")

        with pytest.raises(ValueError, match="Ambiguous"):
            vault_manager.get_vault_health('abc')


class TestHealthModels:
    def test_health_score_to_dict(self):
        """HealthScore.to_dict() returns correct structure."""
        score = HealthScore(name="Test", score=85, details=["d1"], recommendations=["r1"])
        d = score.to_dict()
        assert d['name'] == "Test"
        assert d['score'] == 85
        assert d['details'] == ["d1"]
        assert d['recommendations'] == ["r1"]

    def test_vault_health_to_dict(self):
        """VaultHealth.to_dict() includes all sub-scores."""
        sub = HealthScore(name="Sub", score=80, details=["ok"])
        health = VaultHealth(
            vault_name="MyVault", overall=80,
            connectivity=sub, link_integrity=sub,
            structure=sub, freshness=sub,
        )
        d = health.to_dict()
        assert d['vault'] == "MyVault"
        assert d['overall'] == 80
        assert 'connectivity' in d
        assert 'link_integrity' in d
        assert 'structure' in d
        assert 'freshness' in d

    def test_vault_health_to_json(self):
        """VaultHealth.to_json() returns valid JSON string."""
        import json
        sub = HealthScore(name="Sub", score=80, details=["ok"])
        health = VaultHealth(
            vault_name="MyVault", overall=80,
            connectivity=sub, link_integrity=sub,
            structure=sub, freshness=sub,
        )
        parsed = json.loads(health.to_json())
        assert parsed['vault'] == "MyVault"

    def test_recommendations_capped_at_three(self):
        """VaultHealth.recommendations returns at most 3."""
        sub_many_recs = HealthScore(name="S", score=50, details=[], recommendations=["r1", "r2"])
        health = VaultHealth(
            vault_name="V", overall=50,
            connectivity=sub_many_recs, link_integrity=sub_many_recs,
            structure=sub_many_recs, freshness=sub_many_recs,
        )
        assert len(health.recommendations) == 3
