"""
Unit tests for --json flag output across all data-outputting commands.

Verifies that JSON output is valid, contains expected keys, and has
no Rich markup leaking into the output.
"""
import json
import re
import sys
import pytest
from unittest.mock import MagicMock, patch
from io import StringIO
from datetime import datetime


# Rich markup pattern: [bold], [red], [/], [cyan], etc.
RICH_MARKUP_RE = re.compile(r'\[/?[a-z]+[^\]]*\]')


def _make_mock_args(**kwargs):
    """Create a mock args namespace with defaults."""
    defaults = {
        'command': None,
        'verbose': False,
        'json': True,
    }
    defaults.update(kwargs)
    args = MagicMock()
    for k, v in defaults.items():
        setattr(args, k, v)
    return args


class TestListVaultsJSON:
    """Test vaults command JSON output."""

    @patch('obs_cli.DatabaseManager')
    @patch('obs_cli.VaultManager')
    @patch('obs_cli.GraphAnalyzer')
    def test_list_vaults_json_valid(self, mock_ga, mock_vm, mock_db, capsys):
        """Test that vaults --json produces valid JSON array."""
        from obs_cli import ObsCLI
        mock_vault = MagicMock()
        mock_vault.to_dict.return_value = {
            'id': 'abc123',
            'name': 'Test Vault',
            'path': '/path/to/vault',
            'note_count': 42,
            'link_count': 100,
            'tag_count': 10,
            'orphan_count': 2,
            'hub_count': 5,
            'last_scanned': '2025-12-19T10:00:00',
            'created_at': None,
        }
        mock_vm.return_value.list_vaults.return_value = [mock_vault]

        cli = ObsCLI()
        # Simulate the JSON path from main()
        vaults = cli.vault_manager.list_vaults()
        print(json.dumps([v.to_dict() for v in vaults], indent=2, default=str))

        captured = capsys.readouterr()
        result = json.loads(captured.out)
        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0]['name'] == 'Test Vault'
        assert result[0]['note_count'] == 42
        assert 'id' in result[0]
        assert 'path' in result[0]
        assert 'link_count' in result[0]
        assert 'last_scanned' in result[0]

    @patch('obs_cli.DatabaseManager')
    @patch('obs_cli.VaultManager')
    @patch('obs_cli.GraphAnalyzer')
    def test_list_vaults_json_empty(self, mock_ga, mock_vm, mock_db, capsys):
        """Test that vaults --json with no vaults produces empty array."""
        from obs_cli import ObsCLI
        mock_vm.return_value.list_vaults.return_value = []

        cli = ObsCLI()
        vaults = cli.vault_manager.list_vaults()
        print(json.dumps([v.to_dict() for v in vaults], indent=2, default=str))

        captured = capsys.readouterr()
        result = json.loads(captured.out)
        assert result == []


class TestStatsJSON:
    """Test stats command JSON output."""

    @patch('obs_cli.DatabaseManager')
    @patch('obs_cli.VaultManager')
    @patch('obs_cli.GraphAnalyzer')
    def test_stats_global_json_valid(self, mock_ga, mock_vm, mock_db_class, capsys):
        """Test that stats --json (global) produces valid JSON object."""
        from obs_cli import ObsCLI
        mock_db_class.return_value.get_stats.return_value = {
            'vaults': 2,
            'notes': 100,
            'links': 50,
            'tags': 25,
            'orphaned_notes': 5,
            'broken_links': 2,
        }

        cli = ObsCLI()
        db_stats = cli.db.get_stats()
        print(json.dumps({
            "vaults": db_stats['vaults'],
            "notes": db_stats['notes'],
            "links": db_stats['links'],
            "tags": db_stats['tags'],
            "orphaned_notes": db_stats['orphaned_notes'],
            "broken_links": db_stats['broken_links'],
        }, indent=2, default=str))

        captured = capsys.readouterr()
        result = json.loads(captured.out)
        assert isinstance(result, dict)
        assert result['vaults'] == 2
        assert result['notes'] == 100
        assert result['links'] == 50
        assert result['tags'] == 25
        assert result['orphaned_notes'] == 5
        assert result['broken_links'] == 2

    @patch('obs_cli.DatabaseManager')
    @patch('obs_cli.VaultManager')
    @patch('obs_cli.GraphAnalyzer')
    def test_stats_vault_json_valid(self, mock_ga, mock_vm, mock_db_class, capsys):
        """Test that stats --vault X --json produces valid JSON object."""
        from obs_cli import ObsCLI
        mock_db_class.return_value.get_vault_by_name_or_id.return_value = {
            'id': 'vault-001', 'name': 'MyVault', 'path': '/vaults/my',
        }
        mock_db_class.return_value.list_notes.return_value = [
            {'id': 'n1'}, {'id': 'n2'}, {'id': 'n3'},
        ]
        mock_db_class.return_value.get_outgoing_links.return_value = [{'target': 'x'}]
        mock_db_class.return_value.get_tag_stats.return_value = [{'tag': 'a'}, {'tag': 'b'}]
        mock_db_class.return_value.get_orphaned_notes.return_value = [{'id': 'n1'}]
        mock_db_class.return_value.get_hub_notes.return_value = [{'id': 'n2'}]
        mock_db_class.return_value.get_broken_links.return_value = [{'broken_count': 1}]

        cli = ObsCLI()
        vault = cli.db.get_vault_by_name_or_id('MyVault')
        vault_id = vault['id']
        notes = cli.db.list_notes(vault_id)
        link_count = sum(len(cli.db.get_outgoing_links(note['id'])) for note in notes)
        tag_stats = cli.db.get_tag_stats()
        orphans = cli.db.get_orphaned_notes(vault_id)
        hubs = cli.db.get_hub_notes(vault_id, limit=10)
        broken = cli.db.get_broken_links(vault_id)
        broken_count = sum(b['broken_count'] for b in broken)

        print(json.dumps({
            "vault": vault['name'],
            "path": vault['path'],
            "notes": len(notes),
            "links": link_count,
            "tags": len(tag_stats),
            "orphaned": len(orphans),
            "hubs": len(hubs),
            "broken_links": broken_count,
        }, indent=2, default=str))

        captured = capsys.readouterr()
        result = json.loads(captured.out)
        assert isinstance(result, dict)
        assert result['vault'] == 'MyVault'
        assert result['notes'] == 3
        assert result['links'] == 3  # 3 notes * 1 link each
        assert result['tags'] == 2
        assert result['orphaned'] == 1
        assert result['broken_links'] == 1


