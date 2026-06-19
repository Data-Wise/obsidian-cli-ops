# SPEC: v3.5.0 — obs doctor (Setup Diagnostics + MCP Health Check)

**Status:** draft  
**Created:** 2026-06-19  
**Type:** feature  
**From brainstorm:** `BRAINSTORM-obs-doctor-2026-06-19.md`  
**Trigger:** iCloud Drive write hangs (4-min MCP timeout, zero actionable error) exposed that there is no command to diagnose why MCP tools fail or why setup is broken. Users need a single `obs doctor` command — like `brew doctor` or `gh auth status` — to get a layered pass/warn/fail report with actionable fix hints.

---

## Overview

`obs doctor` runs a battery of self-diagnostics across five layers (Python runtime → database → vault health → MCP server → iCloud write path) and prints a Rich-formatted report with ✅/⚠️/❌ per check and a one-line fix hint for every failure. Exit code 0 = all pass, 1 = any failures, 2 = any errors (scriptable).

A companion MCP tool `diagnose` exposes the same checks as a JSON payload so Claude Desktop can self-diagnose without the user opening a terminal.

---

## Primary User Story

> As an `obs` user whose MCP writes are failing, I run `obs doctor` and immediately see which layer is broken (iCloud not materialized, MCP config missing, venv wrong) and the exact command to fix it — without having to read docs or file a bug.

**Acceptance criteria:**
- `obs doctor` exits 0 when all checks pass, 1 when any check fails.
- Every failure line includes a one-line `→ Fix:` hint.
- `obs doctor --json` emits a valid JSON array of check results (scriptable).
- `obs doctor` completes in < 10 s on a healthy install (write latency check has a 5 s cap).
- MCP tool `obsidian-ops:diagnose` returns the same JSON payload.

---

## Secondary User Stories

- As a developer setting up obs for the first time, `obs ai setup` calls `obs doctor` at the end and surfaces any remaining issues.
- As a CI script, `obs doctor --json | jq '.[] | select(.status == "fail")'` fails the build when the install is broken.
- As a user who just enabled iCloud Optimize Mac Storage, `obs doctor` detects offloaded placeholders before any write is attempted.

---

## Check Registry

Each check is a `DoctorCheck` dataclass: `(id, layer, label, status, message, fix_hint)`.

### Layer 1 — Python runtime

| ID | Label | Pass | Warn | Fail |
|----|-------|------|------|------|
| `py-version` | Python version | ≥ 3.10 | 3.9.x | < 3.9 |
| `py-resolver` | Interpreter source | venv or `$OBS_PYTHON` | ambient w/ deps present | ambient, deps missing |
| `py-imports` | Core imports | all 6 importable | — | any of: rich, networkx, sqlite3, mcp |

Resolver tiers (from `_obs_resolve_python`): `$OBS_PYTHON` → install.sh user venv → Homebrew libexec venv → ambient (warn).

### Layer 2 — Database

| ID | Label | Pass | Warn | Fail |
|----|-------|------|------|------|
| `db-exists` | DB file exists | ✅ | — | ❌ → `obs db init` |
| `db-schema` | Schema version | current | 1 version behind | > 1 behind or corrupt |
| `db-query` | Can query vaults | SELECT ok | — | locked / corrupt |
| `db-vaults` | Vault count | ≥ 1 | 0 registered | — |

### Layer 3 — Vault health (per registered vault)

| ID | Label | Pass | Warn | Fail |
|----|-------|------|------|------|
| `vault-path` | Path accessible | ✅ | iCloud path (note) | path missing |
| `vault-dataless` | iCloud materialized | no SF_DATALESS flag | some placeholders | root is dataless |
| `vault-stale` | Last scanned | < 7 days | 7–30 days | > 30 days or never |
| `vault-fts` | Search index | FTS row count > 0 | — | 0 rows or missing |
| `vault-links` | Link graph | links > 0 | 0 links | — |

Stale thresholds are configurable via `~/.config/obs/config.yaml` (`doctor.warn_days`, `doctor.fail_days`; defaults 7 / 30).

### Layer 4 — MCP server

| ID | Label | Pass | Warn | Fail |
|----|-------|------|------|------|
| `mcp-config` | Claude Desktop config found | file exists | — | not found |
| `mcp-entry` | obsidian-ops entry | present + path valid | present, path wrong | absent |
| `mcp-server` | mcp_server.py importable | imports clean | — | ImportError |
| `mcp-fastmcp` | FastMCP available | `mcp` pkg in venv | — | missing |

