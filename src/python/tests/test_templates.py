"""Tests for core/templates.py — vault template ops (nexus port)."""

import json
from datetime import datetime
from pathlib import Path

import pytest

import config_loader
from core import templates as t

NOW = datetime(2026, 9, 25, 14, 5, 9)


@pytest.fixture(autouse=True)
def no_user_config(monkeypatch):
    """Never read the developer's real ~/.config/obs/config.yaml."""
    monkeypatch.setattr(config_loader, "load", lambda: None)


@pytest.fixture
def vault(tmp_path):
    root = tmp_path / "My Vault"
    (root / ".obsidian").mkdir(parents=True)
    return root


def _tpl(folder: Path, name: str, body: str) -> Path:
    folder.mkdir(parents=True, exist_ok=True)
    p = folder / name
    p.write_text(body, encoding="utf-8")
    return p


# ── Folder resolution ────────────────────────────────────────────────────────

def test_no_templates_folder(vault):
    assert t.find_templates_dir(vault) is None
    assert t.list_templates(vault) == []


def test_fallback_order_prefers_system_templates(vault):
    _tpl(vault / "templates", "a.md", "x")
    _tpl(vault / "_SYSTEM/templates", "b.md", "x")
    tdir = t.find_templates_dir(vault)
    assert tdir.path == vault / "_SYSTEM/templates"
    assert tdir.source == "fallback"


def test_obsidian_setting_wins_over_fallbacks(vault):
    _tpl(vault / "_SYSTEM/templates", "b.md", "x")
    _tpl(vault / "Meta/Tpl", "c.md", "x")
    (vault / ".obsidian/templates.json").write_text(json.dumps({"folder": "Meta/Tpl"}))
    tdir = t.find_templates_dir(vault)
    assert (tdir.path, tdir.source) == (vault / "Meta/Tpl", "obsidian")


def test_obsidian_setting_pointing_at_missing_folder_falls_through(vault):
    _tpl(vault / "templates", "a.md", "x")
    (vault / ".obsidian/templates.json").write_text(json.dumps({"folder": "Gone"}))
    assert t.find_templates_dir(vault).path == vault / "templates"


def test_malformed_obsidian_setting_is_ignored(vault):
    _tpl(vault / "templates", "a.md", "x")
    (vault / ".obsidian/templates.json").write_text("{not json")
    assert t.find_templates_dir(vault).source == "fallback"


def test_config_templates_used_for_matching_vault(vault, monkeypatch):
    custom = vault / "Custom"
    _tpl(custom, "a.md", "x")
    _tpl(vault / "templates", "b.md", "x")
    cfg = config_loader.ObsConfig(root=vault, templates=custom)
    monkeypatch.setattr(config_loader, "load", lambda: cfg)
    assert t.find_templates_dir(vault).source == "config"


def test_config_for_other_vault_is_ignored(vault, tmp_path, monkeypatch):
    other = tmp_path / "Other"
    _tpl(other / "_SYSTEM/templates", "a.md", "x")
    _tpl(vault / "templates", "b.md", "x")
    cfg = config_loader.ObsConfig(root=other)
    monkeypatch.setattr(config_loader, "load", lambda: cfg)
    assert t.find_templates_dir(vault).path == vault / "templates"


def test_vault_less_config_is_ignored(vault, monkeypatch):
    _tpl(vault / "templates", "b.md", "x")
    monkeypatch.setattr(config_loader, "load", lambda: config_loader.ObsConfig())
    assert t.find_templates_dir(vault).source == "fallback"


# ── Listing and lookup ───────────────────────────────────────────────────────

def test_list_strips_tpl_prefix_and_sorts(vault):
    folder = vault / "templates"
    _tpl(folder, "tpl-meeting.md", "x")
    _tpl(folder, "Daily.md", "x")
    _tpl(folder / "sub", "idea.md", "x")
    _tpl(folder, "notes.txt", "ignored")
    names = [i["name"] for i in t.list_templates(vault)]
    assert names == ["Daily", "idea", "meeting"]


def test_resolve_template_accepts_prefix_suffix_and_nested(vault):
    folder = vault / "templates"
    meeting = _tpl(folder, "tpl-meeting.md", "x")
    idea = _tpl(folder / "sub", "idea.md", "x")
    assert t.resolve_template(vault, "meeting") == meeting
    assert t.resolve_template(vault, "tpl-meeting.md") == meeting
    assert t.resolve_template(vault, "idea") == idea