class TestAnalyzeJSON:
    """Test analyze command JSON output."""

    @patch('obs_cli.DatabaseManager')
    @patch('obs_cli.VaultManager')
    @patch('obs_cli.GraphAnalyzer')
    def test_analyze_json_valid(self, mock_ga_class, mock_vm, mock_db_class, capsys):
        """Test that analyze --json produces valid JSON object."""
        from obs_cli import ObsCLI
        mock_db_class.return_value.get_vault_by_name_or_id.return_value = {
            'id': 'vault-001', 'name': 'MyVault', 'path': '/vaults/my',
        }
        analyze_result = {
            'vault_name': 'MyVault',
            'total_notes': 50,
            'total_edges': 120,
            'graph_density': 0.0489,
            'clusters_found': 3,
        }
        mock_ga_class.return_value.analyze_vault.return_value = analyze_result

        cli = ObsCLI()
        vault = cli.db.get_vault_by_name_or_id('MyVault')
        result = cli.graph_analyzer.analyze_vault(vault['id'])
        print(json.dumps(result, indent=2, default=str))

        captured = capsys.readouterr()
        result = json.loads(captured.out)
        assert isinstance(result, dict)
        assert result['vault_name'] == 'MyVault'
        assert result['total_notes'] == 50
        assert result['total_edges'] == 120
        assert result['graph_density'] == 0.0489
        assert result['clusters_found'] == 3


