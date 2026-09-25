"""Drift guard for the Claude Code plugin skills in ``plugin/skills/``.

The skills route tasks to obsidian-ops MCP tools and ``obs`` CLI commands by
name. A renamed tool or subcommand would leave a skill telling Claude to call
something that no longer exists, so every name a skill mentions is checked
against the source of truth: ``@mcp.tool`` functions in ``mcp_server.py`` and
argparse (``obs_cli.py <cmd> --help`` must exit 0).
"""
import ast
import json
import re
import sys
from pathlib import Path
from unittest import mock

import pytest

import obs_cli

ROOT = Path(__file__).resolve().parents[3]
PLUGIN = ROOT / "plugin"
SKILLS = sorted(PLUGIN.glob("skills/*/SKILL.md"))
MCP_SERVER = ROOT / "src" / "python" / "mcp_server.py"


def _mcp_tools() -> set[str]:
    tree = ast.parse(MCP_SERVER.read_text(encoding="utf-8"))
    names = set()
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            for dec in node.decorator_list:
                if isinstance(dec, ast.Call) and getattr(dec.func, "attr", "") == "tool":
                    names.add(node.name)
    return names


def _code_spans(text: str) -> list[str]:
    return re.findall(r"`([^`\n]+)`", text)


def _tool_calls(text: str) -> set[str]:
    """Names written as `name(...)` in code spans."""
    return {m.group(1) for span in _code_spans(text)
            for m in [re.match(r"([a-z_]+)\(", span)] if m}


def _obs_commands(text: str) -> set[tuple[str, ...]]:
    """Command words of each `obs ...` span, up to the first argument/flag."""
    cmds = set()
    for span in _code_spans(text):
        if not span.startswith("obs "):
            continue
        words = []
        for tok in span.split()[1:]:
            if not re.fullmatch(r"[a-z][a-z-]*", tok):
                break
            words.append(tok)
        if words:
            cmds.add(tuple(words))
    return cmds


def test_plugin_manifest_lists_skills_dir():
    manifest = json.loads((PLUGIN / ".claude-plugin" / "plugin.json").read_text())
    assert manifest["name"] == "obsidian-ops"
    assert (PLUGIN / manifest["skills"]).is_dir()
    assert len(SKILLS) == 2


@pytest.mark.parametrize("skill", SKILLS, ids=lambda p: p.parent.name)
def test_skill_frontmatter(skill):
    text = skill.read_text(encoding="utf-8")
    m = re.match(r"---\nname: ([a-z-]+)\ndescription: (.+?)\n---\n", text, re.S)
    assert m, "SKILL.md must start with name/description frontmatter"
    assert m.group(1) == skill.parent.name
    assert m.group(2).startswith("Use when")


@pytest.mark.parametrize("skill", SKILLS, ids=lambda p: p.parent.name)
def test_skill_mcp_tools_exist(skill):
    missing = _tool_calls(skill.read_text(encoding="utf-8")) - _mcp_tools()
    assert not missing, f"{skill.parent.name} names MCP tools that do not exist: {sorted(missing)}"


def _all_obs_commands():
    return sorted({c for s in SKILLS for c in _obs_commands(s.read_text(encoding="utf-8"))})


@pytest.mark.parametrize("words", _all_obs_commands(), ids=" ".join)
def test_skill_obs_commands_exist(words, tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    with mock.patch.object(sys, "argv", ["obs_cli.py", *words, "--help"]):
        with pytest.raises(SystemExit) as exc:
            obs_cli.main()
    assert exc.value.code == 0, f"`obs {' '.join(words)}` is not a valid command"


def test_extractors_catch_a_bad_name():
    """Positive control: a planted bad tool and bad command are both detected."""
    planted = "`not_a_tool(x)` and `obs research nope list`"
    assert "not_a_tool" in _tool_calls(planted) - _mcp_tools()
    assert ("research", "nope", "list") in _obs_commands(planted)
