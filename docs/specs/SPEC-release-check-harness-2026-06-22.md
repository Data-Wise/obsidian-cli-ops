# SPEC — Release-Check Harness (post-install + count/caveats currency)

**Status:** DRAFT — brainstorm output (deep mode, 4 decisions captured)
**Date:** 2026-06-22
**Owner:** @dtofighi
**Branch model:** work on `dev`; new `.md` allowed on `dev`, new code files on `feature/*`
**Motivated by:** the v4.0.0 release (shipped 2026-06-22) silently shipped a **25→38 MCP-tool undercount** and **generic/stale Homebrew caveats** — neither caught by any gate.

> **One-line:** obs has *version*-consistency gates but no *count*-consistency, *caveats-currency*, or *post-install* gates. Adopt craft's validator **patterns** (reshaped for the Python/ZSH layout), wire the count gate into **both `obs doctor` and CI (pytest)**, and **assert-current** the Homebrew caveats — so counts and post-install notes can never drift into a release again.

---

## 0. What v4.0.0 proved (the lived gaps)

| Symptom in v4.0.0 | Root cause | Craft pattern that prevents it |
|---|---|---|
| Docs said "25 MCP tools"; `mcp_server.py` has **38** (`grep -c @mcp.tool`) | No count-consistency check anywhere | `validate-counts.sh` (count from source-of-truth, assert docs match) |
| Homebrew caveats were generic — no new commands, no MCP/restart note until hand-edited | Release Step 10 only bumps `url`+`sha256`; caveats hand-maintained, ungated | `dist:homebrew` caveats + an assert step |
| No check that the *installed* formula's tool count / caveats match reality | No post-install verification beyond db-init | `verify-surfaces.sh` + `brew reinstall --build-from-source` |
| Research MCP tools (13) undocumented in `MCP_README` tool tables | Doc tables hand-maintained, no coverage gate | `doc-coverage-check.sh` analogue |

**obs already has** (keep, build alongside): `test_version_consistency.py` (6 gates: obs.zsh⇄pyproject/package.json/__init__/CLAUDE.md/obs.test.js), `man-page-version-sync.test.js` (`.TH` ⇄ package.json), `obs doctor` (5-layer diagnostic), the `mcp-tool-resolvers` AST check.

**obs lacks:** a `scripts/` directory entirely. This harness creates it.

---

## 1. Decisions (locked this brainstorm)

