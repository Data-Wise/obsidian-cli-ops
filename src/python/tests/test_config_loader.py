"""Tests for config_loader.py — Phase 1."""

import sys
from pathlib import Path

import pytest

# Ensure the python src dir is on the path when running standalone
sys.path.insert(0, str(Path(__file__).parent.parent))

import config_loader as cl


# ──────────────────────────────────────────────────────────────────────────────
# Shell-env parser helpers
# ──────────────────────────────────────────────────────────────────────────────

class TestShellEnvParsers:
    def test_shell_str_double_quotes(self):
        text = 'OBS_ROOT="/some/path"'
        assert cl._shell_str(text, "OBS_ROOT") == "/some/path"

    def test_shell_str_single_quotes(self):
        assert cl._shell_str("KEY='/a/b'", "KEY") == "/a/b"

    def test_shell_str_no_quotes(self):
        assert cl._shell_str("KEY=value", "KEY") == "value"

    def test_shell_str_missing(self):
        assert cl._shell_str("OTHER=x", "OBS_ROOT") is None

    def test_shell_array_bare(self):
        assert cl._shell_array("VAULTS=(Research KB)", "VAULTS") == ["Research", "KB"]

    def test_shell_array_quoted(self):
        text = 'VAULTS=("Research" "Knowledge_Base" "Life_Admin")'
        assert cl._shell_array(text, "VAULTS") == ["Research", "Knowledge_Base", "Life_Admin"]

    def test_shell_array_missing(self):
        assert cl._shell_array("OTHER=(x)", "VAULTS") == []

    def test_shell_array_empty(self):
        assert cl._shell_array("VAULTS=()", "VAULTS") == []


# ──────────────────────────────────────────────────────────────────────────────
# Legacy obs shell-env loader
# ──────────────────────────────────────────────────────────────────────────────

class TestLoadLegacyObs:
    def test_parses_full_env(self, tmp_path, monkeypatch):
        cfg_file = tmp_path / "config"
        cfg_file.write_text(
            'OBS_ROOT="/Users/dt/Vaults"\n'
            'VAULTS=("Research" "Notes")\n'
            'PLUGIN_REGISTRY="https://example.com/plugins.json"\n',
            encoding="utf-8",
        )
        monkeypatch.setattr(cl, "_LEGACY_OBS_PATH", cfg_file)
        cfg = cl._load_legacy_obs()
        assert cfg is not None
        assert cfg.root == Path("/Users/dt/Vaults")
        assert cfg.active == ["Research", "Notes"]
        assert cfg.registry == "https://example.com/plugins.json"

    def test_returns_none_when_file_missing(self, tmp_path, monkeypatch):
        monkeypatch.setattr(cl, "_LEGACY_OBS_PATH", tmp_path / "nope")
        assert cl._load_legacy_obs() is None

    def test_returns_none_when_no_obs_root(self, tmp_path, monkeypatch):
        cfg_file = tmp_path / "config"
        cfg_file.write_text("VAULTS=(Research)\n", encoding="utf-8")
        monkeypatch.setattr(cl, "_LEGACY_OBS_PATH", cfg_file)
        assert cl._load_legacy_obs() is None

    def test_default_registry_when_absent(self, tmp_path, monkeypatch):
        cfg_file = tmp_path / "config"
        cfg_file.write_text('OBS_ROOT="/vault"\nVAULTS=(A)\n', encoding="utf-8")
        monkeypatch.setattr(cl, "_LEGACY_OBS_PATH", cfg_file)
        cfg = cl._load_legacy_obs()
        assert cfg.registry == cl.DEFAULT_REGISTRY


# ──────────────────────────────────────────────────────────────────────────────
# Legacy nexus YAML loader
# ──────────────────────────────────────────────────────────────────────────────

