# Proposal: Claude Integration for obsidian-cli-ops
**Date**: 2026-06-15  
**Status**: Draft for review  
**Author**: Stat-Wise / Davood Tofighi  
**Context**: obsidian-cli-ops v3.2.2 (stable), v3.3.0 bridge+temporal in planning

---

## TL;DR

obsidian-cli-ops already has a working MCP server (`src/python/mcp_server.py`, 276 lines) and a `mcp_config.json`. The groundwork exists. The question is which surface to target and how to package it. **Recommended path: Option B (Cowork plugin with embedded MCP) + Option C (Claude Code plugin), implemented in that order.**

---

## Background

### What exists today

| Component | Location | Status |
|-----------|----------|--------|
| `mcp_server.py` | `src/python/mcp_server.py` | ✅ 276 lines, FastMCP-based, 7 tools |
| `mcp_config.json` | repo root | ✅ Points to `mcp_server.py` |
| `MCP_README.md` | repo root | ✅ Setup instructions for Claude Desktop |
| AI providers | `src/python/ai/` | ✅ 5 providers incl. anthropic-api, claude-cli |
| `--json` flag | all `obs ai` commands | ✅ Machine-readable output |
| 3-layer architecture | core/ | ✅ Interface-agnostic business logic |

### Current MCP tools (7)
- `search_notes(query, vault_id, limit)`
- `list_vaults()`
- `get_vault_stats(vault_id)`
- `discover_vaults(path)`
- `get_related_notes(note_title, vault_id)`
- `get_orphaned_notes(vault_id, limit)`
- `get_hub_notes(vault_id, limit)`

Missing (gaps vs. full `obs` CLI surface):
- `analyze_vault` (graph metrics)
- `health` (4-dimension scoring)
- `ai similar / duplicates / suggest-links / gaps / summarize / quality / tag-suggest`
- `ai refactor` (3-phase pipeline)
- `trends / stale / daily-digest` (v3.3.0 planned)

---

## Integration Options

### Option A — Activate Existing Claude Desktop MCP (Minimal Effort)

**What it is**: Wire the already-built `mcp_server.py` into Claude Desktop's `claude_desktop_config.json`. No new code, just setup + documentation.

**Implementation** (1–2 hours):
```json
// ~/Library/Application Support/Claude/claude_desktop_config.json
{
  "mcpServers": {
    "obsidian-ops": {
      "command": "/opt/homebrew/bin/python3",
      "args": ["/Users/dt/projects/dev-tools/obsidian-cli-ops/src/python/mcp_server.py"],
      "env": {}
    }
  }
}
```
Then verify `mcp_server.py` runs cleanly with the isolated venv python (check `_obs_resolve_python` logic — the MCP server currently calls bare `python3`, which risks the ambient-interpreter bug fixed in v3.2.1).

**Gaps to close**:
- Fix interpreter path in `mcp_server.py` (use `OBS_PYTHON` resolution or hardcode Homebrew venv path)
- Expand tool set to match full CLI surface (7 → ~15 tools)
- Add `--json` output integration for `obs ai` subcommands

**Pros**:
- Zero architecture work — code already exists
- Immediate value in Claude Desktop chat sessions
- Unlocks vault search/analysis in any Claude Desktop conversation

**Cons**:
- Claude Desktop only (not Cowork, not Claude Code)
- Manual config per machine — not portable
- No versioning, no install workflow
- Fragile: if venv path changes, breaks silently
- Not shareable with others

**Effort**: Low (2–4h)  
**Value**: Medium — personal productivity win, but limited reach

---

### Option B — Cowork Plugin (MCP + Skills)

**What it is**: A `.plugin` bundle that ships the MCP server + skills for Cowork mode. Installable via Cowork's plugin system. Users get natural-language access to vault operations inside Cowork sessions.

