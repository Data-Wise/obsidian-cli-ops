"""Tests for obs link — the .obs/sync.yml writer (docs-standards ADR-001)."""
import yaml

from research.obs_link import build_sync_map, write_link


def test_build_sync_map_defaults_to_none_for_non_vault():
    doc = build_sync_map()
    assert doc["mirror"] == "none"
    assert "pairs" not in doc
    assert doc["schema"] == 1


def test_build_sync_map_active_with_vault_root():
    doc = build_sync_map(
        vault_root="~/vault/Research/x",
        pairs=[{"vault": "teaching", "repo": "teaching"}],
    )
    assert doc["mirror"] == "mirror"
    assert doc["vault_root"].endswith("/x")
    assert doc["include"] == ["*.md"]
    assert doc["pairs"][0]["repo"] == "teaching"


def test_write_link_creates_file(tmp_path):
    res = write_link(tmp_path)
    assert res["created"] is True
    target = tmp_path / ".obs" / "sync.yml"
    assert target.exists()
    data = yaml.safe_load(target.read_text())
    assert data["mirror"] == "none"
    assert data["schema"] == 1


def test_write_link_is_idempotent(tmp_path):
    write_link(tmp_path)
    res2 = write_link(tmp_path)
    assert res2["created"] is False
    assert res2["existed"] is True


def test_write_link_force_overwrites(tmp_path):
    write_link(tmp_path, mirror="none")
    res = write_link(tmp_path, vault_root="~/v", mirror="mirror", force=True)
    assert res["created"] is True
    data = yaml.safe_load((tmp_path / ".obs" / "sync.yml").read_text())
    assert data["mirror"] == "mirror"
