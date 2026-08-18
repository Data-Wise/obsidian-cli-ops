"""Unit tests for core/flow_init.py — init wizard logic."""
from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
import yaml

sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent / "core"))

from core.flow_init import (
    FlowConfig,
    validate_config,
    init_flow_config,
    get_config_for_vault,
    _load_schema,
    _infer_vault_root,
    _infer_pairs,
    _SCHEMA_PATH,
)


# ---------------------------------------------------------------------------
# FlowConfig
# ---------------------------------------------------------------------------

class TestFlowConfig:
    def test_to_dict_minimal(self):
        c = FlowConfig(vault_root="~/vault", pairs=[{"vault": "a", "repo": "b"}])
        d = c.to_dict()
        assert d["vault_root"] == "~/vault"
        assert d["pairs"] == [{"vault": "a", "repo": "b"}]
        assert "include" not in d
        assert "exclude" not in d

    def test_to_dict_custom_include_exclude(self):
        c = FlowConfig(
            vault_root="~/vault",
            pairs=[{"vault": "a", "repo": "b"}],
            include=["*.md", "*.txt"],
            exclude=["_archive", "node_modules"],
        )
        d = c.to_dict()
        assert d["include"] == ["*.md", "*.txt"]
        assert d["exclude"] == ["_archive", "node_modules"]

    def test_to_yaml_output(self):
        c = FlowConfig(vault_root="~/vault", pairs=[{"vault": "a", "repo": "b"}])
        yml = c.to_yaml()
        assert "vault_root:" in yml
        assert "pairs:" in yml
        assert "vault: a" in yml


# ---------------------------------------------------------------------------
# Schema loading
# ---------------------------------------------------------------------------

class TestLoadSchema:
    def test_schema_exists(self):
        assert _SCHEMA_PATH.exists(), f"Schema not found: {_SCHEMA_PATH}"

    def test_schema_loads(self):
        schema = _load_schema()
        assert schema["title"] == "flow/obsidian-sync.yml"
        assert "vault_root" in schema["properties"]
        assert "pairs" in schema["properties"]


# ---------------------------------------------------------------------------
# validate_config
# ---------------------------------------------------------------------------

class TestValidateConfig:
    def test_valid_config(self):
        c = FlowConfig(
            vault_root="~/Library/Mobile Documents/iCloud~md~obsidian/Documents/Research",
            pairs=[{"vault": "teaching", "repo": "docs"}],
        )
        errors = validate_config(c)
        # vault_root may not exist on CI, so ignore that error
        errors = [e for e in errors if "not found" not in e]
        assert errors == []

    def test_missing_vault_root(self):
        c = FlowConfig(vault_root="", pairs=[{"vault": "a", "repo": "b"}])
        errors = validate_config(c)
        assert any("vault_root" in e for e in errors)

    def test_empty_pairs(self):
        c = FlowConfig(vault_root="~/vault", pairs=[])
        errors = validate_config(c)
        assert any("pairs" in e for e in errors)

    def test_pair_missing_vault(self):
        c = FlowConfig(vault_root="~/vault", pairs=[{"repo": "b"}])
        errors = validate_config(c)
        assert any("vault" in e for e in errors)

    def test_pair_missing_repo(self):
        c = FlowConfig(vault_root="~/vault", pairs=[{"vault": "a"}])
        errors = validate_config(c)
        assert any("repo" in e for e in errors)

    def test_pair_leading_slash_vault(self):
        c = FlowConfig(vault_root="~/vault", pairs=[{"vault": "/a", "repo": "b"}])
        errors = validate_config(c)
        assert any("start with /" in e for e in errors)

    def test_pair_leading_slash_repo(self):
        c = FlowConfig(vault_root="~/vault", pairs=[{"vault": "a", "repo": "/b"}])
        errors = validate_config(c)
        assert any("start with /" in e for e in errors)

    def test_pair_identity(self):
        c = FlowConfig(vault_root="~/vault", pairs=[{"vault": "x", "repo": "x"}])
        errors = validate_config(c)
        assert any("identical" in e for e in errors)

    def test_pair_duplicate(self):
        c = FlowConfig(
            vault_root="~/vault",
            pairs=[{"vault": "a", "repo": "b"}, {"vault": "a", "repo": "b"}],
        )
        errors = validate_config(c)
        assert any("duplicate" in e for e in errors)

    def test_multiple_errors(self):
        c = FlowConfig(vault_root="", pairs=[])
        errors = validate_config(c)
        assert len(errors) >= 2