**Architecture**:
```
obsidian-cli-ops-plugin/
├── .claude-plugin/
│   └── plugin.json          # name, description, version, author
├── .mcp.json                # MCP server config (points to mcp_server.py)
├── skills/
│   ├── vault-search/
│   │   └── SKILL.md         # "Search my Obsidian vaults for..."
│   ├── vault-health/
│   │   └── SKILL.md         # "Check vault health, orphans, hubs"
│   ├── vault-analyze/
│   │   └── SKILL.md         # "Analyze graph structure"
│   └── vault-ai/
│       └── SKILL.md         # "Find duplicates, suggest links, summarize"
└── README.md
```

**`.mcp.json`** (plugin-scoped MCP — loaded only when plugin active):
```json
{
  "mcpServers": {
    "obsidian-ops": {
      "command": "python3",
      "args": ["${PLUGIN_DIR}/../../../src/python/mcp_server.py"],
      "env": {}
    }
  }
}
```
> **Critical open question**: Does Cowork's `.mcp.json` support path variables or relative paths pointing outside the plugin dir? If not, must use absolute path (non-portable) or a wrapper script in `bin/` that resolves the path dynamically.

**Alternative MCP wiring** (more portable): include a thin `bin/obs-mcp` wrapper script:
```bash
#!/usr/bin/env bash
# Resolve obs python and launch MCP server
OBS_PYTHON=$(/opt/homebrew/bin/python3 -c "import sys; print(sys.executable)")
exec "$OBS_PYTHON" "$(obs --print-python-path)/mcp_server.py"
```

**Skills approach**: Skills call MCP tools directly. Cowork skill invocations become natural:
- `/obsidian-cli-ops:vault-search causal inference`
- `/obsidian-cli-ops:vault-health my-research-vault`

**Pros**:
- Full Cowork integration — skills + MCP in one bundle
- Works with your existing project workflow
- Versioned and installable (`.plugin` archive)
- MCP tools auto-available in Cowork sessions
- Skills provide guided UX ("vault-health" is more discoverable than knowing tool names)
- Natural extension of the CLAUDE.md workflow (`hub`, `status`, etc.)

**Cons**:
- Cowork plugin `.mcp.json` path resolution is **untested** — needs verification
- The MCP server needs the obs venv; packaging must solve the interpreter dependency
- Plugin bundles MCP config but not the Python venv — user must have `obs` installed
- Skills in a Cowork plugin cannot easily call `obs` CLI commands directly (no shell access in skills)
- Maintenance: plugin version must track mcp_server.py API changes

**Effort**: Medium (1–2 days)  
**Value**: High — integrates into your primary AI workspace

---

### Option C — Claude Code Plugin (Standalone)

**What it is**: A plugin for Claude Code (the CLI) that ships skills + an MCP server, installable via `claude plugin install`. Users interact via `/obsidian:vault-search` in Claude Code sessions.

**Architecture** (same structure as Option B but Claude Code-targeted):
```
obsidian-claude-plugin/
├── .claude-plugin/
│   └── plugin.json
├── .mcp.json
├── bin/
│   └── obs-mcp-server      # Executable wrapper that finds and launches mcp_server.py
├── skills/
│   ├── vault-ops/
│   │   └── SKILL.md
│   └── vault-ai/
│       └── SKILL.md
└── hooks/
    └── hooks.json           # Optional: PostToolUse hook to auto-scan after vault writes
```

**Key difference from Option B**: Claude Code plugins can include `bin/` executables added to `PATH` and can run hooks (event handlers). This enables:

```json
// hooks/hooks.json — auto-refresh vault DB after Claude modifies .md files
{
  "hooks": {
    "PostToolUse": [{
      "matcher": "Write|Edit",
      "hooks": [{
        "type": "command",
        "command": "jq -r '.tool_input.file_path' | grep -q '\\.md$' && obs stats $(dirname $VAULT_PATH) --quiet"
      }]
    }]
  }
}
```

**Distributable**: Can be submitted to `claude-community` marketplace after `claude plugin validate`.

**Pros**:
- Works in Claude Code sessions (your primary coding environment)
- `bin/` solves the interpreter-resolution problem cleanly
- Hooks enable reactive vault updates (auto-rescan after note edits)
- Shareable via marketplace (rmediation users, stats colleagues)
- `claude plugin validate` catches structural issues before distribution
- Natural fit with v3.3.0 `obs apply` (bridge write path) — hook can call `obs apply` after AI refactor plans