class TestLoadLegacyNexus:
    NEXUS_YAML = """\
zotero:
  database: ~/Zotero/zotero.sqlite
  storage: ~/Zotero/storage
vault:
  path: ~/Library/Mobile Documents/iCloud~md~obsidian/Documents
  templates: ~/Library/Mobile Documents/iCloud~md~obsidian/Documents/_SYSTEM/templates
pdf:
  directories:
    - ~/Documents/Research/PDFs
    - ~/Documents/Teaching/PDFs
"""

    def test_parses_full_nexus_yaml(self, tmp_path, monkeypatch):
        p = tmp_path / "config.yaml"
        p.write_text(self.NEXUS_YAML, encoding="utf-8")
        monkeypatch.setattr(cl, "_LEGACY_NEXUS_PATH", p)
        # hide the other sources
        monkeypatch.setattr(cl, "_UNIFIED_PATH", tmp_path / "nope.yaml")
        monkeypatch.setattr(cl, "_LEGACY_OBS_PATH", tmp_path / "nope")

        cfg = cl._load_legacy_nexus()
        assert cfg is not None
        assert cfg.root == Path.home() / "Library/Mobile Documents/iCloud~md~obsidian/Documents"
        assert cfg.research is not None
        assert cfg.research.zotero is not None
        assert cfg.research.zotero.database == Path.home() / "Zotero/zotero.sqlite"
        assert len(cfg.research.pdf_directories) == 2

    def test_active_is_empty_for_nexus_migration(self, tmp_path, monkeypatch):
        p = tmp_path / "config.yaml"
        p.write_text(self.NEXUS_YAML, encoding="utf-8")
        monkeypatch.setattr(cl, "_LEGACY_NEXUS_PATH", p)
        cfg = cl._load_legacy_nexus()
        assert cfg.active == []

    def test_returns_none_when_file_missing(self, tmp_path, monkeypatch):
        monkeypatch.setattr(cl, "_LEGACY_NEXUS_PATH", tmp_path / "nope.yaml")
        assert cl._load_legacy_nexus() is None


# ──────────────────────────────────────────────────────────────────────────────
# Unified YAML loader
# ──────────────────────────────────────────────────────────────────────────────

class TestLoadUnified:
    MINIMAL_YAML = """\
version: 1
vault:
  root: ~/Vaults
  active:
    - Research
    - Notes
"""
    FULL_YAML = """\
version: 1
vault:
  root: ~/Vaults
  active:
    - Research
  templates: ~/Vaults/_SYSTEM/templates
research:
  zotero:
    database: ~/Zotero/zotero.sqlite
    storage: ~/Zotero/storage
  pdf:
    directories:
      - ~/Documents/PDFs
plugins:
  registry: https://example.com/plugins.json
"""

    def test_parses_minimal(self, tmp_path, monkeypatch):
        p = tmp_path / "config.yaml"
        p.write_text(self.MINIMAL_YAML, encoding="utf-8")
        monkeypatch.setattr(cl, "_UNIFIED_PATH", p)
        cfg = cl._load_unified()
        assert cfg is not None
        assert cfg.root == Path.home() / "Vaults"
        assert cfg.active == ["Research", "Notes"]
        assert cfg.research is None
        assert cfg.registry == cl.DEFAULT_REGISTRY

    def test_parses_full(self, tmp_path, monkeypatch):
        p = tmp_path / "config.yaml"
        p.write_text(self.FULL_YAML, encoding="utf-8")
        monkeypatch.setattr(cl, "_UNIFIED_PATH", p)
        cfg = cl._load_unified()
        assert cfg is not None
        assert cfg.research is not None
        assert cfg.research.zotero is not None
        assert len(cfg.research.pdf_directories) == 1
        assert cfg.registry == "https://example.com/plugins.json"

    def test_returns_none_when_missing(self, tmp_path, monkeypatch):
        monkeypatch.setattr(cl, "_UNIFIED_PATH", tmp_path / "nope.yaml")
        assert cl._load_unified() is None


# ──────────────────────────────────────────────────────────────────────────────
# Priority chain: load()
# ──────────────────────────────────────────────────────────────────────────────

