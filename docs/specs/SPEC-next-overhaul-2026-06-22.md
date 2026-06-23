# SPEC — What's Next + Overhaul (post nexus-cli absorption)

**Status:** APPROVED — strategy brainstorm output (max mode, 3 verification agents + advisor); the one open fork (5.1 build-vs-delegate, §1) was signed off **2026-06-22 → delegate**.
**Date:** 2026-06-22
**Owner:** @dtofighi
**Supersedes the stale roadmap in:** `.STATUS` (`next:` Phase-5 items are largely already done), `IDEAS.md` (stamped v3.2.0)
**Feeds:** the v4.0.0 release; follow-on v4.1/v4.2 minors

> **One-line:** The absorption is far more done than the planning docs say. The single highest-leverage move is **shipping v4.0.0** — it closes a *live broken promise* (nexus-cli is retired and points users to `obs research`, but the installable obs has no `obs research`). Everything else sequences behind that.

---

## 0. Verified ground truth (2026-06-22)

Three read-only agents checked the **code and live distribution surfaces** against the planning narrative. Findings (with evidence) that change the plan:

| Claim in docs | Verified reality | Source |
|---|---|---|
| `.STATUS` `next:` = "Phase 5: retire nexus-cli (PyPI / tap / archive repo)" | **Already executed.** nexus-cli v0.7.0 on PyPI summary = "DEPRECATED — absorbed into obs"; tap `nexus-cli.rb` has `deprecate!`; source repo `.STATUS` = `deprecated/100`, repo archived 2026-06-21 | release agent |
| SPEC §5.4 "MCP consolidation = port ~15 TS tools, the big risk" | **Done (unreleased).** `mcp_server.py` (1678 ln) already wires all research tools (`unified_search`, `zotero_*`, `pdf_search`, `course_*`, `manuscript_*`, `bib_check`) — 33 research-tool refs | absorption agent |
| SPEC §5.5 "obs formula needs manual resource regen (Typer/Zotero deps)" | **Moot.** `research/*.py` imports only `yaml` (already a formula resource) + stdlib; zotero reads SQLite directly, pdftotext/quarto are runtime binaries. **No new Homebrew resources.** | release + absorption agents |
| IDEAS.md: `obs ai tag-suggest --apply` is "inert" | **False.** Full frontmatter write path: `obs_cli.py:817` → `:1451` → `features_vault.py:354 _apply_tag_to_frontmatter()` (writes tags >0.8 conf) | surface agent |
| Suspected CLI/MCP drift (temporal tools MCP-only) | **No drift.** `obs trends/stale/daily-digest/bridge/doctor/config/research` all shipped as CLI (`obs.zsh:785-800`, `obs_cli.py:825-859`) | surface agent |
| Installable obs already absorbs research | **No.** Homebrew pins `v3.5.0`; tag `v3.5.0` has **0** `obs research` refs; `main` has it. **Phase 1 is main-only, unreleased.** | this session |

**Net:** of the SPEC's five hard parts, **5.2 (config) and 5.4 (MCP) are code-complete on `main`; 5.5 (retirement) is executed.** Only **5.1 (vault-CRUD CLI) and 5.3 (PARA validator) are unstarted** — and 5.1 has an unresolved design fork (below). Coverage is *measured but unenforced* (`ci.yml:37` has `--cov`, no `--cov-fail-under`).

---

## 1. The debate the user asked for: build vs. delegate (hard part 5.1)

5.1 is the largest open item and the **only** decision that, gotten wrong, makes this spec misleading. nexus-cli's `knowledge vault` subgroup (`read / write / daily / template / backlinks / recent / orphans`) has **no `obs` CLI equivalent** today. Two readings:

- **Build (FS-direct), per ratified D3.** SPEC D3 reads "read/write/daily/template act on files live" → implement them as `obs` commands, FS-direct, DB only for graph. Honors the ratified contract. Effort **L**.
- **Delegate to the official Obsidian CLI** (the "brain + hands" strategy in project memory: obs analyzes, the official CLI executes). Shrinks 5.1 to a thin bridge enhancement. Effort **S**.

**The discriminator is offline capability, not tidiness.** The official Obsidian CLI **requires the app running** (IPC); nexus's vault CRUD was **stateless-FS / offline**. Delegating therefore trades an *offline regression* for less code.

