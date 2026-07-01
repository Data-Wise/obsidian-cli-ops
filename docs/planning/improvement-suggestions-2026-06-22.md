# obsidian-cli-ops — Improvement Suggestions & Feature Requests
**Date:** 2026-06-22 · **Repo:** [Data-Wise/obsidian-cli-ops](https://github.com/Data-Wise/obsidian-cli-ops) · **Observed on:** `obs` v4.0.0

> [!success] RESOLVED (2026-07-01) — 4 of 5 issues shipped (v4.1–v4.3)
> This was a live-testing triage from a Cowork session. Four of the five filed issues have since shipped; only **#54** (AI enrichment on scan) remains open. Status table updated below; original evidence kept for history. For **live state** see [`.STATUS`](../../.STATUS).

> Consolidated from a Cowork session (live testing of the obsidian-ops MCP + `obs` CLI while wiring the daily scoop-tripwire) **plus** an investigation of similar Cowork threads. Every item is grounded in something actually observed, not speculation.

---

## TL;DR

- **5 issues filed** this session: 1 bug, 4 features — see table below.
- **Outcome:** #40, #51, #52, #53 **shipped** (v4.1–v4.3); **#54 still open** — the highest-leverage AI feature.
- Biggest themes across sessions: **stale-index / rescan friction**, **MCP↔CLI version drift**, **note-title/tag hygiene**, and an opportunity for **AI-assisted enrichment on scan**.

---

## 1. Filed issues (status)

| # | Type | Title | Status |
|---|------|-------|--------|
| [#40](https://github.com/Data-Wise/obsidian-cli-ops/issues/40) | feat | Section/heading-aware insertion for `append_to_note` (under-heading + table-row), not just EOF | ✅ **Shipped** |
| [#51](https://github.com/Data-Wise/obsidian-cli-ops/issues/51) | bug | Empty-title note aborts with `NOT NULL constraint failed: notes.title` and is dropped from the index | ✅ **Shipped** |
| [#52](https://github.com/Data-Wise/obsidian-cli-ops/issues/52) | feat | First-class `obs scan/rescan <vault>` verb + stale-index awareness | ✅ **Shipped** (`--prune`, stale-index warnings) |
| [#53](https://github.com/Data-Wise/obsidian-cli-ops/issues/53) | feat | Expose running-server version + "restart needed" so stale MCP servers are detectable | ✅ **Shipped** (`server_info`) |
| [#54](https://github.com/Data-Wise/obsidian-cli-ops/issues/54) | feat | AI-assisted enrichment on scan/ingest — auto-title untitled notes, suggest tags + links (opt-in, dry-run-first) | 🟡 **Open** |

---

## 2. Remaining work — #54: AI-assisted enrichment on scan

The one survivor, and the highest-leverage AI feature: it converts the index-hygiene problems the other four issues surfaced (untitled notes, stale tags) from manual chores into an automatic, reviewable step.

- Build on existing `obs ai *` (tag-suggest, suggest-links, quality). New `obs ai enrich <vault> [--titles] [--tags] [--links] [--only-missing] [--dry-run] [--apply]`.
- **Auto-title** untitled notes from content (never overwrite existing); **auto-tag** from the vault's *existing* controlled vocabulary (no sprawl); **suggest links** as a proposal block.
- **Safety:** opt-in, dry-run-first (writes a proposal note to `00_meta/`), batch + content-hash cache for cost, never mutate without `--apply`. Do **not** call the LLM inside the scan loop by default (keep scan fast/offline).

---

## 3. Original evidence (historical — v4.0.0 observations)

### #51 — bug: empty-title note crashed the scanner (fixed)
Observed during a forced rescan of `Documents`:
```
sqlite3.IntegrityError: NOT NULL constraint failed: notes.title
RESCAN_OK notes_scanned=3454 links_found=1209 dur=22.3s
```
3454 notes indexed, but ≥1 untitled note was rejected and never entered `notes`. Fixed via filename-stem fallback; never insert NULL; skipped notes reported instead of a raw traceback.

### #52 — feat: real rescan verb + stale-index awareness (shipped)
- `obs scan` / `obs rescan` → `Unknown command`; `obs analyze Documents` printed metrics while `Last Scanned` stayed **3 days ago** — analyzing a **stale** index with no warning. A real `scan_vault(force=True)` moved notes 3365 → 3454, links 907 → 1209.
- Shipped: `obs scan <vault>` (`--prune`, `--force`), stale-index awareness, shared with MCP `rescan_vault`.

### #53 — feat: MCP server version / restart-needed visibility (shipped)
- Installed `obs version` = v4.0.0 (with the rescan fix), but the live MCP `rescan_vault` still failed (`asyncio.run() cannot be called from a running event loop`) — the in-process server predated the fix and **nothing surfaced the mismatch**.
- Shipped: `server_info` tool exposing running version / build so drift is detectable.

### #40 — feat: heading/table-aware `append_to_note` (shipped)
- `append_to_note` only appended to EOF, so hit-rows landed in the wrong section and broke tables.
- Shipped: `under_heading` + section/table-row modes; default EOF behavior unchanged.

---

## 4. Quick-win improvements (historical)

- **Restart hint in `bridge status`** — folded into #53 (`server_info`).
- **`append_to_note` separator hygiene** — folded into #40's table-row handling.
- **Homebrew-tap auto-bump** — recurring: GitHub release ships, but `obs version` lags until the tap formula bumps manually. `APP_ID`/`APP_PRIVATE_KEY` now wired for auto-bump.
- **Operational:** rescan `Knowledge_Base` when convenient (was stale at time of writing).

---

## 5. Cross-session investigation findings (historical)

Recurring, corroborating signals from related Cowork sessions:

| Theme | Evidence (session) | Maps to |
|-------|--------------------|---------|
| **Stale index / rescan was broken** | "Literature radar weekly" references "the obs/rescan bug"; v4.0.0 shipped a "real rescan" fix | #52, #53 |
| **MCP↔release↔Homebrew version drift** | "Connector feasibility": `obs version` showed 3.2.2 after a 3.2.3 release because the tap hadn't bumped | #53 + quick-win |
| **Source-of-truth / loose-copy hygiene** | `savant` is the research-skills source of truth; canonical `00_meta/` hub | #54 (proposals into `00_meta/`) |
| **Title/tag hygiene matters for retrieval** | Radar/tripwire dedupe + search depend on a clean, well-tagged index | #51, #54 |

**Net finding (still true):** wiring the *existing* `obs ai` enrichment into the scan/ingest path (→ #54) remains the highest-leverage AI feature.

---

*Generated in Cowork while testing obsidian-ops live. Status reconciled 2026-07-01 — #40/#51/#52/#53 shipped, #54 open.*
