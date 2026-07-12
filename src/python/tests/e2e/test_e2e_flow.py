"""
E2E tests for flow init subcommand.

These tests create isolated directories and exercise the flow init
subcommand via the obs_cli.py subprocess.

No external APIs or network needed — all data is local filesystem.

Requirements:
  - obs venv installed (install.sh or brew)

Marks:
  @pytest.mark.e2e   — skipped unless E2E=1 env var is set
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

_SRC = Path(__file__).parent.parent.parent
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

_RUN_E2E = os.environ.get("E2E", "").strip() in ("1", "true", "yes")
pytestmark = pytest.mark.skipif(
    not _RUN_E2E,
    reason="E2E tests skipped — set E2E=1 to run",
)


def _find_obs_python() -> str:
    if env := os.environ.get("OBS_PYTHON"):
        if Path(env).exists():
            return env
    candidates = [
        Path.home() / ".local/share/obs/venv/bin/python3",
        Path("/opt/homebrew/opt/obsidian-cli-ops/libexec/venv/bin/python3"),
    ]
    for p in candidates:
        if p.exists():
            return str(p)
    return sys.executable


_OBS_PYTHON = _find_obs_python()
_OBS_CLI = _SRC / "obs_cli.py"


def _run_obs(*args: str, cwd: str | None = None) -> subprocess.CompletedProcess:
    """Run obs CLI as subprocess."""
    return subprocess.run(
        [_OBS_PYTHON, str(_OBS_CLI), *args],
        capture_output=True,
        text=True,
        cwd=cwd,
        timeout=30,
    )


# ---------------------------------------------------------------------------
# flow init — basic creation
# ---------------------------------------------------------------------------

class TestFlowInitE2E:
    """E2E tests for obs flow init."""

    def test_flow_init_creates_config(self, tmp_path):
        """flow init creates .flow/obsidian-sync.yml."""
        result = _run_obs(
            "flow", "init",
            "--vault-root", str(tmp_path),
            "--pairs", '[{"vault": "a", "repo": "b"}]',
            "--json",
            str(tmp_path),
        )
        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert data["status"] == "created"
        assert data["vault_root"] == str(tmp_path)
        assert len(data["pairs"]) == 1

        flow_file = tmp_path / ".flow" / "obsidian-sync.yml"
        assert flow_file.exists()

    def test_flow_init_writes_valid_yaml(self, tmp_path):
        """flow init writes valid YAML."""
        _run_obs(
            "flow", "init",
            "--vault-root", str(tmp_path),
            "--pairs", '[{"vault": "a", "repo": "b"}]',
            str(tmp_path),
        )
        flow_file = tmp_path / ".flow" / "obsidian-sync.yml"
        with open(flow_file) as f:
            data = yaml.safe_load(f)
        assert data["vault_root"] == str(tmp_path)
        assert len(data["pairs"]) == 1

    def test_flow_init_human_output(self, tmp_path):
        """flow init shows human-friendly output."""
        result = _run_obs(
            "flow", "init",
            "--vault-root", str(tmp_path),
            "--pairs", '[{"vault": "a", "repo": "b"}]',
            str(tmp_path),
        )
        assert result.returncode == 0
        assert "Created" in result.stdout
        assert "vault_root" in result.stdout

    def test_flow_init_multiple_pairs(self, tmp_path):
        """flow init handles multiple pairs."""
        pairs = [{"vault": "a", "repo": "b"}, {"vault": "c", "repo": "d"}]
        result = _run_obs(
            "flow", "init",
            "--vault-root", str(tmp_path),
            "--pairs", json.dumps(pairs),
            "--json",
            str(tmp_path),
        )
        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert len(data["pairs"]) == 2

    def test_flow_init_refuses_overwrite(self, tmp_path):
        """flow init refuses to overwrite existing config."""
        flow_dir = tmp_path / ".flow"
        flow_dir.mkdir()
        (flow_dir / "obsidian-sync.yml").write_text("existing")

        result = _run_obs(
            "flow", "init",
            "--vault-root", str(tmp_path),
            "--pairs", '[{"vault": "a", "repo": "b"}]',
            str(tmp_path),
        )
        assert result.returncode != 0
        output = result.stdout + result.stderr
        assert "already exists" in output

    def test_flow_init_force_overwrite(self, tmp_path):
        """flow init with --force overwrites existing config."""
        flow_dir = tmp_path / ".flow"
        flow_dir.mkdir()
        (flow_dir / "obsidian-sync.yml").write_text("existing")

        result = _run_obs(
            "flow", "init",
            "--vault-root", str(tmp_path),
            "--pairs", '[{"vault": "a", "repo": "b"}]',
            "--force",
            "--json",
            str(tmp_path),
        )
        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert data["status"] == "created"

    def test_flow_init_missing_vault_root(self, tmp_path):
        """flow init fails without --vault-root in non-interactive mode."""
        result = _run_obs(
            "flow", "init",
            "--pairs", '[{"vault": "a", "repo": "b"}]',
            str(tmp_path),
        )
        assert result.returncode != 0
        output = result.stdout + result.stderr
        assert "--vault-root required" in output

    def test_flow_init_missing_pairs(self, tmp_path):
        """flow init fails without --pairs in non-interactive mode."""
        result = _run_obs(
            "flow", "init",
            "--vault-root", str(tmp_path),
            str(tmp_path),
        )
        assert result.returncode != 0
        output = result.stdout + result.stderr
        assert "--pairs required" in output

    def test_flow_init_invalid_json(self, tmp_path):
        """flow init fails with invalid JSON."""
        result = _run_obs(
            "flow", "init",
            "--vault-root", str(tmp_path),
            "--pairs", "not json",
            str(tmp_path),
        )
        assert result.returncode != 0

    def test_flow_init_validation_error(self, tmp_path):
        """flow init fails validation for identity pairs."""
        result = _run_obs(
            "flow", "init",
            "--vault-root", str(tmp_path),
            "--pairs", '[{"vault": "a", "repo": "a"}]',
            str(tmp_path),
        )
        assert result.returncode != 0
        output = result.stdout + result.stderr
        assert "Validation failed" in output

    def test_flow_init_json_error_output(self, tmp_path):
        """flow init outputs errors as JSON."""
        result = _run_obs(
            "flow", "init",
            "--vault-root", str(tmp_path),
            "--pairs", "not json",
            "--json",
            str(tmp_path),
        )
        assert result.returncode != 0
        output = result.stdout + result.stderr
        data = json.loads(output)
        assert "error" in data

    def test_flow_init_no_subcommand(self, tmp_path):
        """flow without subcommand shows usage."""
        result = _run_obs("flow")
        assert result.returncode != 0


# ---------------------------------------------------------------------------
# flow init — with existing vaults
# ---------------------------------------------------------------------------

class TestFlowInitWithVaults:
    """E2E tests for flow init with real vault structures."""

    def test_flow_init_in_research_project(self, tmp_path):
        """flow init works in a research project structure."""
        # Create a minimal research project structure
        (tmp_path / "manuscript.qmd").write_text("---\ntitle: Test\n---")
        (tmp_path / "_manuscript").mkdir()
        (tmp_path / "code").mkdir()

        result = _run_obs(
            "flow", "init",
            "--vault-root", str(tmp_path),
            "--pairs", '[{"vault": "teaching", "repo": "docs"}]',
            "--json",
            str(tmp_path),
        )
        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert data["vault_root"] == str(tmp_path)

    def test_flow_init_creates_flow_dir(self, tmp_path):
        """flow init creates .flow/ directory if missing."""
        assert not (tmp_path / ".flow").exists()

        result = _run_obs(
            "flow", "init",
            "--vault-root", str(tmp_path),
            "--pairs", '[{"vault": "a", "repo": "b"}]',
            str(tmp_path),
        )
        assert result.returncode == 0
        assert (tmp_path / ".flow").is_dir()
        assert (tmp_path / ".flow" / "obsidian-sync.yml").exists()


# ---------------------------------------------------------------------------
# doctor --layer flow — integration with flow init
# ---------------------------------------------------------------------------

class TestDoctorFlowIntegration:
    """E2E tests for doctor --layer flow after flow init."""

    def test_doctor_flow_after_init(self, tmp_path):
        """doctor --layer flow passes after flow init."""
        # Create config
        _run_obs(
            "flow", "init",
            "--vault-root", str(tmp_path),
            "--pairs", '[{"vault": "a", "repo": "b"}]',
            str(tmp_path),
        )
        # Note: doctor needs a registered vault, so this just tests the CLI wiring
        result = _run_obs("doctor", "--layer", "flow")
        # Should not crash
        assert result.returncode in (0, 1)  # 1 = some warns, but no crash

    def test_doctor_flow_json_output(self, tmp_path):
        """doctor --layer flow --json outputs valid JSON."""
        result = _run_obs("doctor", "--layer", "flow", "--json")
        assert result.returncode in (0, 1)
        # Output should be valid JSON (may be empty if no vaults)
        output = result.stdout.strip()
        if output:
            data = json.loads(output)
            assert isinstance(data, list)
            # All results should have required fields
            for r in data:
                assert "id" in r
                assert "layer" in r
                assert "status" in r
