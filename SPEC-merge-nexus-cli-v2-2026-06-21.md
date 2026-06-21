# SPEC v2 — Merge `nexus-cli` into `obsidian-cli-ops`

**Status:** RFC v2 — decision-ready Phase 0 (supersedes `SPEC-merge-nexus-cli-2026-06-19.md` / issue #35)
**Date:** 2026-06-21
**Owner:** @dtofighi
**Affects:** `Data-Wise/obsidian-cli-ops` (survivor), `Data-Wise/nexus-cli` (slimmed/retired), `Data-Wise/mcp-servers/nexus` (TS MCP), `Data-Wise/homebrew-tap`, PyPI `nexus-cli`

> **Why a v2?** An adversarial review (2026-06-21) verified the v1 spec against the live repos and found it (a) rests on **stale data**, (b) maps work onto **commands/servers that already exist or live elsewhere**, and (c) hand-waves the five genuinely hard parts. v1's *strategy* (one Obsidian CLI, layered AI, option B) survives; v1's *Phase 0* did not. This v2 rewrites Phase 0 into a contract-producing phase with verified facts and a sign-off-ready decision matrix. **No code moves until §6 is ratified.**

---

## 1. Summary

Two Python Obsidian CLIs overlap on vault operations:

- **`obs`** (`obsidian-cli-ops`) — **v3.5.0**; vault discovery + graph analysis + multi-provider AI; SQLite-backed; in-repo Python MCP server.
- **`nexus`** (`nexus-cli`) — **v0.6.1**; broader research/teaching/writing workflow; deliberately AI-free; **stateless filesystem**; a **separate TypeScript** MCP server.

Proposal unchanged in spirit: `obs` absorbs nexus's **vault + graph-export + structure-validation** capability under a **layered-AI** model; non-vault domains (Zotero/PDF/teaching/writing) are handled by an **explicit Tier-2 decision** (recommended: **option B**, nexus becomes a thin research tool that depends on `obs`).

## 2. Corrected baseline (verified 2026-06-21)

| | `obs` (obsidian-cli-ops) | `nexus` (nexus-cli) |
|---|---|---|
| Version | **3.5.0** (was "3.4.2") | **0.6.1** (was "0.5.0") |
| Tests | ~**341 pytest + 59 Jest** (≈400; internal docs disagree 314/341/400 — re-baseline in P0) | **746** collected, ~**89.5%** cov (was "422 / 75%") |
| Python floor | 3.9+ | 3.11+ *(policy only — both use `from __future__ import annotations`, so neither needs >3.9 at runtime)* |
| Storage | **SQLite** (`~/.config/obs/obs.db`, scan→DB→query) | **stateless FS** (`Path.rglob`, no DB) |
| Config | **shell-env** `~/.config/obs/config` (`OBS_ROOT=…`) | **YAML** `~/.config/nexus/config.yaml` (zotero/vault/pdf/teach/write) |
| Command shape | flat (`obs search`, `obs ai …`) | domain (`nexus knowledge|research|teach|write …`) |
| Vault CLI ops | discover, scan, analyze, stats, vaults, db, search, health, bridge, trends, stale, daily-digest | search, read, write, daily, template, backlinks, recent, orphans, graph export (graphml/d3/json) |
| `doctor` | **EXISTS** (v3.5.0) — 5-layer *self-diagnostic* (Python/DB/vault/MCP/iCloud) | health/integration check; **PARA validation lives in `vault_spec.py`/`vault-spec.yaml`**, not in `doctor` itself |
| AI | yes — 5 providers, **opt-in** (`obs ai …`), provider-gated | none |
| MCP server | **in-repo Python** (FastMCP, 25 tools, key `obsidian-ops`); note CRUD already implemented (read/write/create/append/rename/delete) | **separate TS/Bun repo** `mcp-servers/nexus` (~15 `nexus_*` tools, key `nexus`) |
| Distribution | Homebrew only | Homebrew **+ PyPI** (`pip install nexus-cli`, OIDC) |

> The "≈360 extra tests" and the "doctor already exists / nexus MCP is TypeScript / configs are different formats" facts are the reason v1's effort estimates and Phase 3 were wrong.

## 3. What this corrects in v1

| v1 claim | Reality | Impact |
|---|---|---|
| §8: map nexus vault cmds onto obs as **de-duplication** | obs has **none** of read/write/daily/template/backlinks/recent at the CLI | It's **net-new CLI** (≈10 cmds), though obs's **MCP layer already implements note CRUD** → wrap, don't reinvent |
| §8: `nexus doctor → obs doctor (new)` | `obs doctor` **already exists** (self-diagnostic); nexus PARA logic is in `vault_spec`, not `doctor` | **Name collision** + wrong port target — see §5.3 |
| §7/§10: "collapse the **two** MCP servers" | nexus MCP = **separate TS repo**, obs MCP = in-repo Python | **Cross-language migration**, not a prefix change — see §5.4 |
| §1/§3: versions & test counts | Stale by 1–2 cycles; nexus tests +77%, cov +14pts | All estimates understated ~50% |
| §10: Python floor "bump to 3.11 to unblock nexus code" | No language constraint — both run on 3.9 | Demoted to a **policy** choice, not a blocker |
| §7 + CLAUDE.md: enforce **`NN_snake_case`** | nexus `vault-spec.yaml` enforces **`00-INBOX`** (NN-HYPHEN/caps); nexus *docs* `.STATUS` claims it propagated `NN_snake_case` | **3-way convention conflict** — must be reconciled before `doctor` enforces anything — see §5.3 |

## 4. Status quo — the null hypothesis (was missing in v1)

Before merging, the burden is on "why not coexist." Compare four TCOs in Phase 0:
- **(0) Coexist** with a documented division of labor (obs = vault, nexus = research) — cheapest now, pays the "two tools, one job" tax forever.
- **(1) Merge + option B** (recommended) — one vault CLI; nexus shrinks to research, depends on obs.
- **(2) Merge + option A** (obs absorbs everything) — re-bloats obs against its v3 "do one thing" charter.
- **(3) Facade/wrapper** — a thin `obs`/`nexus` umbrella that dispatches to both, no real merge.

Recommendation stands (option 1/B), **but the decision record must state why (0) is insufficient** — concretely: duplicated vault search/orphan/backlink/graph code across two test suites + two release cadences, and user/Claude ambiguity over which tool owns vault ops.

## 5. The five hard parts (Phase 0 must deliver a sub-spec for each)

### 5.1 Data model — SQLite vs stateless FS  *(blocks Phase 1)*
obs is DB-backed (scan→SQLite→query, graph metrics consistent); nexus reads the filesystem live. Porting `read/write/daily/template` is a **paradigm choice**, not a port:
- **(A) FS-direct** for read/write/daily/template (fast, always-fresh) + DB only for graph/analytics. *Recommended* — matches each op's nature; least churn.
- **(B) DB-through** everything (graph-consistent, but every write must re-index; slower).
- **Deliverable:** a one-page decision + the rule for when an op touches the DB vs the FS, and how writes invalidate cached graph metrics.

### 5.2 Config schema  *(blocks Phase 1)*
obs = shell-env file; nexus = YAML with domain sections. v1 said Phase 0 "locks" this but delivered nothing.
- **Recommended:** a single **YAML** `~/.config/obsidian/config.yaml` (or keep `~/.config/obs/`) with `vault:` (shared) + `ai:` (obs) + `research:` (nexus: zotero/pdf/teach/write) sections; obs reads `vault:`+`ai:`, nexus reads `vault:`+`research:`.
- **Deliverable:** the actual unified schema + a migration shim that reads both legacy `obs` shell-env and `nexus` YAML for ≥1 release.

### 5.3 `doctor` + PARA convention  *(blocks Phase 2)*
Two problems: (i) `obs doctor` already exists with different semantics; (ii) the convention is contradictory.
- **Command UX (decide):** merge into one `obs doctor` that runs both self-diagnostic **and** vault-structure checks; OR namespace (`obs doctor` = health, `obs doctor structure` / `obs doctor vault` = PARA). *Recommended:* namespaced subcommand — keeps the shipped self-diagnostic intact.
- **Convention (decide + reconcile FIRST):** pick the canonical form — `NN_snake_case` (`00_inbox`) vs `NN-HYPHEN/caps` (`00-INBOX`). The live `nexus-cli/vault-spec.yaml` says `00-INBOX`; the `nexus` docs `.STATUS` says it propagated `NN_snake_case`. **These must be reconciled before any validator enforces one**, or it will flag healthy vaults. *Action:* inspect the live Research/Knowledge_Base vaults, set the truth in one place (`vault-spec.yaml`), then port.
- **Port target:** nexus's `vault_spec.py` + `vault-spec.yaml` engine (not a "doctor command").

### 5.4 MCP consolidation  *(cross-language; own workstream)*
nexus MCP = **TS/Bun** (`mcp-servers/nexus`, ~15 `nexus_*` tools, key `nexus`); obs MCP = **Python** (FastMCP, 25 tools, key `obsidian-ops`). Options:
- **(A)** Port the 15 TS tools to obs's Python `mcp_server.py` (rewrite), retire the `nexus` MCP key, give Claude clients a deprecation window to switch keys. *Recommended for the vault subset;* the research tools follow the Tier-2 decision.
- **(B)** Keep a separate research MCP (option B symmetry): obs MCP owns vault tools; a slimmed nexus MCP owns Zotero/PDF/teach/write and calls obs for vault ops.
- **Deliverable:** tool-name map (old `nexus_vault_*` → obs equivalents), the client-migration note for the `nexus`→`obsidian-ops` key, and which tools are retired vs ported.

### 5.5 Deprecation — PyPI + Homebrew  *(was absent)*
- **PyPI:** `nexus-cli` is published. Option B's rename kills `pip install nexus-cli`. Ship a **final `nexus-cli` release** that prints a deprecation banner and points to the successor (`pip install <new-name>`); keep ≥1–2 cycles; update the PyPI description.
- **Homebrew:** two formulae in `data-wise/tap`. Decide: retire `nexus-cli.rb` vs rename vs fold options into `obsidian-cli-ops.rb`. **obs's formula needs MANUAL resource-block regen** when deps change (nexus adds Typer/Zotero deps) — schedule it *before* the release tag.
- **Rollback:** tag `pre-merge` on obs `main`; keep a revert branch; define a 48h validation window on the live vaults before deleting nexus surfaces.

## 6. Decision matrix — sign-off gate (ratify before Phase 1)

| # | Decision | Options | Recommendation | Verified constraint |
|---|---|---|---|---|
| D1 | **Tier-2 scope** | A absorb / B sibling-dep / C spin-out | **B** | nexus has *zero* dep on obs today; obs not importable (no PyPI) → B needs an integration (D2) |
| D2 | **nexus→obs integration** (if B) | Python import / subprocess CLI / MCP call | subprocess or MCP (import couples release cycles + needs packaging) | obs ships no importable package |
| D3 | **Data model** | FS-direct / DB-through | FS-direct (§5.1) | obs SQLite vs nexus FS |
| D4 | **Config** | unified YAML / dual + shim | unified YAML + shim (§5.2) | formats differ (env vs YAML) |
| D5 | **`doctor` UX** | merge / namespace | namespace (§5.3) | `obs doctor` already exists |
| D6 | **PARA convention** | `NN_snake` / `NN-HYPHEN` | reconcile to live vaults first (§5.3) | 3-way conflict |
| D7 | **MCP strategy** | port TS→Py / dual server | port vault tools; research per D1 (§5.4) | nexus MCP is TS, separate repo |
| D8 | **Command shape** | flat / domain / aliases | keep obs flat + add domain aliases for nexus muscle memory | obs flat, nexus nested |
| D9 | **Python floor** | 3.9 / 3.11 | keep 3.9 (policy, not constraint) | both run on 3.9 |
| D10 | **PyPI/Homebrew fate** | retire / rename / fold | rename + deprecate (§5.5) | nexus on PyPI; 2 tap formulae |

## 7. Revised migration plan

- **Phase 0 — Decision & contract (this doc, ratified).** Deliverables: §6 signed; §5.1–5.5 sub-specs written; §4 TCO recorded; baseline re-confirmed. **Exit criteria:** every D1–D10 has a decision; unified config schema + tool-name map exist as artifacts.
- **Phase 1 — Vault/graph parity.** Add the net-new vault CLI commands (wrapping existing obs MCP note-CRUD where possible); port graph-export formats into obs's graph module; merge test suites (budget the real ~1,000-test reconciliation + mypy-gate + coverage-threshold decision).
- **Phase 2 — Structure validation.** Port `vault_spec` PARA engine under the D5 `doctor` UX; teach it the D6 canonical convention; tests.
- **Phase 3 — MCP (cross-language).** Execute D7: port vault tools TS→Python under `obsidian-ops`; client key-migration window.
- **Phase 4 — nexus slim-down (option B).** Strip vault/graph from nexus; wire D2 integration; rename per D10.
- **Phase 5 — Deprecate & release.** PyPI deprecation banner; Homebrew formula change (+ manual resource regen); rollback tag; obs major release; migration guide.

## 8. Risks (additions to v1 §10)
Cross-language MCP migration (critical path) · PyPI package retirement · Homebrew dual-formula + manual resource regen · no rollback path · config format mismatch · data-model paradigm clash · PARA-convention contradiction breaking live vaults. (v1's "two MCP servers / Python-floor blocker" framings were inaccurate — see §3.)

## 9. Recommendation
Proceed with **Tier-1 merge + option B + layered AI**, *but only after Phase 0 produces the five sub-specs (§5) and D1–D10 are signed (§6)*. The strategy is sound; the prior risk was executing on stale data and undefined contracts. This v2 removes that risk.

---
*Provenance: corrections in §2/§3 verified against obs v3.5.0 and nexus v0.6.1 at HEAD on 2026-06-21 (versions, test counts, command surfaces, MCP servers, config formats, storage models, `vault-spec.yaml` convention). Supersedes v1; keep #35 open and link this.*