Claude Desktop config path: `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS). Fall back to `~/.config/claude/claude_desktop_config.json` (Linux).

### Layer 5 — iCloud write path

| ID | Label | Pass | Warn | Fail |
|----|-------|------|------|------|
| `icloud-detect` | Vault on iCloud Drive | — (non-iCloud is fine) | detected | — |
| `icloud-write` | Write latency | < 1 s | 1–5 s | > 5 s or error |
| `icloud-offload` | Optimize Mac Storage | off or N/A | on (risk) | all vault files offloaded |

Write latency test: write a 1-byte `.obs-doctor-probe` temp file into the vault root, measure wall time, delete it. Uses `_fs_op` with a 5 s timeout (not the full 30 s write timeout) so the check itself never hangs.

---

## Architecture

Three-layer per project conventions, plus a new MCP tool.

### `src/python/core/doctor.py` (new)

```python
from dataclasses import dataclass
from typing import Literal

Status = Literal["pass", "warn", "fail", "skip", "error"]

@dataclass
class DoctorResult:
    id: str
    layer: str
    label: str
    status: Status
    message: str
    fix_hint: str = ""

def run_checks(vault_id: str | None = None) -> list[DoctorResult]:
    """Run all checks; return results in layer order."""
    results = []
    results += _check_python()
    results += _check_database()
    results += _check_vaults(vault_id)
    results += _check_mcp()
    results += _check_icloud()
    return results
```

Each `_check_*` function returns `list[DoctorResult]`. Checks are independent — a failure in layer 1 does not skip later layers (but some checks short-circuit gracefully, e.g. if DB is corrupt skip per-vault checks).

### `src/python/obs_cli.py` (extend)

Add `doctor` subparser:

```
obs_cli.py doctor [--json] [--fix] [--vault VAULT_ID] [--layers LAYER,...]
```

- `--json`: emit `list[DoctorResult]` as JSON, exit 0/1/2
- `--fix`: after printing report, attempt safe auto-remediations (see §Auto-fix)
- `--vault`: scope vault checks to one vault
- `--layers`: comma-separated subset (e.g. `mcp,icloud`)

### `src/obs.zsh` (extend)

```zsh
obs_doctor() {
    local python_cli
    python_cli=$(_get_python_cli) || return 1
    "$(_obs_resolve_python)" "$python_cli" doctor "$@"
}
```

Add `doctor` to the dispatcher `case` and to `obs_help()`.

### `src/python/mcp_server.py` (extend)

New MCP tool `diagnose`:

```python
@mcp.tool()
def diagnose(vault_id: str = "") -> str:
    """
    Run obs doctor checks and return a JSON health report.
    Use this when MCP tools are failing or setup seems broken.
    """
    from core.doctor import run_checks
    import json
    results = run_checks(vault_id or None)
    return json.dumps([r.__dict__ for r in results], indent=2)
```

---

## Auto-fix (`--fix`)

Only safe, non-destructive remediations run automatically:

| Failure | Auto-fix action |
|---------|----------------|
| `db-exists` fails | `obs db init` |
| `vault-stale` warns/fails | `obs scan <vault_id>` (offers prompt if multiple vaults) |
| `vault-links` warns | `obs analyze <vault_id>` |
| `mcp-entry` missing | Print exact JSON snippet to add to `claude_desktop_config.json`; do NOT write the file (user must restart Claude Desktop) |
| `icloud-write` slow | Print Finder + `brctl download` instructions; cannot auto-fix |

Anything that mutates the Claude Desktop config or triggers iCloud download is print-only — the user executes.

---

## UI/UX Specification

### Terminal output (Rich)

```
obs doctor
────────────────────────────────────────────────────
  Python runtime
  ✅  Python 3.14.6 (/opt/homebrew/.../python3.14)
  ✅  Resolver: user venv (~/.local/share/obs/venv)
  ✅  Core imports: rich, networkx, sqlite3, mcp

  Database
  ✅  vault.db found, schema v7 (current)
  ✅  2 vaults registered

  Vault: Documents (a812d844)
  ⚠️  iCloud path — writes may be slow
  ⚠️  Last scanned 113 days ago
       → Fix: obs scan a812d844
  ⚠️  Link graph empty (0 links)
       → Fix: obs analyze a812d844
  ✅  Search index: 3016 rows

  Vault: Knowledge_Base (60a2c59d)
  ✅  Path accessible
  ✅  Last scanned 113 days ago (warn threshold)
  ✅  Search index: 2374 rows

  MCP server
  ✅  claude_desktop_config.json found
  ✅  obsidian-ops entry: path valid
  ✅  mcp_server.py imports clean
  ⚠️  Write latency to iCloud vault: 3.2s
       → Fix: Finder → right-click vault folder → Download Now
       → Or: brctl download "<vault path>"