**Cons**:
- Claude Code plugin MCP support is newer — `.mcp.json` in plugins may have edge cases
- Skills require Claude Code to be running (not useful in Claude Desktop chat)
- `bin/obs-mcp-server` must handle venv resolution without assuming Homebrew path
- Hooks run in Claude Code's sandboxed bash — vault path must be accessible

**Effort**: Medium (1–2 days, shares ~80% code with Option B)  
**Value**: High for Claude Code workflows; shareable

---

### Option D — Full Native MCP Connector (Packaged)

**What it is**: A standalone Python package (`obsidian-ops-mcp`) published to PyPI, designed to be used as a proper MCP connector — installable via `uvx obsidian-ops-mcp` or `pip install obsidian-ops-mcp`. Referenced in any Claude config (Desktop, Code, Cowork) via standard MCP server config.

**Architecture**:
```
obsidian-ops-mcp/           (separate repo or src/ subpackage)
├── pyproject.toml           # name = obsidian-ops-mcp, entry_point = obs-mcp
├── src/
│   └── obsidian_ops_mcp/
│       ├── __init__.py
│       ├── server.py        # Refactored from mcp_server.py
│       └── tools/           # Modular tool definitions
└── README.md
```

Config in any Claude product:
```json
{
  "mcpServers": {
    "obsidian-ops": {
      "command": "uvx",
      "args": ["obsidian-ops-mcp"]
    }
  }
}
```

**Pros**:
- Truly portable — works in Desktop, Code, Cowork identically
- `uvx` handles venv/interpreter automatically (no path fragility)
- Versioned releases with PyPI semantics
- Community-shareable: `pip install obsidian-ops-mcp`
- Clean separation: obsidian-cli-ops (the CLI tool) vs. obsidian-ops-mcp (the AI connector)
- Aligns with how production MCP servers are packaged (e.g., `mcp-server-sqlite`, `mcp-server-filesystem`)

**Cons**:
- Separate repo/package to maintain
- Requires PyPI publishing infrastructure
- obsidian-ops core logic becomes a dependency (or must be duplicated)
- Most work of any option (3–5 days to do properly)
- Overkill for personal use; justified only if distributing publicly

**Effort**: High (3–5 days)  
**Value**: Highest reach; only needed if publishing publicly

---

## Comparison Matrix

| Criterion | A (Claude Desktop) | B (Cowork Plugin) | C (Claude Code Plugin) | D (PyPI Package) |
|-----------|-------------------|-------------------|------------------------|------------------|
| **Effort** | Low (2–4h) | Medium (1–2d) | Medium (1–2d) | High (3–5d) |
| **Works in Cowork** | ❌ | ✅ | ❌ | ✅ |
| **Works in Claude Code** | ❌ | ❌ | ✅ | ✅ |
| **Works in Claude Desktop** | ✅ | ❌ | ❌ | ✅ |
| **Shareable** | ❌ | 🟡 (manual) | ✅ (marketplace) | ✅ (PyPI) |
| **Versioned install** | ❌ | 🟡 | ✅ | ✅ |
| **Hooks/reactive** | ❌ | ❌ | ✅ | ✅ |
| **Venv handled** | ❌ (manual) | 🟡 (wrapper) | ✅ (bin/) | ✅ (uvx) |
| **v3.3.0 bridge fit** | 🟡 | 🟡 | ✅ | ✅ |
| **Maintenance burden** | Low | Medium | Medium | High |

---

## Recommendation

### Phase 1 (this week, ~4h): Option A — Activate what exists

- Fix `mcp_server.py` to use obs venv python (not ambient `python3`)
- Wire into `claude_desktop_config.json`  
- Test all 7 tools from Claude Desktop chat  
- Expand to ~12 tools (add `analyze`, `health`, AI subcommands via `--json` subprocess calls)

This gives immediate value and surfaces real gaps.

### Phase 2 (v3.3.0 window, 1–2 days): Option B — Cowork Plugin