> **RESOLVED (2026-06-22) → DELEGATE.** Offline, app-not-running vault read/write is **not** required. 5.1 routes vault CRUD (`read / write / daily / template / backlinks / recent / orphans`) to the official Obsidian CLI under the "brain + hands" model — `obs` analyzes/suggests, the official CLI executes — plus the existing bridge write-path. This **amends ratified D3** (which read "act on files live"): the accepted tradeoff is an *offline regression* (CRUD now requires the Obsidian app running via IPC) in exchange for a thin-bridge implementation. Effort drops **L → ~S**.
>
> Consequence for scope: with delegate chosen, the absorption is **effectively 4/5 hard parts resolved** (5.2 config + 5.4 MCP code-complete on `main`; 5.5 retirement executed; **5.1 now scoped to a thin bridge**). Only **5.3 (PARA validator)** remains as net-new build. The v4.1 "vault CRUD" chunk collapses from L to a bridge enhancement.

---

## 2. Recommendation — SHIP is the keystone, then sequence the rest

The user selected **all four directions**; they collapse into a sequence, not four buckets:

### 🟢 Now (keystone) — Ship v4.0.0: research-absorption + nexus-retirement
- **Why first / mildly urgent:** closes the live broken promise (§0 last row). Lowest effort of everything: retirement is *done*, resources are *moot*, release CI is *armed* (`homebrew-release.yml`, `APP_ID`+`APP_PRIVATE_KEY` set 2026-06-15; auto-bump works because no resources changed).
- **Scope honesty:** v4.0.0 ships the *research namespace + config + MCP research tools + nexus retirement*. It does **NOT** ship 5.1 (vault CRUD) or 5.3 (PARA). Say so in the changelog.
- **SemVer = v4.0.0** (plain reading, decide once): SPEC §7 committed the number; the whole-program contract changes (a sibling CLI disappears, MCP `nexus` key retired → `obsidian-ops`). The committed Phase-1 code is *additive* (new `config`/`research` namespaces + backward-compat config shim), but cutting it as v3.6.0 would force a second confusing major immediately after. One clean cut-line.
- **Work:** ~18-file version bump (`pyproject.toml`, `package.json`+lock, `src/python/__init__.py`, `src/obs.zsh:7,102`, `man/man1/obs.1:3` `.TH`, README badge, mkdocs pages, test assertions `tests/obs.test.js:58,183,185` + `__tests__/cli.test.js:53`) → PR → tag → release → CI auto-bumps tap.

### 🟢 Rides along with the release — Overhaul pass (low cost, high signal)
- Fix **IDEAS.md** false "`--apply` inert" claim (it has a write path); re-stamp it (currently says v3.2.0).
- Refresh **`.STATUS`**: mark Phase-5 retirement *done*; correct `progress` (75 understates it); drop the stale `next:` items.
- Add **`--cov-fail-under=70`** to `ci.yml` — the 70–80% "standard" in CLAUDE.md is currently fictional (measured, never gated); lock it before it silently regresses.
- Fix **`graph_builder.py:57`** alias TODO — small, self-contained; makes broken-link/backlink counts correct for alias-heavy vaults (currently `aliases:` targets resolve to None → false "broken").

### 🟡 After ship — Complete the absorption (the two real gaps)
1. **5.1 vault CRUD — DELEGATE (resolved §1, v4.1 / ~S):** thin bridge to the official Obsidian CLI (`read / write / daily / template / backlinks / recent / orphans`); `obs` analyzes, the official CLI executes. Amends D3. No FS-direct build. Document the offline regression (CRUD needs the app running) in the v4.1 changelog.
2. **5.3 PARA validator** `obs doctor structure` (v4.2 / M) — **blocked**: first rewrite nexus's stale `vault-spec.yaml` (`00-INBOX`/hyphen-caps) to per-vault-configurable `NN_snake_case` (D6), then port `vault_spec.py`. **This is now the only net-new build left in the absorption.**

### ⚪ Longer-horizon — New user value (post-v4 roadmap, refreshes IDEAS.md)
- Graph-native discovery the official CLI *cannot* do: shortest-path between notes, community detection (Louvain/Leiden), bridge-node detection.
- Bridge write-path batch ops (`obs apply <plan>` — the *real* unbuilt one; `--apply` already works for single tag-suggest): `batch-tag`, `batch-link`.
- `daily-digest` is shipped (CLI+MCP) — promote it in docs as the flagship "morning vault health" command.