class TestLoadPriorityChain:
    def test_unified_wins_over_legacy(self, tmp_path, monkeypatch):
        unified = tmp_path / "config.yaml"
        unified.write_text(
            "version: 1\nvault:\n  root: ~/Unified\n  active:\n    - U\n",
            encoding="utf-8",
        )
        legacy = tmp_path / "config"
        legacy.write_text('OBS_ROOT="/LegacyObs"\nVAULTS=(L)\n', encoding="utf-8")

        monkeypatch.setattr(cl, "_UNIFIED_PATH", unified)
        monkeypatch.setattr(cl, "_LEGACY_OBS_PATH", legacy)
        monkeypatch.setattr(cl, "_LEGACY_NEXUS_PATH", tmp_path / "nope.yaml")

        cfg = cl.load()
        assert cfg is not None
        assert cfg.source == "unified"
        assert cfg.active == ["U"]

    def test_legacy_obs_wins_when_no_unified(self, tmp_path, monkeypatch):
        legacy = tmp_path / "config"
        legacy.write_text('OBS_ROOT="/LegacyObs"\nVAULTS=(L)\n', encoding="utf-8")
        monkeypatch.setattr(cl, "_UNIFIED_PATH", tmp_path / "nope.yaml")
        monkeypatch.setattr(cl, "_LEGACY_OBS_PATH", legacy)
        monkeypatch.setattr(cl, "_LEGACY_NEXUS_PATH", tmp_path / "nope2.yaml")

        cfg = cl.load()
        assert cfg is not None
        assert cfg.source == "legacy-obs"

    def test_returns_none_when_nothing_found(self, tmp_path, monkeypatch):
        monkeypatch.setattr(cl, "_UNIFIED_PATH", tmp_path / "a.yaml")
        monkeypatch.setattr(cl, "_LEGACY_OBS_PATH", tmp_path / "b")
        monkeypatch.setattr(cl, "_LEGACY_NEXUS_PATH", tmp_path / "c.yaml")
        assert cl.load() is None


# ──────────────────────────────────────────────────────────────────────────────
# ObsConfig helpers
# ──────────────────────────────────────────────────────────────────────────────

class TestObsConfigHelpers:
    def test_templates_resolved_uses_explicit(self):
        cfg = cl.ObsConfig(
            root=Path("/vault"),
            templates=Path("/vault/my-templates"),
        )
        assert cfg.templates_resolved == Path("/vault/my-templates")

    def test_templates_resolved_defaults_to_subpath(self):
        cfg = cl.ObsConfig(root=Path("/vault"))
        assert cfg.templates_resolved == Path("/vault/_SYSTEM/templates")


# ──────────────────────────────────────────────────────────────────────────────
# _to_yaml round-trip
# ──────────────────────────────────────────────────────────────────────────────

class TestToYaml:
    def test_round_trip_minimal(self, tmp_path, monkeypatch):
        """Write then re-read should give the same root and active list."""
        import yaml as _yaml

        cfg = cl.ObsConfig(root=Path("/vault"), active=["Research", "Notes"])
        yaml_text = cl._to_yaml(cfg)
        doc = _yaml.safe_load(yaml_text)
        assert doc["vault"]["root"] == "/vault"
        assert doc["vault"]["active"] == ["Research", "Notes"]
        assert "research" not in doc

    def test_research_section_included_when_present(self):
        import yaml as _yaml

        cfg = cl.ObsConfig(
            root=Path("/vault"),
            active=["Research"],
            research=cl.ResearchConfig(
                zotero=cl.ZoteroConfig(
                    database=Path("/zotero.sqlite"),
                    storage=Path("/zotero/storage"),
                ),
                pdf_directories=[Path("/pdfs")],
            ),
        )
        doc = _yaml.safe_load(cl._to_yaml(cfg))
        assert "research" in doc
        assert doc["research"]["zotero"]["database"] == "/zotero.sqlite"
        assert doc["research"]["pdf"]["directories"] == ["/pdfs"]

    def test_custom_registry_included(self):
        import yaml as _yaml

        cfg = cl.ObsConfig(root=Path("/v"), registry="https://custom.example/p.json")
        doc = _yaml.safe_load(cl._to_yaml(cfg))
        assert doc["plugins"]["registry"] == "https://custom.example/p.json"

    def test_default_registry_omitted(self):
        import yaml as _yaml

        cfg = cl.ObsConfig(root=Path("/v"))
        doc = _yaml.safe_load(cl._to_yaml(cfg))
        assert "plugins" not in doc