- Build the `.plugin` bundle around the working `mcp_server.py`
- Add 4 skills (vault-search, vault-health, vault-analyze, vault-ai)
- Test `.mcp.json` path resolution in Cowork
- Store in `~/projects/dev-tools/obsidian-cli-ops-plugin/` (own git repo)

### Phase 3 (post-v3.3.0, 1–2 days): Option C — Claude Code Plugin

- Adapt the Cowork plugin for Claude Code (add `bin/`, hooks)
- Wire the `obs apply` bridge (v3.3.0 Theme A) as a PostToolUse hook
- Submit to `claude-community` marketplace

**Skip Option D** unless you want to publish this publicly for the Obsidian/stats community. Worth revisiting post-v3.3.0.

---

## Open Questions / Risks

1. **Interpreter resolution in plugin MCP**: Does `.mcp.json` in a Cowork/Claude Code plugin support `${PLUGIN_DIR}` or must it use absolute paths? → Test with a minimal plugin before committing.

2. **mcp_server.py venv dependency**: The server imports from `db_manager`, `core/`, `ai/` — requires obs's isolated venv. If launched outside that venv (e.g., by Claude Desktop's MCP runner), imports fail. Mitigation: use a `bin/obs-mcp-server` wrapper that activates the venv.

3. **Tool coverage gap**: Current 7 tools cover vault metadata ops. The AI features (`duplicates`, `suggest-links`, `quality`, `summarize`) use heavy Python deps (numpy, embeddings). Including these in MCP means Claude can invoke them, but first invocation may take 30–60s (model load). Need to surface this latency in tool docstrings.

4. **v3.3.0 bridge dependency**: `obs apply` writes to vault files via the official Obsidian CLI. If the Obsidian app isn't running, bridge tools silently degrade. MCP tools that wrap bridge features need graceful fallback messaging.

5. **Cowork plugin format stability**: Plugin spec is in beta (v1.1.0 as of June 2026). Breaking changes possible. Mitigate by pinning `.claude-plugin/plugin.json` format version and testing on each Cowork update.

---

## Implementation Notes

### Fixing the venv issue (prerequisite for all options)

```python
# At top of mcp_server.py — replace bare imports with venv-aware bootstrap
import subprocess, sys
from pathlib import Path

def _find_obs_python():
    """Find the obs-managed Python interpreter."""
    candidates = [
        Path.home() / ".local/share/obs/venv/bin/python3",
        Path("/opt/homebrew/libexec/obs/venv/bin/python3"),
    ]
    for p in candidates:
        if p.exists():
            return str(p)
    return sys.executable  # fallback with warning

# If not running in correct interpreter, re-exec
_obs_python = _find_obs_python()
if sys.executable != _obs_python:
    import os
    os.execv(_obs_python, [_obs_python] + sys.argv)
```

### Skeleton for `bin/obs-mcp-server` wrapper

```bash
#!/usr/bin/env bash
# obs-mcp-server — launch the MCP server in the correct venv
set -euo pipefail

OBS_VENV="${OBS_PYTHON:-}"
if [ -z "$OBS_VENV" ]; then
    for candidate in \
        "$HOME/.local/share/obs/venv/bin/python3" \
        "/opt/homebrew/libexec/obs/venv/bin/python3"
    do
        [ -x "$candidate" ] && OBS_VENV="$candidate" && break
    done
fi

OBS_VENV="${OBS_VENV:-python3}"
OBS_SRC="$(obs --print-src-path 2>/dev/null || echo "$(dirname "$0")/../../../src/python")"

exec "$OBS_VENV" "$OBS_SRC/mcp_server.py" "$@"
```

---

## Related Files

- `src/python/mcp_server.py` — existing MCP server (7 tools)
- `mcp_config.json` — existing Claude Desktop config stub
- `MCP_README.md` — existing setup docs
- `docs/specs/SPEC-v3.3.0-bridge-temporal-2026-06-04.md` — v3.3.0 context
- `IDEAS.md` — feature backlog
- `.STATUS` — current project state