---

## 3. Sequencing diagram

```
 v4.0.0 (NOW)                 v4.1                  v4.2               post-v4
 ┌──────────────┐    ┌────────────────────┐   ┌──────────────┐   ┌──────────────┐
 │ research+cfg │    │ 5.1 vault CRUD     │   │ 5.3 PARA     │   │ graph-native │
 │ +MCP shipped │ →  │ DELEGATE to        │ → │ doctor       │ → │ discovery,   │
 │ nexus retire │    │  official CLI (~S) │   │ structure    │   │ apply batch  │
 │ +overhaul    │    └────────────────────┘   └──────────────┘   └──────────────┘
 └──────────────┘
   closes live           thin bridge,            blocked on          IDEAS.md
   broken promise         offline regression      vault-spec rewrite  refresh
```

---

## 4. Acceptance criteria (v4.0.0 slice)

> ✅ **SHIPPED** — keystone delivered in **v4.0.0** (2026-06-22, PR #49) and hardened in **v4.0.1** (2026-06-23, PR #58). One item deferred (cov gate, see below).

- [x] Version bumped across the ~18 files; `tests/obs.test.js` + `__tests__/cli.test.js` + `man/man1/obs.1` `.TH` updated and green. *(v4.0.0; re-verified v4.0.1)*
- [x] `brew install data-wise/tap/obsidian-cli-ops` → `obs research --help` works (the gap closes). *(v4.0.0)*
- [x] CHANGELOG explicitly scopes v4.0.0 = research+config+MCP+retirement; states 5.1/5.3 deferred to v4.1/v4.2. *(`docs_mkdocs/changelog.md`; v4.0.1 section added)*
- [x] `.STATUS` + `IDEAS.md` corrected (retirement done; `--apply` not inert; re-stamped). *(re-stamped to v4.0.1)*
- [ ] `ci.yml` gains `--cov-fail-under` (value TBD by current real %). **← only open item; tracked in `.STATUS` next.**
- [x] Tap formula auto-bumped by `homebrew-release.yml`; `brew audit --strict` clean; `brew reinstall --build-from-source` db-init clean (the release gate). *(v4.0.0 + v4.0.1; v4.0.1 sha256 verified == tarball)*

## 5. Risks

- **Single biggest:** none blocks shipping. The MCP `nexus`→`obsidian-ops` client-key migration is the only breaking item, and the TS server repo is *already archived* — so it's a client-config comms note, not code work.
- **5.1 mis-scope (content risk): RESOLVED** — delegate was chosen by **explicit sign-off** (2026-06-22, §1), not silently assumed. D3 is formally amended and the offline regression is accepted/documented, so this risk is retired. The residual carry-over: the v4.1 changelog must state the offline-CRUD regression plainly so users aren't surprised.
- **Coverage gate:** setting `--cov-fail-under` too high vs the unmeasured real % could red the build — measure first, then set the floor at-or-below current.

## 6. Documentation & Discoverability

- [x] CHANGELOG `[Unreleased]`→v4.0.0 section + count bumps (commands/MCP tools/tests). *(+ v4.0.1 section, 2026-06-23)*
- [x] mkdocs: `obs research` + `obs config` reference pages already exist (PR #38) — flip any "unreleased/Phase 1" annotations to "shipped in v4.0.0".
- [x] README badge + headline counts → v4.0.x; released-vs-branch convention refreshed (branch == released after the cut).
- [x] Migration note for MCP clients: `nexus` key retired → `obsidian-ops`.
- [x] `validate-counts` / docs-staleness clean post-bump. *(now CI-gated via `core/doc_counts.py` + floor gate, PR #50)*
- [x] N/A: no new tutorial needed for the bump (research pages exist); add one only if 5.1 ships new CLI verbs.

---

## 7. Landing this spec

**Landed 2026-06-22** on `feature/spec-next-overhaul` (off `dev`) → PR to `dev`, per branch protection (`main` is PR-only; new `.md` files need a `feature/*` branch). The 5.1 build-vs-delegate fork (§1) was resolved to **delegate** before landing. Open follow-ups now tracked in `.STATUS`/`IDEAS.md`: ship **v4.0.0** (keystone), then **5.1 delegate bridge** (v4.1) and **5.3 PARA validator** (v4.2).
