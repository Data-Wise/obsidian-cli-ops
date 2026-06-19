# BRAINSTORM: obs doctor — MCP health check + setup diagnostics

**Date:** 2026-06-19  
**Mode:** feature | **Depth:** default  
**Status:** brainstorm → ready for spec

---

## The Core Idea

`obs doctor` is a self-diagnostic command that runs a battery of checks and prints a
pass/warn/fail report — same pattern as `brew doctor`, `gh auth status`, `cargo doctor`.
One command to answer "why isn't my MCP working?"

---

## Check Categories (MVP)

### Layer 1 — Python runtime
| Check | Pass | Warn | Fail |
|-------|------|------|------|
| Python version | ≥ 3.9 | 3.9 exactly | < 3.9 |
| Resolver tier | `$OBS_PYTHON` or venv | ambient w/ deps | ambient w/o deps |
| Core imports | all 6 importable | — | any missing |

### Layer 2 — Database
| Check | Pass | Warn | Fail |
|-------|------|------|------|
| DB file exists | ✅ | — | ❌ → `obs db init` |
| Schema version | current | behind | corrupt |
| Can query | vaults table responds | — | locked/corrupt |
| Vault count | ≥ 1 registered | 0 (no vaults) | — |

### Layer 3 — Vault health
| Check | Pass | Warn | Fail |
|-------|------|------|------|
| Vault path exists | accessible | iCloud (warn) | missing |
| iCloud materialized | local files | some dataless | all dataless |
| Last scanned | < 7 days | 7–30 days | > 30 days or never |
| Search index | FTS populated | empty | missing table |
| Link graph | links > 0 | 0 links | — |

### Layer 4 — MCP server
| Check | Pass | Warn | Fail |
|-------|------|------|------|
| Config file found | claude_desktop_config.json found | — | not found |
| `obsidian-ops` entry | present + correct path | present, wrong path | absent |
| MCP server importable | mcp_server.py importable | — | import error |
| FastMCP importable | `mcp` package present in venv | — | missing |
| Write test | temp file write < 1s | write slow (> 5s) | timeout or error |

### Layer 5 — iCloud write path
| Check | Pass | Warn | Fail |
|-------|------|------|------|
| Vault is iCloud path | — | warn: writes may be slow | — |
| Test write latency | < 1s | 1–5s | > 5s or hung |
| SF_DATALESS on root | — | some placeholders | all offloaded |

---

## Output Format

```
obs doctor
──────────────────────────────────────────────────
  Python runtime
  ✅  Python 3.14.6 at /opt/homebrew/opt/python/bin/python3
  ✅  Resolver: user venv (~/.local/share/obs/venv)
  ✅  Core imports: rich, networkx, sqlite3, yaml, requests, mcp

  Database
  ✅  DB at ~/.config/obs/vault.db (schema v7)
  ✅  2 vaults registered

  Vaults
  ⚠️   Documents (a812d844): iCloud path — 3016 notes, last scanned 113 days ago
        → Run: obs scan a812d844
  ⚠️   Documents (a812d844): 0 links in graph
        → Run: obs analyze a812d844
  ✅  Knowledge_Base (60a2c59d): accessible

  MCP server
  ✅  claude_desktop_config.json found
  ✅  obsidian-ops entry present
  ✅  mcp_server.py importable
  ⚠️   Write latency to iCloud vault: 3.2s (slow — iCloud not fully materialized)
        → In Finder: right-click vault → Download Now

──────────────────────────────────────────────────
  2 warnings, 0 failures
  Run `obs doctor --fix` to auto-fix what's fixable
```

Exit codes: 0 = all pass, 1 = any failures (scriptable in CI/setup scripts).

---

## Quick Wins (< 30 min each)

1. **Skeleton `obs doctor` ZSH + Python stub** — wire up three-layer scaffold; exits 0/1 for scripting
2. **Python + import checks** — cheapest, highest-value; catches venv resolver issues immediately
3. **DB health check** — `SELECT 1 FROM vaults` covers 80% of "obs isn't finding my vault" bugs
4. **MCP config check** — parse `~/Library/Application Support/Claude/claude_desktop_config.json`, verify `obsidian-ops` key + path
5. **iCloud write latency test** — write 1-byte temp file, measure elapsed, delete; directly diagnoses the iCloud hang bug

## Medium Effort (1–2 hrs)

- **`--fix` flag** — auto-remediate safe issues: `obs db init` for missing DB, `obs scan <id>` for stale vaults
- **`--json` output** — machine-readable for CI and the future MCP `diagnose` tool
- **FTS index probe** — `SELECT COUNT(*) FROM notes_fts` to detect empty search index (explains "search returns nothing")
- **Stale vault warning threshold** — configurable (default: warn at 7 days, fail at 30)

## Long-term (future sessions)

- **MCP `diagnose` tool** — expose `doctor` as MCP tool so Claude Desktop self-diagnoses: `obsidian-ops:diagnose` → JSON report
- **`obs doctor --watch`** — monitor and alert on vault drift / DB corruption
- **Setup wizard integration** — `obs ai setup` calls `obs doctor` at the end to confirm wiring

---

## Recommended Path

→ **Start with MCP config check + iCloud write latency test** — these directly diagnose the
issue that prompted this feature (iCloud write hangs + MCP not registered). < 30 min combined.

Implementation order:
1. `src/python/core/doctor.py` — `run_checks() → list[DoctorResult]`
2. `src/python/obs_cli.py` — `doctor` subcommand, `--json` flag
3. `src/obs.zsh` — `obs_doctor()` wrapper
4. MCP `diagnose` tool (medium effort, separate increment)