| # | Decision | Choice |
|---|---|---|
| D1 | Scope | **Adopt craft scripts wholesale** — vendor + reshape `validate-counts.sh` / `verify-surfaces.sh` / `post-release-sweep.sh` into `obs/scripts/`, stripping plugin-structure assumptions and re-pointing at obs's source-of-truth. |
| D2 | Count-gate location | **Both** — `obs doctor` gets a `doc-counts` check (user-facing) **and** a CI-gated `test_doc_counts.py` (drift can't merge). Belt-and-suspenders, mirrors the version-consistency pattern. |
| D3 | Caveats strategy | **Assert-current** — a check (release step + CI) verifies the tap formula caveats name the right counts/commands; fails if stale. Caveats stay hand-written but guarded. (Not codegen — the tap is a separate repo; lower risk.) |
| D4 | Live 25→38 drift | **Patch now** (Phase 0), then build the harness so it can't recur. |

---

## 2. obs source-of-truth map (what the validators count)

The reshape's core: craft counts `commands/*.md` + `SKILL.md`; obs counts **code**, not files.

| Metric | Source of truth (authoritative) | Surfaces that must match |
|---|---|---|
| MCP tools | `grep -c '@mcp.tool' src/python/mcp_server.py` (currently **38**) | MCP_README (header + table + arch), index.md, claude-integration.md, refcard.md, cli-reference.md, architecture.md, api-reference.md, testing/overview.md, tutorials, CLAUDE.md, .STATUS, **tap caveats** |
| MCP resources | `grep -c '@mcp.resource' src/python/mcp_server.py` (4) | same |
| `obs` commands | dispatcher cases in `src/obs.zsh` + argparse subparsers in `obs_cli.py` | README, CLAUDE.md, refcard, cli-reference, .STATUS |
| AI providers | `ai/providers/` modules (5) | docs headers |
| Version | `obs.zsh VERSION=` (already gated) | — (existing) |

**Reshape note:** craft scripts `source formatting.sh` and assume `PLUGIN_DIR`. The obs ports drop both — use plain ANSI + `git rev-parse --show-toplevel`. Keep the **output format** (one-line-per-surface, traffic-light) for familiarity.

---

## 3. Components & phasing

### Phase 0 — Hotfix the live drift (NOW, `docs(mcp)` on dev)
- `25 → 38` MCP-tool count across all doc surfaces (precise phrase targeting, not blind replace).
- **Document the 13 research tools** in `MCP_README.md` (new "Research Tools" table: `unified_search`, `zotero_search/get/recent/cite`, `pdf_search`, `course_list/show/lectures`, `manuscript_list/show/stats`, `bib_check`).
- `architecture.md` group breakdown → add "Research (13)" → "**38** MCP tools in **10** groups".
- `testing/overview.md`: "90 MCP tests" → **113**.
- Tap caveats already corrected to 38 this session (`5b8034d`).
- **Acceptance:** `grep -rn '25 .*tools' docs/ docs_mkdocs/ *.md | grep -vi historical` returns 0; full suite green.

### Phase 1 — `scripts/validate-counts.sh` (the keystone) — `feature/release-harness`
- Reshape craft's `validate-counts.sh`: count `@mcp.tool`/`@mcp.resource` from `mcp_server.py`, `obs` subcommands from `obs.zsh`, AI providers; grep the surface docs for the claimed numbers; report mismatches; exit 1 on drift.
- `--quiet` (exit code only, for hooks/CI), `--fix` (optional, mechanical number swaps in flagged files).

### Phase 2 — Count gate, two surfaces (D2)
- **`obs doctor` `doc-counts` check** (new, under a `docs` layer or the existing structure): runs `validate-counts` logic in-process; WARN on drift with the offending files. User-facing, runs anytime.
- **`test_doc_counts.py`** (mirrors `test_version_consistency.py`): asserts each surface's MCP-tool/command count == source-of-truth. **CI-gated → drift cannot merge.**

### Phase 3 — Caveats assert-current (D3)
- `scripts/verify-caveats.sh` (reshape of `verify-surfaces.sh` idea): fetch the tap formula caveats (`gh api … Formula/obsidian-cli-ops.rb`), assert they mention the current MCP-tool count + the latest-release commands. Fails (release-blocking) on staleness; warn in plain CI.
- Wire into the obs release runbook (§5) as a pre-tag step.

### Phase 4 — Post-install verification (reshape `verify-surfaces.sh` + build-from-source)
- `scripts/post-install-check.sh`: after `brew install/upgrade`, assert (a) `obs version` == release, (b) `obs doctor` exits clean (db-init worked — the known real gate), (c) the installed `mcp_server.py` `@mcp.tool` count == documented, (d) tap formula `url`/`sha256` resolve. Encodes the `brew reinstall --build-from-source` lesson (audit-green ≠ installs clean) from project memory.

### Phase 5 — `scripts/post-release-sweep.sh` (reshape)
- Tier-2 drift after a release: secondary version refs, stale counts, CHANGELOG⇄index currency. `--fix` for mechanical items. Run as release Step 13.5 analogue.

---

## 4. Sequencing

```
 Phase 0 (NOW)        Phase 1            Phase 2            Phase 3-4-5
 ┌────────────┐   ┌──────────────┐   ┌──────────────┐   ┌──────────────┐
 │ hotfix     │ → │ validate-    │ → │ doctor check │ → │ caveats-     │
 │ 25→38 +    │   │ counts.sh    │   │ + pytest CI  │   │ assert +     │
 │ doc 13     │   │ (keystone)   │   │ gate (D2)    │   │ post-install │
 │ research   │   └──────────────┘   └──────────────┘   │ + sweep      │
 └────────────┘                                          └──────────────┘
  docs(mcp), dev    new scripts/, feature branch (code)   release runbook
```

Phase 0 is docs-only (dev). Phases 1–5 add **code** → `feature/release-harness` worktree off dev (branch-guard blocks new code files on dev).

## 5. Risks

- **Count-phrase false positives** — "25" appears in non-tool contexts (dates, percentages). Mitigate: validator matches anchored phrases (`N MCP tools`, `Tools:** N`, `Available Tools (N)`), never bare `N`. Maintain an explicit surface list, not a repo-wide grep.
- **Reshape drift from craft** — vendored scripts fork from upstream craft. Accept: obs is not a craft plugin; one-time adaptation, no ongoing sync. Document provenance in each script header.
- **Tap is a separate repo** — caveats assert (Phase 3) reads the tap via `gh api`; needs the formula pushed first. Order in runbook: release → formula auto-bump → assert-caveats.
- **Over-gating CI** — a too-strict count test could red the build on a benign doc edit. Mitigate: the test asserts *documented == source*, and `--fix` makes realignment one command.

## 6. Acceptance criteria

- [ ] Phase 0: 0 stale "25 … tools" in current docs; research tools documented; suite green.
- [ ] `scripts/validate-counts.sh` exits 1 on an injected drift, 0 when aligned.
- [ ] `obs doctor` shows a `doc-counts` check; `test_doc_counts.py` fails on injected drift (proves the gate).
- [ ] `verify-caveats.sh` flags a deliberately-stale caveats block.
- [ ] `post-install-check.sh` passes against a real `brew reinstall --build-from-source`.
- [ ] Release runbook (CLAUDE.md / a RELEASING.md) references the new gates in order.

## 7. Documentation & Discoverability

- [ ] `obs doctor --help` lists the `doc-counts` check; troubleshooting rule entry.
- [ ] `docs_mkdocs/developer/` page documenting the release-check harness + how to run each script.
- [ ] CLAUDE.md "Releasing" section (workflows.md) updated with the gate order (validate-counts → caveats-assert → post-install).
- [ ] `.STATUS` next: points at this spec; CHANGELOG notes the harness when it ships.
- [ ] Memory: record the count-drift class + the validate-counts pattern (link [[v4.0.0-release-nexus-absorption]]).

## 8. Landing

DRAFT on `dev` (docs/specs/). Phase 0 executes immediately as `docs(mcp)` on dev. Phases 1–5 need `feature/release-harness` (new code files). Reuses craft's **patterns**, not its plumbing — obs stays craft-independent.
