# obsidian-cli-ops — Improvement Suggestions & Feature Requests
**Date:** 2026-06-22 · **Repo:** [Data-Wise/obsidian-cli-ops](https://github.com/Data-Wise/obsidian-cli-ops) · **Installed:** `obs` v4.0.0

> Consolidated from this Cowork session (live testing of the obsidian-ops MCP + `obs` CLI while wiring the daily scoop-tripwire) **plus** an investigation of similar Cowork threads. Every item is grounded in something actually observed, not speculation.

---

## TL;DR

- **5 issues filed** this session: 1 bug, 4 features — see table below.
- Biggest themes across sessions: **stale-index / rescan friction**, **MCP↔CLI version drift**, **note-title/tag hygiene**, and an opportunity for **AI-assisted enrichment on scan**.
- Suggested order: **#51 → #52 → #40 → #54 → #53**.

---

## 1. Filed issues (status)

| # | Type | Title | Why it matters |
|---|------|-------|----------------|
| [#40](https://github.com/Data-Wise/obsidian-cli-ops/issues/40) | feat | Section/heading-aware insertion for `append_to_note` (under-heading + table-row), not just EOF | Unblocks the scoop-tripwire's table writes (rows currently land under the wrong trailing section) |
| [#51](https://github.com/Data-Wise/obsidian-cli-ops/issues/51) | bug | Empty-title note aborts with `NOT NULL constraint failed: notes.title` and is dropped from the index | Correctness hole: untitled notes silently invisible to search/graph/MCP |
| [#52](https://github.com/Data-Wise/obsidian-cli-ops/issues/52) | feat | First-class `obs scan/rescan <vault>` verb + stale-index awareness | No discoverable rescan; `analyze` silently runs on stale data |
| [#53](https://github.com/Data-Wise/obsidian-cli-ops/issues/53) | feat | Expose running-server version + "restart needed" so stale MCP servers are detectable | A v4.0.0 CLI with a stale in-process MCP fails silently with no signal |
| [#54](https://github.com/Data-Wise/obsidian-cli-ops/issues/54) | feat | AI-assisted enrichment on scan/ingest — auto-title untitled notes, suggest tags + links (opt-in, dry-run-first) | Turns dropped/untitled notes into searchable, well-tagged ones; keeps the graph healthy automatically |

---

## 2. Issue detail

### #51 — bug: empty-title note crashes the scanner (CONFIRMED, v4.0.0)
Observed during a forced rescan of `Documents`:
```
sqlite3.IntegrityError: NOT NULL constraint failed: notes.title
RESCAN_OK notes_scanned=3454 links_found=1209 dur=22.3s
```
3454 notes indexed, but ≥1 untitled note was rejected and never entered `notes`. **Fix:** filename-stem fallback → `(untitled)`; never insert NULL; report `notes_skipped` (count + paths) in `ScanResult` instead of a raw traceback.

### #52 — feat: real rescan verb + stale-index awareness (CONFIRMED gap)
- `obs scan` / `obs rescan` → `Unknown command`; `obs help --all` lists no scan verb.
- `obs analyze Documents` printed metrics while `Last Scanned` stayed **3 days ago** and counts were unchanged — i.e. it analyzed a **stale** index with no warning. A real `scan_vault(force=True)` moved notes 3365 → 3454, links 907 → 1209.
- **Fix:** `obs scan <vault>` (alias `rescan`, `--all`, `--force`, shared with MCP `rescan_vault`); warn on `analyze`/`search`/`health` when the index is stale; optional `--rescan`.

### #53 — feat: MCP server version / restart-needed visibility
- Installed `obs version` = v4.0.0 (with the "real rescan" fix), but the live MCP `rescan_vault` still failed: `asyncio.run() cannot be called from a running event loop` — the in-process server predated the fix, and **nothing surfaced the mismatch**.
- **Fix:** `server_info` tool (or `version`/`build`/`started_at` on `get_bridge_status`); flag `restart_recommended` when running < installed.

### #40 — feat: heading/table-aware `append_to_note`
- `append_to_note` only appends to EOF. Both radar notes have a section *after* the target table (`## Hits` → `## Scan log`; dedup table → `## Citation-chase targets`), so hit-rows land in the wrong section and break the table.
- **Fix:** `under_heading` + `mode: eof|section|table_row` (default `eof`); validate table column count; default behavior unchanged.

### #54 — feat: AI-assisted enrichment on scan (the "AI titles + tags" idea)
- Build on existing `obs ai *` (tag-suggest, suggest-links, quality). New `obs ai enrich <vault> [--titles] [--tags] [--links] [--only-missing] [--dry-run] [--apply]`.
- **Auto-title** untitled notes from content (never overwrite existing); **auto-tag** from the vault's *existing* controlled vocabulary (no sprawl); **suggest links** as a proposal block.
- **Safety:** opt-in, dry-run-first (writes a proposal note to `00_meta/`), batch + content-hash cache for cost, never mutate without `--apply`. Do **not** call the LLM inside the scan loop by default (keep scan fast/offline).

---

## 3. Quick-win improvements (not yet filed)

- **Restart hint in `bridge status`** — a one-line "running vX vs installed vY" would have instantly explained today's stale-server failure (overlaps #53; cheap to add now).
- **`append_to_note` separator hygiene** — when appending a table row, guard against the default `\n\n` landing *inside* a table block (breaks the table). Fold into #40's acceptance criteria.
- **Homebrew-tap auto-bump** — recurring across sessions: GitHub release ships, but `obs version` lags until the tap formula bumps manually. Wire `APP_ID`/`APP_PRIVATE_KEY` so `homebrew-release.yml` auto-bumps (noted as a "next session" item in the connector-feasibility session, still open).
- **Operational:** `Knowledge_Base` vault is still "3 days ago" — rescan when convenient (the `Documents` vault was refreshed this session).

---

## 4. Cross-session investigation findings

Reviewed related Cowork sessions via session inspection. Recurring, corroborating signals:

| Theme | Evidence (session) | Maps to |
|-------|--------------------|---------|
| **Stale index / rescan was broken** | "Literature radar weekly" references "the obs/rescan bug I drafted the issue for"; v4.0.0 shipped a "real rescan" fix because the old path shelled to read-only `obs stats` | #52, #53 |
| **MCP↔release↔Homebrew version drift** | "Claude Obsidian connector feasibility": `obs version` showed 3.2.2 after a 3.2.3 release because the tap hadn't bumped; "next session: add APP_ID/APP_PRIVATE_KEY secrets to automate" | #53 + quick-win |
| **Source-of-truth / loose-copy hygiene** | "Literature radar weekly": `savant` is the research-skills source of truth; loose `.skill` files are an anti-pattern; canonical `00_meta/` hub | #54 (write proposals into `00_meta/`, not loose notes) |
| **Title/tag hygiene matters for retrieval** | Radar/tripwire dedupe + search depend on a clean, well-tagged index; untitled/untagged notes degrade it | #51, #54 |
| **`analyze` cross-vault correctness** | Connector-feasibility session fixed `obs analyze` cross-vault edge contamination + misleading link counts | (already fixed; watch for regressions) |

**Net new idea surfaced:** wiring the *existing* `obs ai` enrichment into the scan/ingest path (→ #54) is the highest-leverage AI feature — it converts the index-hygiene problems (#51, stale tags) from manual chores into an automatic, reviewable step.

---

## 5. Suggested priority / roadmap

1. **#51** (bug, correctness) — untitled notes shouldn't vanish. Smallest, highest-certainty fix.
2. **#52** (rescan UX) — the gap that forced manual `scan_vault` calls this session; also stops `analyze` from lying about freshness.
3. **#40** (heading/table append) — unblocks the scoop-tripwire's vault writes.
4. **#54** (AI enrichment) — builds on #51; biggest quality-of-life lift once #51/#52 land.
5. **#53** (version visibility) — diagnostics; prevents future "why did a fixed tool fail?" confusion.

---

*Generated in Cowork while testing obsidian-ops live. All five issues are open at [Data-Wise/obsidian-cli-ops/issues](https://github.com/Data-Wise/obsidian-cli-ops/issues).*