────────────────────────────────────────────────────
  4 warnings, 0 failures  (exit 0)
  Run `obs doctor --fix` to attempt auto-remediation
```

Rules:
- ✅ green, ⚠️ yellow, ❌ red (Rich color codes)
- Fix hints indented 7 spaces (aligns under message)
- Layer headers in bold
- Summary line always last; exit code shown parenthetically
- `--json` suppresses all Rich output; raw JSON only

### JSON output (`--json`)

```json
[
  {
    "id": "py-version",
    "layer": "python",
    "label": "Python version",
    "status": "pass",
    "message": "Python 3.14.6",
    "fix_hint": ""
  },
  {
    "id": "vault-stale",
    "layer": "vault",
    "label": "Last scanned",
    "status": "warn",
    "message": "Documents: 113 days since last scan",
    "fix_hint": "obs scan a812d844"
  }
]
```

---

## Dependencies

No new dependencies. Uses:
- `rich` (already required) — terminal formatting
- `sqlite3` (stdlib) — DB checks
- `os.stat` + `stat.SF_DATALESS` (stdlib, macOS-only; guarded with `hasattr`) — iCloud detection
- `concurrent.futures.ThreadPoolExecutor` (stdlib) — write latency test via `_fs_op`
- `json` (stdlib) — JSON output
- `pathlib` (stdlib) — path checks
- `time` (stdlib) — latency measurement

---

## Open Questions

1. **Linux support for iCloud checks**: `stat.SF_DATALESS` is macOS-only. On Linux, iCloud layer should `skip` with message "iCloud checks not applicable on Linux". Use `platform.system() == "Darwin"` guard.
2. **Claude Desktop config path on Windows**: Not in current scope (obs is macOS-first), but the config path should be behind a platform helper for future portability.
3. **`--fix` for stale vaults**: Should auto-scan be gated behind a confirmation prompt when the vault is iCloud-backed? (Risk: scan itself may be slow if files are offloaded.) Lean yes — add `--yes` to bypass prompt.

---

## Review Checklist

- [ ] `DoctorResult` dataclass is JSON-serializable (`__dict__` or `dataclasses.asdict`)
- [ ] All five layers tested (unit tests for each `_check_*` function)
- [ ] `--json` output is valid JSON (schema stable for MCP `diagnose` consumers)
- [ ] Exit codes: 0 = all pass/warn, 1 = any fail, 2 = unexpected error
- [ ] iCloud write latency test uses `_fs_op` with 5 s timeout (not 30 s)
- [ ] SF_DATALESS flag guarded with `hasattr(st, 'st_flags')` for Linux
- [ ] MCP `diagnose` tool returns the same JSON as `--json`
- [ ] `obs doctor` added to `obs help --all`
- [ ] `obs doctor` added to man page
- [ ] Version bump to 3.5.0 (new command = minor bump)
- [ ] CLAUDE.md command count updated (24 → 25 obs commands)
- [ ] `.STATUS` updated

---

## Implementation Notes

- `_check_icloud()` must not block: wrap the write latency probe in `_fs_op(fn, timeout=5)` — if it times out, status = `fail` with message "write timed out after 5s (iCloud placeholder not materialized)".
- `_check_mcp()` is read-only: parse JSON config, check key existence and path validity. Do not attempt to start or connect to the MCP server process.
- `_check_vaults()` short-circuits gracefully: if `db-query` fails, skip per-vault checks with `status="skip"` and `message="skipped: DB unavailable"`.
- FTS check: `SELECT COUNT(*) FROM notes_fts` — guard with `try/except sqlite3.OperationalError` (table may not exist on older installs).
- The Rich console used in `doctor.py` should be the same singleton from `obs_cli.py` (pass it in or import from a shared module) to respect `--no-color` / piped output.

---

## History

| Date | Author | Note |
|------|--------|------|
| 2026-06-19 | dt | Initial draft from brainstorm `BRAINSTORM-obs-doctor-2026-06-19.md` |
