# SPEC — Merge `nexus-cli` into `obsidian-cli-ops`

**Status:** Draft / RFC
**Date:** 2026-06-19
**Owner:** @dtofighi
**Affects:** `Data-Wise/obsidian-cli-ops` (survivor), `Data-Wise/nexus-cli` (absorbed/retired)

---

## 1. Summary

We maintain **two Python Obsidian CLIs** that have grown to overlap on vault operations:

- **`obs`** (`obsidian-cli-ops`, v3.4.2, 304 tests) — laser-focused vault management + graph analysis + **multi-provider AI**.
- **`nexus`** (`nexus-cli`, v0.5.0, 422 tests) — broader research/teaching/writing knowledge workflow; **deliberately no AI** ("Claude is the brain"); adds Zotero, PDF, Quarto, manuscripts, tutorials, and PARA-`doctor`.

This spec proposes a **scoped merge**: `obs` absorbs nexus's **vault + graph + structure-validation** capabilities (which are squarely "Obsidian vault management"), and we make an **explicit decision** about nexus's non-vault domains (Zotero / PDF / teaching / writing) rather than swallowing them wholesale. Goal: **one Obsidian CLI**, less duplication, no philosophy whiplash.

## 2. Why merge

- **Two tools, one job.** Both read/search/organize Obsidian notes and export graphs. Users (and Claude) shouldn't have to know whether vault search is `obs ...` or `nexus knowledge vault search ...`.
- **Maintenance tax.** Two test suites (304 + 422), two CIs, two doc sites, two release cadences for overlapping code.
- **Divergent AI philosophy is a feature, not a blocker** — see §5. We can keep both stances by making AI an *optional layer*.

## 3. Side-by-side

| | `obs` (obsidian-cli-ops) | `nexus` (nexus-cli) |
|---|---|---|
| Version / tests | 3.4.2 / 304 | 0.5.0 / 422 (75% cov) |
| Python | 3.9+ | 3.11+ |
| Scope | Obsidian vault mgmt + graph | research/teaching/writing knowledge workflow |
| AI | **Yes** — multi-provider (Gemini/Anthropic/Ollama/CLI) | **No** — data/ops only, Claude thinks |
| Command shape | flat (`obs stats`, `obs ai ...`) | domain (`nexus knowledge|research|teach|write ...`) |
| Vault ops | discover, stats, analyze, graph (PageRank/centrality), orphans, hubs, broken links | search, read, write, daily, backlinks, recent, orphans, template, **graph export** (graphml/d3/json) |
| Structure | — | **`doctor`** validates PARA vault structure |
| Non-vault | — | Zotero (2.7k papers), PDF, Quarto, manuscripts, **unified search**, `learn` tutorials |

## 4. Overlap & uniqueness

**Overlap (must de-duplicate):** vault search, orphan detection, backlinks, recent, graph export. Both have a graph layer (obs: analysis/metrics; nexus: export formats).

**Unique to obs (keep):** AI multi-provider layer; PageRank/centrality/clustering; the v3 "do one thing well" simplification.

**Unique to nexus (candidates to absorb):**
- ✅ **Vault-aligned:** `vault read/write/daily/template`, `graph export graphml|d3|json`, `doctor` (PARA validation), `config`.
- ⚠️ **Not vault management:** `research zotero …`, `research pdf …`, `teach …`, `write …`, `knowledge search` (cross-source).
- ✅ **Cross-cutting:** `learn` interactive tutorials.

## 5. Philosophy reconciliation (the key decision)

`obs` does AI; `nexus` refuses AI on purpose. Reconcile by **layering**, not choosing:

```
obs (unified)
├── core: data + operations         ← nexus's stance is the DEFAULT (Claude is the brain)
│   read · write · search · graph · doctor · daily · template
└── ai/  (OPTIONAL, provider-gated)  ← obs's stance, off by default
    similar · gaps · refactor · quality · summarize …
```

- The **deterministic data/ops core** is always available and AI-free (satisfies nexus users).
- **AI is an opt-in subcommand namespace** (`obs ai …`) requiring a configured provider (already true in obs). Nothing AI runs unless asked.
- This lets the merged tool serve "Claude is the brain" workflows **and** standalone AI workflows from one binary.

## 6. Scope decision (explicit — needs sign-off)

**Tier 1 — merge now (vault + graph + structure):** absorb nexus's vault ops, graph export, `doctor`, `config`, `learn` into `obs`. Fits obs's charter exactly.