def test_resolve_template_missing(vault):
    _tpl(vault / "templates", "a.md", "x")
    with pytest.raises(t.TemplateError, match="Template not found"):
        t.resolve_template(vault, "nope")


# ── Rendering ────────────────────────────────────────────────────────────────

def test_render_core_variables():
    out = t.render("# {{title}}\n{{date}} {{time}}", "My Note", now=NOW)
    assert out == "# My Note\n2026-09-25 14:05"


def test_render_moment_formats():
    out = t.render("{{date:dddd, MMMM DD YYYY}}|{{time:HH:mm:ss}}|{{date:YY-MM}}", "x", now=NOW)
    assert out == "Friday, September 25 2026|14:05:09|26-09"


def test_render_custom_variables_override_title():
    out = t.render("{{title}} by {{author}}", "file-stem", {"title": "Real", "author": "DT"}, NOW)
    assert out == "Real by DT"


def test_render_leaves_unknown_and_templater_untouched():
    body = "{{unknown}} <% tp.date.now() %> {{ date }}"
    assert t.render(body, "x", now=NOW) == "{{unknown}} <% tp.date.now() %> 2026-09-25"


# ── Creating notes ───────────────────────────────────────────────────────────

def test_create_from_template(vault):
    _tpl(vault / "templates", "tpl-idea.md", "# {{title}}\nCreated {{date}} for {{project}}\n")
    r = t.create_from_template(vault, "idea", "Lit Review/My Note", {"project": "pmed"}, NOW)
    note = vault / "Lit Review" / "My Note.md"
    assert Path(r["path"]) == note.resolve()
    assert r["relative"] == str(Path("Lit Review/My Note.md"))
    assert note.read_text() == "# My Note\nCreated 2026-09-25 for pmed\n"


def test_create_refuses_overwrite(vault):
    _tpl(vault / "templates", "a.md", "new body")
    (vault / "Existing.md").write_text("keep me")
    with pytest.raises(t.TemplateError, match="already exists"):
        t.create_from_template(vault, "a", "Existing.md")
    assert (vault / "Existing.md").read_text() == "keep me"


def test_create_refuses_path_traversal(vault):
    _tpl(vault / "templates", "a.md", "x")
    with pytest.raises(t.TemplateError, match="escapes the vault"):
        t.create_from_template(vault, "a", "../outside")
    assert not (vault.parent / "outside.md").exists()


def test_create_refuses_absolute_and_empty_dest(vault, tmp_path):
    _tpl(vault / "templates", "a.md", "x")
    with pytest.raises(t.TemplateError, match="relative"):
        t.create_from_template(vault, "a", str(tmp_path / "abs"))
    with pytest.raises(t.TemplateError, match="empty"):
        t.create_from_template(vault, "a", "  ")


# ── Hardening: template-name escape, degenerate destinations, formats ────────

def test_template_name_cannot_escape_templates_folder(vault):
    _tpl(vault / "templates", "a.md", "x")
    _tpl(vault / "Private", "diary.md", "secret")
    with pytest.raises(t.TemplateError, match="escapes the templates folder"):
        t.resolve_template(vault, "../Private/diary")
    with pytest.raises(t.TemplateError, match="Invalid template name"):
        t.resolve_template(vault, str(vault / "Private" / "diary"))


def test_nested_template_name_with_folder_still_resolves(vault):
    idea = _tpl(vault / "templates" / "sub", "idea.md", "x")
    assert t.resolve_template(vault, "sub/idea") == idea


def test_destination_without_file_name_is_refused(vault):
    _tpl(vault / "templates", "a.md", "x")
    for dest in (".", "notes/.."):
        with pytest.raises(t.TemplateError):
            t.create_from_template(vault, "a", dest)


def test_render_unpadded_tokens_and_literal_escape():
    out = t.render("{{date:MMM D, YYYY [at] h A}}|{{date:M/D H}}", "x", now=NOW)
    assert out == "Sep 25, 2026 at 2 PM|9/25 14"


def test_obsidian_date_and_time_formats_apply_to_bare_placeholders(vault):
    _tpl(vault / "templates", "a.md", "{{date}} {{time}} {{date:YYYY}}")
    (vault / ".obsidian/templates.json").write_text(
        json.dumps({"dateFormat": "DD.MM.YYYY", "timeFormat": "HH:mm:ss"}))
    t.create_from_template(vault, "a", "Out", now=NOW)
    assert (vault / "Out.md").read_text() == "25.09.2026 14:05:09 2026"