# ---------------------------------------------------------------------------
# init_flow_config (non-interactive)
# ---------------------------------------------------------------------------

class TestInitFlowConfig:
    def test_non_interactive_creates_file(self, tmp_path):
        flow_dir = tmp_path / ".flow"
        flow_file = flow_dir / "obsidian-sync.yml"

        config = init_flow_config(
            directory=str(tmp_path),
            vault_root=str(tmp_path),  # Use tmp_path as vault_root (exists)
            pairs_json='[{"vault": "a", "repo": "b"}]',
            force=True,
            non_interactive=True,
        )

        assert flow_file.exists()
        assert config.vault_root == str(tmp_path)
        assert config.pairs == [{"vault": "a", "repo": "b"}]

    def test_non_interactive_writes_valid_yaml(self, tmp_path):
        init_flow_config(
            directory=str(tmp_path),
            vault_root=str(tmp_path),
            pairs_json='[{"vault": "a", "repo": "b"}]',
            force=True,
            non_interactive=True,
        )

        flow_file = tmp_path / ".flow" / "obsidian-sync.yml"
        with open(flow_file) as f:
            data = yaml.safe_load(f)

        assert data["vault_root"] == str(tmp_path)
        assert len(data["pairs"]) == 1

    def test_non_interactive_refuses_overwrite(self, tmp_path):
        flow_dir = tmp_path / ".flow"
        flow_dir.mkdir()
        flow_file = flow_dir / "obsidian-sync.yml"
        flow_file.write_text("existing")

        with pytest.raises(FileExistsError, match="already exists"):
            init_flow_config(
                directory=str(tmp_path),
                vault_root=str(tmp_path),
                pairs_json='[{"vault": "a", "repo": "b"}]',
                non_interactive=True,
            )

    def test_non_interactive_force_overwrite(self, tmp_path):
        flow_dir = tmp_path / ".flow"
        flow_dir.mkdir()
        flow_file = flow_dir / "obsidian-sync.yml"
        flow_file.write_text("existing")

        config = init_flow_config(
            directory=str(tmp_path),
            vault_root=str(tmp_path),
            pairs_json='[{"vault": "a", "repo": "b"}]',
            force=True,
            non_interactive=True,
        )
        assert config.vault_root == str(tmp_path)

    def test_non_interactive_missing_vault_root(self, tmp_path):
        with pytest.raises(ValueError, match="--vault-root required"):
            init_flow_config(
                directory=str(tmp_path),
                pairs_json='[{"vault": "a", "repo": "b"}]',
                non_interactive=True,
            )

    def test_non_interactive_missing_pairs(self, tmp_path):
        with pytest.raises(ValueError, match="--pairs required"):
            init_flow_config(
                directory=str(tmp_path),
                vault_root="~/vault",
                non_interactive=True,
            )

    def test_non_interactive_invalid_json(self, tmp_path):
        with pytest.raises(json.JSONDecodeError):
            init_flow_config(
                directory=str(tmp_path),
                vault_root="~/vault",
                pairs_json='not json',
                non_interactive=True,
            )

    def test_non_interactive_validation_error(self, tmp_path):
        with pytest.raises(ValueError, match="Validation failed"):
            init_flow_config(
                directory=str(tmp_path),
                vault_root="~/vault",
                pairs_json='[{"vault": "a", "repo": "a"}]',  # identity
                non_interactive=True,
            )

    def test_non_interactive_pairs_not_array(self, tmp_path):
        with pytest.raises(ValueError, match="must be a JSON array"):
            init_flow_config(
                directory=str(tmp_path),
                vault_root="~/vault",
                pairs_json='{"vault": "a", "repo": "b"}',
                non_interactive=True,
            )

    def test_non_interactive_pair_not_object(self, tmp_path):
        with pytest.raises(ValueError, match="must be a JSON object"):
            init_flow_config(
                directory=str(tmp_path),
                vault_root="~/vault",
                pairs_json='["not an object"]',
                non_interactive=True,
            )

    def test_non_interactive_pair_missing_keys(self, tmp_path):
        with pytest.raises(ValueError, match="must have 'vault' and 'repo'"):
            init_flow_config(
                directory=str(tmp_path),
                vault_root="~/vault",
                pairs_json='[{"vault": "a"}]',
                non_interactive=True,
            )


