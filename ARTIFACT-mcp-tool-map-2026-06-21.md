# Phase-0 Artifact: MCP Tool-Name Map (§5.4)

**Status:** Ratified 2026-06-21 | **RFC:** SPEC-merge-nexus-cli-v2-2026-06-21.md §5.4  
**Sources:** nexus-mcp (TS, 15 tools) + obsidian-ops (Python, 25 tools)

---

## 1. Summary

| Disposition | Count |
|-------------|-------|
| Map to existing obs tool (no new Python needed) | 2 |
| New Python tool (Phase 2) | 1 |
| New Python tool (Phase 4 – research domain) | 12 |
| **Total nexus tools to absorb** | **15** |

All 15 nexus `nexus_*` TypeScript tools will be superseded. The TS MCP server (`mcp-servers/nexus/src/index.ts`) is retired at Phase 4 completion.

---

## 2. Full Mapping Table

### Phase 1 — Vault Tools (already covered by obs MCP)

These nexus tools have direct obs equivalents. Claude's MCP config entry for `nexus` can be updated to `obsidian-ops` immediately after Phase 1 ships; these two tools require zero new Python.

| nexus tool (TS) | obs tool (Python) | Notes |
|-----------------|-------------------|-------|
| `nexus_vault_search` | `search_notes` | obs adds `vault_id` param; nexus used vault path. Wire via `vault_id` lookup. |
| `nexus_vault_read` | `read_note` | Direct 1:1 map. nexus used relative vault path; obs uses `note_id` (path from DB). |

### Phase 2 — Unified Search

One nexus tool has no single obs equivalent — it crosses vault + Zotero + PDF. Implement after Phase 4 backends exist.

| nexus tool (TS) | new obs tool | Notes |
|-----------------|-------------|-------|
| `nexus_unified_search` | `unified_search` | Fans out to `search_notes` + `zotero_search` + `pdf_search`, merges ranked results. Hold until Phase 4 backends are in place. |

### Phase 4 — Research Domain (Zotero + PDF + Teaching + Writing)

All 12 tools are net-new Python. They are gated on D1=Option A (full absorption). Tool names drop the `nexus_` prefix; signatures are preserved from nexus TS unless noted.

**Zotero sub-domain** (`obs research zotero …` CLI surface):

| nexus tool (TS) | new obs tool | Signature delta |
|-----------------|-------------|-----------------|
| `nexus_zotero_search` | `zotero_search` | `query: str, limit: int = 10` — unchanged |
| `nexus_zotero_get` | `zotero_get` | `item_key: str` — unchanged |
| `nexus_zotero_cite` | `zotero_cite` | `item_key: str, format: str = "apa"` — unchanged |
| `nexus_zotero_recent` | `zotero_recent` | `limit: int = 10` — unchanged |

**PDF sub-domain** (`obs research pdf …`):

| nexus tool (TS) | new obs tool | Signature delta |
|-----------------|-------------|-----------------|
| `nexus_pdf_search` | `pdf_search` | `query: str, directories: list[str] \| None = None` — `directories` defaults to `config.research.pdf.directories` |

**Teaching sub-domain** (`obs research teach …`):

| nexus tool (TS) | new obs tool | Signature delta |
|-----------------|-------------|-----------------|
| `nexus_course_list` | `course_list` | No params — unchanged |
| `nexus_course_show` | `course_show` | `name: str` — unchanged |
| `nexus_course_lectures` | `course_lectures` | `name: str` — unchanged |

**Writing sub-domain** (`obs research write …`):

| nexus tool (TS) | new obs tool | Signature delta |
|-----------------|-------------|-----------------|
| `nexus_manuscript_list` | `manuscript_list` | No params — unchanged |
| `nexus_manuscript_show` | `manuscript_show` | `name: str` — unchanged |
| `nexus_manuscript_stats` | `manuscript_stats` | `name: str` — unchanged |

**Bib check** (straddles research + writing):

| nexus tool (TS) | new obs tool | Signature delta |
|-----------------|-------------|-----------------|
| `nexus_bib_check` | `bib_check` | `vault_id: str \| None = None` — adds optional vault scope |

---

## 3. Existing obs MCP Tools (unchanged, shown for completeness)

The 25 existing `obsidian-ops` tools are unaffected by the merge. Listed here so the full post-merge tool inventory is traceable in one place.

**Vault ops:** `list_vaults`, `discover_vaults`, `get_vault_stats`, `rescan_vault`  
**Note CRUD:** `list_notes`, `read_note`, `write_note`, `create_note`, `append_to_note`, `rename_note`, `delete_note`  
**Search/graph:** `search_notes`, `find_similar_notes`, `get_hub_notes`, `get_orphaned_notes`, `get_broken_links`, `get_note_links`, `analyze_vault`  
**Health/trends:** `get_vault_health`, `get_trends`, `get_stale_notes`, `get_daily_digest`  
**AI + util:** `run_obs_ai`, `get_bridge_status`, `diagnose`

**Post-merge total (Phase 4 complete):** 25 existing + 13 new = **38 tools**

---

## 4. Deprecation Shim (nexus-mcp TS server)

The nexus TS MCP server (`mcp-servers/nexus/src/index.ts`) stays **operational** until every tool it exposes has a Python equivalent and the MCP config in `~/.claude/claude_desktop_config.json` (and any MCP client configs) has been updated.

Deprecation timeline:
- **Phase 1 complete**: update MCP config to replace `nexus` entry with `obsidian-ops` entry (vault search + read now covered)
- **Phase 4 complete**: shut down nexus TS server; all 15 tools covered
- **After Phase 4**: delete `mcp-servers/nexus/` and the `nexus-cli` dependency from any config

The shim is not needed in Python — the TS server runs independently until retired.

---

## 5. MCP Config Delta (Claude Desktop / claude_desktop_config.json)

**Phase 1 change** (remove nexus, keep obsidian-ops — 2 tools already covered):

```json
// REMOVE this entry:
"nexus": {
  "command": "bun",
  "args": ["/path/to/mcp-servers/nexus/src/index.ts"]
}

// obsidian-ops entry already present — no change needed
```

**Phase 4 change** — no config change needed; new Python tools are auto-registered by FastMCP in the same `obsidian-ops` server process.

---

## 6. Tool Naming Conventions (post-merge)

- Tool names: `snake_case`, no prefix (obs already uses this style — `search_notes` not `obs_search_notes`)
- All new research-domain tools follow the existing pattern: `<noun>_<verb>` or `<noun>` (e.g., `zotero_search`, `course_list`)
- No `nexus_` prefix in any new tool name
- `unified_search` is the one tool that breaks the sub-domain noun-first pattern — acceptable because it genuinely spans all domains

---

*Artifact locked 2026-06-21. Changes require RFC amendment.*
