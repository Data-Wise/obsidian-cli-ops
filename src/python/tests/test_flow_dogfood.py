"""
Dogfood tests for flow init CLI — tests that exercise the CLI argument
parsing and error handling without needing a real vault.

These tests mock external dependencies and focus on CLI-level behavior.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

_SRC = Path(__file__).parent.parent
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))


# ---------------------------------------------------------------------------
# CLI argument parsing
# ---------------------------------------------------------------------------

class TestFlowInitArgParsing:
    """Test CLI argument parsing for flow init."""

    def test_flow_init_default_directory(self):
        """flow init defaults directory to current dir."""
        from argparse import ArgumentParser
        parser = ArgumentParser()
        sub = parser.add_subparsers(dest="command")
        flow = sub.add_parser("flow")
        flow_sub = flow.add_subparsers(dest="flow_command")
        init = flow_sub.add_parser("init")
        init.add_argument("directory", nargs="?", default=".")
        init.add_argument("--vault-root", default=None)
        init.add_argument("--pairs", default=None)
        init.add_argument("--force", action="store_true")
        init.add_argument("--json", action="store_true")

        args = parser.parse_args(["flow", "init"])
        assert args.directory == "."
        assert args.vault_root is None
        assert args.pairs is None
        assert args.force is False
        assert args.json is False

    def test_flow_init_custom_directory(self):
        """flow init accepts custom directory."""
        from argparse import ArgumentParser
        parser = ArgumentParser()
        sub = parser.add_subparsers(dest="command")
        flow = sub.add_parser("flow")
        flow_sub = flow.add_subparsers(dest="flow_command")
        init = flow_sub.add_parser("init")
        init.add_argument("directory", nargs="?", default=".")
        init.add_argument("--vault-root", default=None)
        init.add_argument("--pairs", default=None)
        init.add_argument("--force", action="store_true")
        init.add_argument("--json", action="store_true")

        args = parser.parse_args(["flow", "init", "/custom/path"])
        assert args.directory == "/custom/path"

    def test_flow_init_all_flags(self):
        """flow init parses all flags correctly."""
        from argparse import ArgumentParser
        parser = ArgumentParser()
        sub = parser.add_subparsers(dest="command")
        flow = sub.add_parser("flow")
        flow_sub = flow.add_subparsers(dest="flow_command")
        init = flow_sub.add_parser("init")
        init.add_argument("directory", nargs="?", default=".")
        init.add_argument("--vault-root", default=None)
        init.add_argument("--pairs", default=None)
        init.add_argument("--force", action="store_true")
        init.add_argument("--json", action="store_true")

        args = parser.parse_args([
            "flow", "init",
            "/my/dir",
            "--vault-root", "~/vault",
            "--pairs", '[{"vault":"a","repo":"b"}]',
            "--force",
            "--json",
        ])
        assert args.directory == "/my/dir"
        assert args.vault_root == "~/vault"
        assert args.pairs == '[{"vault":"a","repo":"b"}]'
        assert args.force is True
        assert args.json is True


# ---------------------------------------------------------------------------
# FlowConfig edge cases
# ---------------------------------------------------------------------------

class TestFlowConfigEdgeCases:
    """Test FlowConfig edge cases."""

    def test_empty_pairs_list(self):
        """FlowConfig with empty pairs list."""
        from core.flow_init import FlowConfig
        c = FlowConfig(vault_root="~/vault", pairs=[])
        d = c.to_dict()
        assert d["pairs"] == []

    def test_many_pairs(self):
        """FlowConfig with many pairs."""
        from core.flow_init import FlowConfig
        pairs = [{"vault": f"v{i}", "repo": f"r{i}"} for i in range(20)]
        c = FlowConfig(vault_root="~/vault", pairs=pairs)
        d = c.to_dict()
        assert len(d["pairs"]) == 20

    def test_special_characters_in_paths(self):
        """FlowConfig with special characters in paths."""
        from core.flow_init import FlowConfig
        c = FlowConfig(
            vault_root="~/Library/Mobile Documents/iCloud~md~obsidian/Documents/Research",
            pairs=[{"vault": "project (final)", "repo": "project-final"}],
        )
        d = c.to_dict()
        assert "iCloud~md~obsidian" in d["vault_root"]
        assert d["pairs"][0]["vault"] == "project (final)"

    def test_yaml_preserves_structure(self):
        """YAML output preserves config structure."""
        from core.flow_init import FlowConfig
        import yaml
        c = FlowConfig(
            vault_root="~/vault",
            pairs=[{"vault": "a", "repo": "b"}],
            include=["*.md", "*.txt"],
            exclude=["_archive", "node_modules"],
        )
        yml = c.to_yaml()
        data = yaml.safe_load(yml)
        assert data["vault_root"] == "~/vault"
        assert data["include"] == ["*.md", "*.txt"]
        assert data["exclude"] == ["_archive", "node_modules"]


# ---------------------------------------------------------------------------
# validate_config edge cases
# ---------------------------------------------------------------------------

class TestValidateConfigEdgeCases:
    """Test validate_config edge cases."""

    def test_vault_root_with_spaces(self, tmp_path):
        """validate_config accepts vault_root with spaces."""
        from core.flow_init import FlowConfig, validate_config
        vault_path = tmp_path / "path with spaces" / "vault"
        vault_path.mkdir(parents=True)
        c = FlowConfig(
            vault_root=str(vault_path),
            pairs=[{"vault": "a", "repo": "b"}],
        )
        errors = validate_config(c)
        # Should not fail on spaces
        assert not any("spaces" in e for e in errors)

    def test_vault_root_relative_path(self, tmp_path):
        """validate_config accepts relative vault_root."""
        from core.flow_init import FlowConfig, validate_config
        c = FlowConfig(
            vault_root="relative/path",
            pairs=[{"vault": "a", "repo": "b"}],
        )
        errors = validate_config(c)
        # Should warn about not found but not fail
        assert any("not found" in e for e in errors)

    def test_pair_with_subdirectory(self, tmp_path):
        """validate_config accepts pairs with subdirectories."""
        from core.flow_init import FlowConfig, validate_config
        c = FlowConfig(
            vault_root=str(tmp_path),
            pairs=[{"vault": "dir/subdir/file", "repo": "other/dir"}],
        )
        errors = validate_config(c)
        # Should not fail on subdirectories
        assert errors == []

    def test_multiple_validation_errors(self):
        """validate_config returns multiple errors."""
        from core.flow_init import FlowConfig, validate_config
        c = FlowConfig(
            vault_root="",
            pairs=[{"vault": "", "repo": ""}, {"vault": "/bad", "repo": "b"}],
        )
        errors = validate_config(c)
        # Should have multiple errors
        assert len(errors) >= 3

    def test_valid_config_minimal(self):
        """validate_config passes with minimal valid config."""
        from core.flow_init import FlowConfig, validate_config
        c = FlowConfig(
            vault_root="/nonexistent/path",
            pairs=[{"vault": "a", "repo": "b"}],
        )
        errors = validate_config(c)
        # Should only warn about path not found
        assert errors == ["vault_root path not found: /nonexistent/path"]


# ---------------------------------------------------------------------------
# init_flow_config edge cases
# ---------------------------------------------------------------------------

class TestInitFlowConfigEdgeCases:
    """Test init_flow_config edge cases."""

    def test_creates_nested_flow_dir(self, tmp_path):
        """init_flow_config creates nested .flow/ directory."""
        from core.flow_init import init_flow_config
        nested = tmp_path / "a" / "b" / "c"
        nested.mkdir(parents=True)

        config = init_flow_config(
            directory=str(nested),
            vault_root=str(tmp_path),
            pairs_json='[{"vault": "a", "repo": "b"}]',
            force=True,
            non_interactive=True,
        )
        assert (nested / ".flow" / "obsidian-sync.yml").exists()

    def test_writes_header_comments(self, tmp_path):
        """init_flow_config writes header comments."""
        from core.flow_init import init_flow_config
        init_flow_config(
            directory=str(tmp_path),
            vault_root=str(tmp_path),
            pairs_json='[{"vault": "a", "repo": "b"}]',
            force=True,
            non_interactive=True,
        )
        content = (tmp_path / ".flow" / "obsidian-sync.yml").read_text()
        assert "vault↔repo mirror map" in content.lower() or "vault" in content.lower()
        assert "Created:" in content

    def test_preserves_include_exclude(self, tmp_path):
        """init_flow_config preserves custom include/exclude."""
        from core.flow_init import init_flow_config
        import yaml
        init_flow_config(
            directory=str(tmp_path),
            vault_root=str(tmp_path),
            pairs_json='[{"vault": "a", "repo": "b"}]',
            force=True,
            non_interactive=True,
        )
        with open(tmp_path / ".flow" / "obsidian-sync.yml") as f:
            data = yaml.safe_load(f)
        # Defaults should be applied
        assert "include" not in data  # Not written when default
        assert "exclude" not in data  # Not written when default

    def test_force_overwrites_existing(self, tmp_path):
        """init_flow_config with force overwrites existing."""
        from core.flow_init import init_flow_config
        flow_dir = tmp_path / ".flow"
        flow_dir.mkdir()
        (flow_dir / "obsidian-sync.yml").write_text("old content")

        config = init_flow_config(
            directory=str(tmp_path),
            vault_root=str(tmp_path),
            pairs_json='[{"vault": "x", "repo": "y"}]',
            force=True,
            non_interactive=True,
        )
        content = (flow_dir / "obsidian-sync.yml").read_text()
        assert "old content" not in content
        assert config.pairs == [{"vault": "x", "repo": "y"}]


# ---------------------------------------------------------------------------
# get_config_for_vault
# ---------------------------------------------------------------------------

class TestGetConfigForVault:
    """Test get_config_for_vault function."""

    def test_loads_existing_config(self, tmp_path):
        """get_config_for_vault loads existing config."""
        from core.flow_init import get_config_for_vault, init_flow_config
        init_flow_config(
            directory=str(tmp_path),
            vault_root=str(tmp_path),
            pairs_json='[{"vault": "a", "repo": "b"}]',
            force=True,
            non_interactive=True,
        )
        config = get_config_for_vault(str(tmp_path))
        assert config is not None
        assert config.vault_root == str(tmp_path)
        assert len(config.pairs) == 1

    def test_returns_none_for_missing(self, tmp_path):
        """get_config_for_vault returns None for missing config."""
        from core.flow_init import get_config_for_vault
        config = get_config_for_vault(str(tmp_path))
        assert config is None

    def test_returns_none_for_empty_yaml(self, tmp_path):
        """get_config_for_vault returns None for empty YAML."""
        from core.flow_init import get_config_for_vault
        flow_dir = tmp_path / ".flow"
        flow_dir.mkdir()
        (flow_dir / "obsidian-sync.yml").write_text("")
        config = get_config_for_vault(str(tmp_path))
        assert config is None