**Tier 2 — decide deliberately (non-vault domains):** Zotero / PDF / Quarto / manuscripts. Three options:
- **(A) Absorb as optional modules** (`obs research zotero …`) — re-expands obs scope (tension with "laser focus on vaults"). 
- **(B) Keep as a thin sibling** (`nexus` becomes a *research-workflow* tool that depends on `obs` for vault ops) — preserves obs focus; nexus shrinks to non-vault domains.
- **(C) Spin out** Zotero/PDF into their own small tool.
- **Recommendation: (B)** — `obs` owns *all Obsidian/vault/graph*, nexus (renamed e.g. `lab` / `research-cli`) keeps *only* Zotero/PDF/teaching/writing and calls `obs` for vault access. Cleanest charter split; no philosophy clash; smallest blast radius.

## 7. Target architecture (assuming Tier-1 merge + option B)

```
obsidian-cli-ops/  (obs — the single Obsidian CLI)
  core/        read · write · search · daily · template · backlinks · recent
  graph/       analysis (PageRank/centrality) + export (graphml/d3/json)   ← merge both graph layers
  structure/   doctor (PARA validator; enforces NN_snake_case convention)  ← from nexus
  ai/          optional, provider-gated (existing obs AI)
  tutorials/   learn (getting-started/medium/advanced)                     ← from nexus
  mcp/         single MCP server (supersedes the two existing ones)
```

> Note: the `doctor` validator should enforce the **current vault convention** (`NN_snake_case` top-level + `snake_case` subfolders; `_`-prefixed pinned stores) used by the live Research/Knowledge_Base vaults and the nexus vault-template.

## 8. Command mapping (nexus → obs)

| nexus | obs (proposed) | Notes |
|---|---|---|
| `nexus knowledge vault search` | `obs search` | de-dupe with obs vault search |
| `nexus knowledge vault read/write/daily/template` | `obs read` / `obs write` / `obs daily` / `obs template` | new in obs |
| `nexus knowledge vault backlinks/recent/orphans` | `obs backlinks` / `obs recent` / `obs orphans` | orphans already in obs |
| `nexus knowledge vault export {graphml,d3,json}` | `obs graph export {…}` | merge into obs graph |
| `nexus doctor` | `obs doctor` | PARA + convention validator |
| `nexus config` | `obs config` | unify config schema |
| `nexus learn` | `obs learn` | port tutorials |
| `nexus research|teach|write …` | **stays in `nexus`** (option B) | non-vault; nexus depends on obs |

## 9. Migration plan

- **Phase 0 — Inventory & contract** (1–2 days): exhaustive command/feature diff; pick the Tier-2 option (§6); lock the unified `config` schema + MCP tool surface. *Deliverable: this spec, ratified.*
- **Phase 1 — Vault/graph parity** (port nexus vault ops + graph export into obs; reconcile duplicate orphan/backlink logic; one graph module). Tests merged.
- **Phase 2 — `doctor` + convention validator** (port PARA `doctor`; teach it the `NN_snake_case` convention).
- **Phase 3 — tutorials + MCP** (port `learn`; collapse the two MCP servers into one; update `obsidian-ops` MCP tool names).
- **Phase 4 — nexus slim-down** (option B): strip vault/graph from nexus; have it call `obs`; rename if desired; cross-link docs.
- **Phase 5 — deprecate & release** (nexus-cli `knowledge` commands print deprecation → `obs`; major release of obs; homebrew-tap formula update; changelog/migration guide).

## 10. Risks & mitigations

| Risk | Mitigation |
|---|---|
| Scope creep re-bloats obs (vs its v3 simplification) | Tier-2 option B keeps non-vault out of obs |
| Python floor (3.9 vs 3.11) | bump obs to 3.11 (it already targets modern Python) or keep 3.10 floor; decide in Phase 0 |
| Test/CI merge churn (304+422) | port by module with tests; don't big-bang |
| Two MCP servers in use downstream | keep `obsidian-ops` MCP name; add nexus tools under it; deprecation window |
| Breaking users' `nexus knowledge …` muscle memory | deprecation shims + aliases for ≥1 minor cycle |

## 11. Open questions (for the obsidian-cli-ops dev)

1. **Tier-2 decision:** absorb non-vault domains (A), sibling-with-dependency (B, recommended), or spin out (C)?
2. **AI default:** confirm AI stays opt-in/provider-gated so the merged tool honors the "Claude is the brain" default.
3. **Command shape:** keep obs's flat commands, or adopt nexus's domain grouping for the absorbed surface?
4. **Python floor** and **single MCP server** name/ownership.
5. Survivor naming: keep `obs` / `obsidian-cli-ops`, or rebrand the unified tool?

## 12. Recommendation

Proceed with **Tier-1 merge** (vault + graph + `doctor` + tutorials → `obs`) under the **layered AI** model (§5) and **option B** for non-vault domains (§6). This yields one Obsidian CLI with a clean charter, preserves both AI philosophies, and shrinks `nexus` to a focused research-workflow tool that builds on `obs`.