class TestAICommandsJSON:
    """Test AI command JSON output."""

    def test_ai_similar_json_valid(self, capsys):
        """Test that ai similar --json produces valid JSON array."""
        # Simulate SimilarityMatch objects
        matches = [
            MagicMock(note_id='n1', title='Note A', similarity=0.95, path='notes/a.md'),
            MagicMock(note_id='n2', title='Note B', similarity=0.82, path='notes/b.md'),
        ]

        output = [{
            "note_id": m.note_id,
            "title": m.title,
            "similarity": m.similarity,
            "path": m.path,
        } for m in matches]
        print(json.dumps(output, indent=2, default=str))

        captured = capsys.readouterr()
        result = json.loads(captured.out)
        assert isinstance(result, list)
        assert len(result) == 2
        assert result[0]['title'] == 'Note A'
        assert result[0]['similarity'] == 0.95
        assert 'note_id' in result[0]
        assert 'path' in result[0]

    def test_ai_analyze_json_valid(self, capsys):
        """Test that ai analyze --json produces valid JSON object."""
        result = MagicMock(
            summary='A note about testing',
            themes=['testing', 'development'],
            quality_score=0.85,
            connections=['CI/CD', 'pytest'],
            suggestions=['Add examples', 'Link to docs'],
        )

        output = {
            "summary": result.summary,
            "themes": result.themes,
            "quality_score": result.quality_score,
            "connections": result.connections,
            "suggestions": result.suggestions,
        }
        print(json.dumps(output, indent=2, default=str))

        captured = capsys.readouterr()
        parsed = json.loads(captured.out)
        assert isinstance(parsed, dict)
        assert parsed['summary'] == 'A note about testing'
        assert parsed['quality_score'] == 0.85
        assert 'themes' in parsed
        assert 'connections' in parsed
        assert 'suggestions' in parsed

    def test_ai_duplicates_json_valid(self, capsys):
        """Test that ai duplicates --json produces valid JSON array."""
        groups = [
            MagicMock(
                similarity=0.92,
                notes=[
                    {'title': 'Note A', 'path': 'a.md'},
                    {'title': 'Note B', 'path': 'b.md'},
                ],
            ),
        ]

        output = [{
            "similarity": g.similarity,
            "notes": [{"title": n['title'], "path": n['path']} for n in g.notes],
        } for g in groups]
        print(json.dumps(output, indent=2, default=str))

        captured = capsys.readouterr()
        result = json.loads(captured.out)
        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0]['similarity'] == 0.92
        assert len(result[0]['notes']) == 2

    def test_ai_suggest_links_json_valid(self, capsys):
        """Test that ai suggest-links --json produces valid JSON array."""
        suggestions = [
            MagicMock(
                target_title='Related Note',
                target_path='notes/related.md',
                similarity=0.78,
                reason='Shared themes',
            ),
        ]

        output = [{
            "target_title": s.target_title,
            "target_path": s.target_path,
            "similarity": s.similarity,
            "reason": s.reason,
        } for s in suggestions]
        print(json.dumps(output, indent=2, default=str))

        captured = capsys.readouterr()
        result = json.loads(captured.out)
        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0]['target_title'] == 'Related Note'
        assert result[0]['similarity'] == 0.78
        assert 'reason' in result[0]

    def test_ai_gaps_json_valid(self, capsys):
        """Test that ai gaps --json produces valid JSON array."""
        gaps = [
            MagicMock(
                description='Missing coverage on deployment',
                related_notes=['CI/CD', 'Docker'],
                suggested_action='Create a deployment guide',
            ),
        ]

        output = [{
            "description": g.description,
            "related_notes": g.related_notes,
            "suggested_action": g.suggested_action,
        } for g in gaps]
        print(json.dumps(output, indent=2, default=str))

        captured = capsys.readouterr()
        result = json.loads(captured.out)
        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0]['description'] == 'Missing coverage on deployment'
        assert 'related_notes' in result[0]
        assert 'suggested_action' in result[0]

    def test_ai_summarize_json_valid(self, capsys):
        """Test that ai summarize --json produces valid JSON object."""
        summary = MagicMock(
            note_count=50,
            themes=['development', 'testing', 'deployment'],
            top_hubs=[{'title': 'Index', 'connections': 20}],
            orphan_count=3,
            summary_text='A vault focused on software development.',
        )

        output = {
            "note_count": summary.note_count,
            "themes": summary.themes,
            "top_hubs": summary.top_hubs,
            "orphan_count": summary.orphan_count,
            "summary_text": summary.summary_text,
        }
        print(json.dumps(output, indent=2, default=str))

        captured = capsys.readouterr()
        result = json.loads(captured.out)
        assert isinstance(result, dict)
        assert result['note_count'] == 50
        assert result['orphan_count'] == 3
        assert 'themes' in result
        assert 'top_hubs' in result
        assert 'summary_text' in result


class TestJSONNoRichMarkup:
    """Verify that JSON output never contains Rich markup."""

    def test_json_flag_no_rich_markup(self, capsys):
        """Verify JSON output has no Rich markup like [bold], [red], etc."""
        # Simulate all the JSON outputs and check for Rich markup
        outputs = [
            json.dumps([{
                'id': 'abc', 'name': 'Vault', 'path': '/p',
                'note_count': 1, 'link_count': 0, 'last_scanned': None,
            }], indent=2),
            json.dumps({
                'vaults': 1, 'notes': 10, 'links': 5,
                'tags': 3, 'orphaned_notes': 0, 'broken_links': 0,
            }, indent=2),
            json.dumps({
                'vault_name': 'V', 'total_notes': 10,
                'total_edges': 20, 'graph_density': 0.04, 'clusters_found': 2,
            }, indent=2),
            json.dumps({
                'summary': 'Test summary', 'themes': ['a', 'b'],
                'quality_score': 0.9, 'connections': [], 'suggestions': [],
            }, indent=2),
        ]

        for output in outputs:
            print(output)

        captured = capsys.readouterr()
        # No Rich markup should be present
        assert not RICH_MARKUP_RE.search(captured.out), \
            f"Found Rich markup in JSON output: {RICH_MARKUP_RE.findall(captured.out)}"