# ---------------------------------------------------------------------------
# Path traversal validation (Fix #5)
# ---------------------------------------------------------------------------

class TestPathTraversal:
    def test_vault_traversal(self):
        c = FlowConfig(vault_root="~/vault", pairs=[{"vault": "../../etc", "repo": "b"}])
        errors = validate_config(c)
        assert any(".." in e for e in errors)

    def test_repo_traversal(self):
        c = FlowConfig(vault_root="~/vault", pairs=[{"vault": "a", "repo": "../secret"}])
        errors = validate_config(c)
        assert any(".." in e for e in errors)

    def test_traversal_in_middle(self):
        c = FlowConfig(vault_root="~/vault", pairs=[{"vault": "a/../../b", "repo": "c"}])
        errors = validate_config(c)
        assert any(".." in e for e in errors)


# ---------------------------------------------------------------------------
# _infer_vault_root (Fix #13)
# ---------------------------------------------------------------------------

class TestInferVaultRoot:
    def test_finds_obsidian_dir(self, tmp_path):
        (tmp_path / ".obsidian").mkdir()
        assert _infer_vault_root(tmp_path) == str(tmp_path)

    def test_finds_parent_obsidian(self, tmp_path):
        nested = tmp_path / "subdir"
        nested.mkdir()
        (tmp_path / ".obsidian").mkdir()
        assert _infer_vault_root(nested) == str(tmp_path)

    def test_default_fallback(self, tmp_path):
        result = _infer_vault_root(tmp_path)
        assert "iCloud" in result or "Research" in result


# ---------------------------------------------------------------------------
# _infer_pairs (Fix #14)
# ---------------------------------------------------------------------------

class TestInferPairs:
    def test_returns_empty(self, tmp_path):
        # After fix #1, inference returns empty
        assert _infer_pairs(tmp_path) == []


# ---------------------------------------------------------------------------
# get_config_for_vault corrupted YAML (Fix #15)
# ---------------------------------------------------------------------------

class TestGetConfigCorrupted:
    def test_corrupted_yaml_returns_none(self, tmp_path):
        flow_dir = tmp_path / ".flow"
        flow_dir.mkdir()
        (flow_dir / "obsidian-sync.yml").write_text(": invalid: yaml: {{{}}}")
        config = get_config_for_vault(str(tmp_path))
        assert config is None

    def test_missing_file_returns_none(self, tmp_path):
        config = get_config_for_vault(str(tmp_path))
        assert config is None


# ---------------------------------------------------------------------------
# get_config_for_vault with valid file
# ---------------------------------------------------------------------------

class TestGetConfigValid:
    def test_loads_valid_config(self, tmp_path):
        flow_dir = tmp_path / ".flow"
        flow_dir.mkdir()
        (flow_dir / "obsidian-sync.yml").write_text(
            "vault_root: ~/vault\npairs:\n- vault: a\n  repo: b\n"
        )
        config = get_config_for_vault(str(tmp_path))
        assert config is not None
        assert config.vault_root == "~/vault"
        assert config.pairs == [{"vault": "a", "repo": "b"}]
