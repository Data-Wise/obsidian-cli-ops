# Changelog

All notable changes to Obsidian CLI Ops.

---

## [Unreleased]

### Docs gap audit (2026-07-12)

- **Architecture docs updated** — added Config File Contracts section documenting the `.flow/obsidian-sync.yml` vault↔repo mirror map (vault-rooted, v4.3.0).
- **Testing overview fixed** — added 5 missing test files to the inventory table (`flow_init` 36, `flow_dogfood` 19, `research_board` 8, `db_manager` 8, `obs_link` 5→removed); unit subtotal 342 → 413; Jest subtotal 69 → 70.
- **Architecture testing section fixed** — 450+ pytest → 764 pytest; 69 Jest → 70 Jest.
- **refcard.md updated** — added `obs flow init` and `obs doctor --layer flow` to the "Other" section.
- **Removed `.obs/sync.yml` / `obs link` (ADR-001)** — deleted `research/obs_link.py`, `tests/test_obs_link.py`, `docs_mkdocs/obs-sync-yml.md`; removed `obs link` CLI subcommand and zsh dispatcher; `.flow/obsidian-sync.yml` is now the sole vault↔repo mirror-map contract.
- **New `design-standards.md`** — contributor-facing reference for the three convention-driven surfaces: local config file contracts (`.flow/obsidian-sync.yml`), their create/validate command pairs (`obs flow init` / `obs doctor --layer flow`), and Obsidian dashboards (`obs research board` / `obs board refresh`); wired into `mkdocs.yml` Reference nav with a "new surface" PR checklist.

### Docs website redesign & brand system (2026-07-12)

- **Palette + typography** — replaced Material's default indigo/purple with a fixed ink `#15161a` / paper `#f7f6f2` / teal `#0d9488` system via `docs_mkdocs/stylesheets/redesign.css` (Space Grotesk + JetBrains Mono, no Inter, 4px radii).
- **Logo & favicon** — new "Node Cartography" mark (faceted obsidian diamond hub + note nodes) wired into `mkdocs.yml` `theme.logo` / `theme.favicon` (transparent mark so it reads on the ink header); assets in `docs/proposals/brand/` + `docs_mkdocs/assets/`.
- **Proposal artifact** — the interactive audit + before/after mockup is preserved as a self-contained `docs_mkdocs/proposals/docs-redesign.html` (JS+CSS inlined, mark embedded as a base64 data URI, zero external refs), linked from `design-standards.md` §6.
- **Planning record** — `docs/specs/SPEC-docs-redesign-2026-07-12.md` documents the decisions and the bundle-rebuild workflow for future redesign passes.
- **Navigation regroup** — the 13-item "Tutorials & Cookbook" menu is now split into sub-sections (Getting Started, Vault, Graph, AI, Research, Flow & Diagnostics) with Cookbook kept top-level; Reference's AI Setup Guide + Claude Integration are grouped under "AI & MCP". No pages added or removed.

## v4.3.0 (2026-07-01) — Board sync automation + E2E dogfood

### Board sync automation

#### Added

- **`obs board refresh`** — multi-source board engine that reads from atlas
  (`atlas project list`), vault DB (ghost drift detection), and `.STATUS` files
  (YAML + fallback line parser), then merges into a deterministic `_ACTION-BOARD.md`
  with heuristic-ranked action items and status tables.
- **`obs board status`** — check whether `_ACTION-BOARD.md` exists, when it was
  last refreshed, and whether the vault has ghost drift.
- **`scripts/board-refresh.sh`** — weekly cron shell script with Python path
  resolver (3-candidate chain matching `obs.zsh` priority), intended for launchd
  automation.
- **`core/board.py`** — 535-line engine with 5 components: `AtlasConnector`,
  `StatusConnector` (PyYAML with fallback), `VaultConnector`, `Merger`,
  `BoardRenderer` (action ranking, progress bars, status icons), and `VaultWriter`
  (marker-aware ± full-file overwrite).

### E2E dogfood expansion

#### Added

- New test classes: `TestE2ENoteLinks`, `TestE2EDogfoodCLI`, `TestE2EMiscTools`
- New MCP tool coverage: `write_note`, `rename_note`, `get_note_links`
  (outgoing/incoming/orphan), `insert_to_note`, `server_info`,
  `get_bridge_status`, `get_trends`, `get_stale_notes`, `get_daily_digest`,
  `diagnose`, `unified_search`
- New CLI subprocess tests: `doctor`, `health`, `analyze`, `search`, `vaults`, `stats`
- New edge cases: `create_note` subfolder, duplicate guard, negative limits,
  unicode queries, empty vault_id, path traversal, unknown vault

#### Fixed

- `test_delete_confirm_removes_file`: title slugification mismatch (spaces→hyphens
  in filenames broke file lookup)
- `create_note` E2E tests: content heading must match `title` param for
  `search_notes` to find the note; `rescan_vault` required after creation for DB indexing
- `import json` shadowing in `obs_cli.py` that broke `obs doctor --layer sync --json`

#### Changed

- E2E test count: 32 → 71 (all passing, 0 skips)
- Doc counts synced via `scripts/validate-counts.sh --fix`

### Release-prep fixes (2026-07-01)

Follow-up pass closing gaps found before the v4.3.0 GitHub release was cut.

#### Added

- `obs board refresh`/`obs board status` wired into the `src/obs.zsh` shell
  dispatcher — previously reachable only via the raw `python3 obs_cli.py` path
- `obs board`/`research board` listed in `obs help --all`
- `obs research learn`, `obs config validate`, `obs config migrate` documented
  with runnable examples (were CLI-reference-only, no tutorial coverage)
- `docs/planning/README.md` updated with the `specs-completed/` archive
  convention and a SPEC-lifecycle rule mirroring the existing
  ORCHESTRATE-deletion convention

#### Fixed

- Command count corrected 62 → 63 across `CLAUDE.md`, `cli-reference.md`,
  `refcard.md` (`obs research learn` had landed after the count was last set)
- Version strings corrected 4.2.0 → 4.3.0 across 14 files (`obs.zsh`,
  `pyproject.toml`, `package.json`, man page, tests) — the in-repo version bump
  for this release had been incomplete
- MCP Tool Groups section in `cli-reference.md` completed (6 → 10 groups) to
  match `refcard.md`
- Stale anchor link (`refcard.md#claude-mcp-tools-v330`) broken by the above fix

#### Removed

- 34 stale/already-shipped branches (local + remote) whose content had landed
  via squash-merge but were never cleaned up
- Stray `ORCHESTRATE-*.md` working artifacts that leaked onto `dev` from
  merged PRs

## v4.2.0 (2026-06-26) — Vault ↔ index sync reconciliation

### Vault ↔ index sync reconciliation

#### Added

- **`obs scan --prune` / `--no-prune`** — opt-in mark-and-sweep that reconciles the index
  with disk. After scanning, rows whose path is gone from disk (notes deleted or renamed)
  are swept, cascading to their links, tags, graph metrics, and embeddings (S1/S2). Default
  stays **additive** (`--no-prune`). A scan that sees zero files skips the sweep with a
  warning rather than wiping the index (bad-path / un-materialised-iCloud guard).
- **MCP `rescan_vault(vault_id, prune=False)`** — gains the same opt-in `prune` parameter.
- **`obs doctor --layer sync`** — new per-vault sync layer giving content-based (not just
  time-based) drift visibility: `sync-ghosts` (rows whose file is gone), `sync-missing`
  (`*.md` on disk absent from the DB), `sync-errors` (last scan recorded failures), and a
  `sync-drift` summary line (S5).
- Scan summary now reports **unchanged**, **pruned**, and **failed** note counts.
- **`obs doctor` `vault-nesting` check** — warns when one registered vault's path is inside
  another's (e.g. `Documents ⊃ Knowledge_Base`), which double-indexes the child's notes (I1).

#### Changed

- **`templates/` directories are no longer scanned** — `*.md` files inside a `templates`/
  `Templates` directory are Templater scaffolds (invalid-YAML `{{x}}` / `<% %>` frontmatter),
  not knowledge notes; they're skipped like dot-directories rather than counted as scan
  failures (D1). The scanner and `obs doctor --layer sync` share one `is_indexable_md`
  predicate so the index and the sync diff never disagree.

#### Fixed

- **AI embedding cache destroyed on every scan (N1)** — each `obs scan` re-inserted every
  note unconditionally, and the row replace's `ON DELETE CASCADE` wiped each note's
  `note_embeddings` row, forcing a full recompute (latency + paid-API cost) on the next AI
  op. The scanner now compares each file's `content_hash` against the stored one and
  **skips unchanged notes** (N2), preserving embeddings, links, and tags.
- **Silent per-note scan loss (S4)** — a note that failed to parse or insert was swallowed
  by `except Exception: continue` while `complete_scan` hardcoded an error count of 0. Scan
  failures are now counted, captured (path + exception), logged, and surfaced in the scan
  summary and `scan_history`; the scan still completes.
- **Non-string frontmatter tags dropped notes** — a note with a valid-YAML but non-string
  tag element (`tags: [{}]`, `tags: [2024]`) raised `AttributeError` in `_extract_tags` and
  the whole note was dropped from the index (same silent-drop class as the above). Tag
  elements are now normalized (strings stripped, scalars coerced, dict/list/None skipped),
  recovering such notes. Found via dogfood: recovered 18 real notes across two vaults.

---

## v4.1.0 (2026-06-26) — MCP rescan fix, server_info & count gates

### Fixed

- **`rescan_vault` MCP tool crashed on every call** (#62) — the sync handler ran
  `asyncio.run(scan_vault(...))` inside FastMCP's already-running event loop,
  raising `RuntimeError: asyncio.run() cannot be called from a running event
  loop`. The scan never ran, so the obs DB/search index went silently stale
  after every write tool. The handler is now `async def` and `await`s the
  coroutine. A regression test drives the tool inside a live event loop so the
  failure mode can't silently return.
- **Command-count drift** — docs disagreed on the `obs` command total
  (`.STATUS` said 25, refcard 35, cli-reference 40); none matched the code.
  Reconciled every current-state surface to the real count: **45 runnable
  commands** (17 top-level groups, incl. the `obs config` / `obs research`
  families absorbed from nexus-cli).

### Added

- **`obs link`** — create the per-project `.obs/sync.yml` mirror map (docs-standards ADR-001); idempotent. *(Removed in v4.3.1 — superseded by `obs flow init` / `.flow/obsidian-sync.yml`.)*
- **`obs research board`** — deterministic atlas → vault dashboard renderer (manuscripts + programs); marker-bounded atomic write; `--out`, `--kind`, `--dry-run`. [Tutorial](tutorials/research-board.md).
- **`server_info` MCP tool** (#53) — reports the running server's
  `server_version`, `installed_version`, `started_at`, and
  `restart_recommended`. An in-process MCP server keeps the code it loaded at
  startup in memory, so after an upgrade the host can serve stale tool code
  until restarted; `server_info` makes that observable without a restart.
  (Tool count 39 → 40.)
- **`obs doctor` `mcp-async-run` check** (mcp layer) — static AST guard that
  fails if any **sync** `@mcp.tool()` handler calls `asyncio.run()`, so the #62
  bug class cannot recur. Mirrors the existing `mcp-tool-resolvers` guard.
- **Command-count gate** — `core/doc_counts.py` now derives the runnable `obs`
  command count (leaf subcommands) statically from `obs_cli.py` (AST), so it
  joins MCP tools/resources/providers as a gated single source of truth.
  `validate-counts.sh`, `obs doctor --layer docs`, and `test_doc_counts.py` all
  surface it; command-count drift can no longer merge.

### Fixed

- **Scanner: empty/null frontmatter `title:`** no longer crashes the scan with a `NOT NULL` constraint failure on `notes.title` (which silently dropped the note from the index). The title now falls back to the H1 heading or the filename stem (#65; an uncovered case of #51).

---

## v4.0.1 (2026-06-23) — insert_to_note + fixes + release-quality tooling

### Added

- **`insert_to_note` MCP tool** — heading-aware insertion (#40): insert content
  `after_heading`, `before_heading`, `replace_section`, or append as `as_table_row`.
  Uses markdown-it-py AST so headings in fenced code blocks are correctly ignored.
- **`obs scan` verb** — explicit `obs scan <path>` command to rescan a vault without
  running graph analysis; accepts `--name`, `--analyze`, `--check` (#52).
- **Staleness warnings** — `obs analyze`, `obs search`, `obs health` now warn to stderr
  when the vault index is older than 24 h (configurable via `config.yaml`) (#52).
- **Release-check harness** (#50) — `core/doc_counts.py` single-source count gate with
  thin consumers (`validate-counts.sh`, `obs doctor --layer docs`, `test_doc_counts.py`)
  plus release-time `verify-caveats` / `post-install-check` / `post-release-sweep` scripts.
- **Unit-test count gate** — round-down-to-10 floor ("340+ unit") so doc/test-count
  drift is caught in CI without a doc bump on every test added.

### Fixed

- Vault scan no longer crashes on dotfiles (e.g. `.md`) — `_extract_title()` now
  handles the zero-stem edge case with a hash fallback (#51).

### Docs

- `craft:site:audit` remediation: monitoring & diagnostics command reference
  (`bridge status`, `trends`, `stale`, `daily-digest`, `doctor`), TUI/R-Dev removal,
  monitoring/temporal API methods, corrected test counts, monitoring/research tutorials.

---

## v4.0.0 (2026-06-22) — nexus-cli absorption + MCP vault-resolution fix

Major release. Absorbs `nexus-cli` into `obs` (RFC v2 D1=Option A): config unification +
research domain commands, plus the MCP vault-resolution/doctor fix. The `nexus-cli` sibling
is retired and the MCP `nexus` client key is replaced by `obsidian-ops`.

### Added

- **`obs config`** — unified config management at `~/.config/obs/config.yaml`:
  - `obs config show` — print current config and source file
  - `obs config validate` — validate config and report errors
  - `obs config migrate` — convert legacy obs/nexus-cli config to unified YAML
  - `obs config init` — interactive wizard to create a fresh config
  - `obs config edit` — open config in `$EDITOR`
- **`obs research`** — research domain absorbed from nexus-cli (11 subcommands):
  - `obs research zotero search/get/recent` — Zotero library operations
  - `obs research pdf search` — full-text PDF search
  - `obs research course list/show/lectures` — course management
  - `obs research manuscript list/show/stats` — manuscript tracking
  - `obs research bib check` — bibliography citation check
- **Migration guide**: `migration.md` now includes nexus-cli → obs command mapping

### Changed

- `obs config migrate` absorbs nexus-cli config (`~/.config/nexus/config.yaml`) into the unified config file

### Fixed (MCP vault resolution + doctor)

- **MCP vault tools now accept a vault name or ID prefix, not only an exact ID.** Nine tools (`get_vault_stats`, `get_hub_notes`, `get_orphaned_notes`, `get_broken_links`, `analyze_vault`, `list_notes`, `create_note`, `rescan_vault`, `diagnose`) resolved vaults with exact-ID-only `db.get_vault()`, so passing a vault **name** silently returned "Vault not found" — or a misleading empty result (e.g. `get_orphaned_notes` reporting "✅ No orphaned notes!"). They now use 3-tier `get_vault_by_name_or_id()` resolution (name → exact ID → unambiguous prefix). The research tools (`unified_search`, `zotero_*`, `pdf_*`, `course_*`, `manuscript_*`) operate on non-vault sources and were unaffected.
- **`rescan_vault` now actually re-scans the vault.** It previously shelled out to the read-only `obs stats` subcommand — reporting success while never updating the database. It now performs a real in-process `scan_vault(path, name)`.
- **`obs doctor` no longer crashes on real vaults.** The vault layer read a non-existent `last_scan` column (schema column is `last_scanned`), raising `IndexError` whenever any vault was registered. A unit test using a hand-rolled fake schema had masked the bug.

### Added

- **`obs doctor` `mcp-tool-resolvers` check** (mcp layer) — statically AST-scans `mcp_server.py` and fails if any MCP tool resolves a vault with exact-ID-only `db.get_vault()` instead of name/ID/prefix resolution. Guards against the resolver bug class regressing.

---

## v3.5.0 (2026-06-19)

Self-diagnostics release: `obs doctor` command and `diagnose` MCP tool.

### Added

- **`obs doctor`** — five-layer self-diagnostic command covering Python runtime, database integrity, vault health, MCP configuration, and iCloud filesystem status. Returns structured pass/warn/fail/skip results with fix hints. Accepts `--vault`, `--layer` (repeatable), and `--json` flags. Exits 0 on pass/warn, 1 on any fail.
- **`diagnose` MCP tool** (tool #25) — exposes the same diagnostics over the MCP protocol for Claude Desktop integration.
- **`fs_utils.py`** — shared filesystem utility module (`is_icloud_path`, `is_dataless`, `fs_op`, `FS_WRITE_TIMEOUT`, `FS_PROBE_TIMEOUT`) extracted from `mcp_server.py` to enable reuse without circular imports.

---

## v3.4.2 (2026-06-19)

Patch release: two bug fixes discovered during vault dogfood testing.

### Fixed

- **Links column always showed 0 in vault list** — `list_vaults()` queried the `vaults` table directly, which has no `link_count` column; the column now computed via a correlated subquery over `links + notes` (no schema migration required).
- **Vault scan crashed on YAML date frontmatter** — PyYAML parses `created: 2024-01-15` as Python `datetime.date`; `json.dumps()` cannot serialize `date` without a custom encoder. Added `_DateEncoder` to `db_manager.py` so frontmatter with date fields scans without error.

---

## v3.4.1 (2026-06-19)

Patch release: iCloud Drive write-hang fix for MCP server.

### Fixed

- **MCP stdio server blocked on iCloud writes** — file-system operations against iCloud-backed vault paths could block indefinitely, hanging the MCP event loop for the full 4-minute Claude Desktop timeout. Added `_fs_op(fn, timeout)` wrapper using `ThreadPoolExecutor` to enforce a hard deadline on all FS writes; times out with a structured MCP error instead of blocking.

---

## v3.4.0 (2026-06-19)

Bridge + Temporal Analytics + Daily Digest release.

### Added

- **`obs temporal`** — temporal knowledge analytics: growth trends, freshness scoring, activity heatmaps, stale note detection (`obs temporal growth/freshness/heatmap/stale`).
- **`obs bridge`** — integration between `obs` graph analysis and the official Obsidian CLI for note CRUD; lets `obs` identify what to fix, and the native CLI execute it.
- **`obs ai daily-digest`** — AI-generated daily digest of vault activity, linking patterns, and knowledge gaps.

---

## v3.3.0 (2026-06-15)

Claude / MCP integration release. Expands the MCP server from 7 tools to 20 and wires it
into Claude Desktop via a robust venv-aware launcher. No changes to the existing `obs` CLI.

### Added

- **MCP server — 20 tools** (`src/python/mcp_server.py`, 276 → 956 lines):
  - *Vault:* `list_vaults`, `get_vault_stats`, `discover_vaults`
  - *Search:* `search_notes`, `find_similar_notes`
  - *Graph:* `get_hub_notes`, `get_orphaned_notes`, `get_broken_links`, `analyze_vault`
  - *Health:* `get_vault_health` (4-dimension scoring)
  - *Notes (new):* `list_notes`, `read_note`, `write_note`, `create_note`, `append_to_note`, `rename_note`, `delete_note`, `get_note_links`, `rescan_vault`
  - *AI passthrough:* `run_obs_ai` (bridges all `obs ai` subcommands with `--json`)
  - *MCP resources:* `vault://{id}/stats`, `vault://{id}/health`, `obsidian://overview`, `note://{id}`
- **Venv-aware MCP launcher** — `claude_desktop_config.json` uses a 3-candidate zsh resolver; never calls `brew --prefix` (subprocess-in-MCP-env risk eliminated).
- **`mcp==1.27.2`** + 22 transitive deps added to `requirements.lock`, `pyproject.toml`, and Homebrew formula resource blocks. `brew audit --strict` clean.
- **`MCP_README.md`** — comprehensive setup guide, all 20 tools documented.
- **`docs_mkdocs/claude-integration.md`** — MkDocs page for Claude Desktop integration.

### Safety

- `delete_note` defaults to dry-run (`confirm=False`); requires `confirm=True` to actually delete.
- `write_note` creates a `.bak` backup by default.
- `rename_note` warns when other notes link to the renamed note.

---

## v3.2.3 (2026-06-15)

Patch release: new `obs search` command, graph bug fix, stats display fix, and test suite expansion.

### Added

- **`obs search <query>`** — native CLI command for title search across all vaults
  - `--vault` / `-v` to scope to one vault
  - `--limit` / `-n` to cap results (default 20)
  - `--json` for machine-readable output
- **52 MCP unit tests** (`test_mcp_server.py`) — full coverage of all 20 MCP tools + 4 resources; includes unicode, empty inputs, path traversal safety, and server stability edge cases
- **32 E2E dogfood tests** (`tests/e2e/test_e2e_mcp.py`) — real subprocess JSON-RPC; run with `E2E=1 pytest src/python/tests/e2e/ -v`

### Fixed

- **`obs analyze <vault>` cross-vault edge contamination** — graph builder now scopes link queries to the target vault via JOIN on the notes table; graphs for different vaults no longer bleed edges into each other
- **`obs stats <vault>` misleading link count** — now shows internal links and broken links separately (e.g. `Links: 56 (635 broken)`) instead of a single ambiguous total
- **numpy-dependent tests** now skip gracefully under system Python (was erroring at collection time)

### Changed

- **Test counts:** 230 unit pytest + 52 MCP unit pytest + 32 E2E pytest + 69 Jest = **383 total**

---

## v3.2.2 (2026-06-05)

Documentation + bug-fix release. Ships the first `obs` man page and fixes the `--json`/`--verbose` flags on the v3.2.0 AI quality commands.

### Added

- **`man/man1/obs.1`** -- first man page; `man obs` documents the full command surface. Homebrew now installs it (`man1.install`), and `install.sh` symlinks it for from-source installs.
- **Help backfill** -- `obs ai merge-suggest`/`tag-suggest`/`quality` now appear in `obs help --all` (were dispatched but undocumented).
- **Man-page version-sync guard** (`__tests__/man-page-version-sync.test.js`) -- CI fails if the `.TH` version drifts from `package.json`.

### Fixed

- **`obs ai merge-suggest|tag-suggest|quality --json` (and `--verbose`)** -- these are global flags on the Python CLI and must precede the subcommand, but the ZSH handlers appended them *after* it, so `obs_cli.py` rejected them with "unrecognized arguments". The handlers now route global flags ahead of the `ai` token; `--json` output works for all three commands.

### Changed

- Test counts now **235 pytest + 69 Jest (304 total)** (+4 flag-routing regression tests, +6 man-page guard tests).

---

## v3.2.1 (2026-06-04)

Install-reliability release. No command or behavior changes for existing working installs.

### Fixed

- **Clean-install crash** -- `obs` no longer crashes on a fresh install with `ModuleNotFoundError: No module named 'rich'`. Core dependencies are now provisioned into an **isolated virtual environment** (Homebrew `libexec/venv`; `install.sh` -> `~/.local/share/obs/venv`) instead of an ambient interpreter, and survive system-Python upgrades.

### Added

- **`requirements.lock`** -- pinned single source of truth for the 6 core runtime dependencies.
- **4-tier interpreter resolution** (`_obs_resolve_python` in `obs.zsh`) -- `$OBS_PYTHON` -> install.sh user venv -> Homebrew formula venv -> ambient `python3` (with a warning). Never silently trusts a bare `python3` (that was the crash).
- **Clean-install CI smoke test** -- proves a fresh machine runs `obs --help` with zero manual `pip`; guards this regression for all future releases.
- **29 dependency-bootstrapping tests** (`tests/dep_bootstrap.test.js`, 2 network-gated, run in CI).

### Changed

- **`install.sh`** now provisions the isolated venv (idempotent via a lockfile-hash sentinel) in addition to symlinking the launcher.
- Docs updated to the isolated-venv install model; test counts now **235 pytest + 59 Jest (294 total)**.

---

## v3.2.0 (2026-03-09)

### Added

- **`obs ai merge-suggest <vault>`** -- find note pairs with high embedding similarity for potential merging
- **`obs ai tag-suggest <target>`** -- AI-powered tag suggestions for untagged notes (vault-wide or single note)
- **`obs ai quality <target>`** -- score notes on 4 dimensions: completeness, connectivity, metadata, freshness (graph-only, no AI required)
- **`--apply` flag** for tag-suggest -- auto-apply high-confidence tags to YAML frontmatter
- **`--threshold` flag** for merge-suggest -- configurable similarity threshold (default: 0.8)
- **3 new domain models** -- `MergeCandidate`, `TagSuggestion`, `NoteQuality` dataclasses in `ai/models.py`
- **`features_vault.py`** -- new module for vault-level quality features (~500 lines)
- **`features_refactor.py`** -- extracted refactor logic from features.py (~345 lines)
- **29 new tests** -- 14 model tests + 15 vault feature tests (235 pytest total)

### Fixed

- **`obs ai quality --json`** -- flag was silently ignored when passed after target argument (ZSH handler missing flag-consuming loop)

### Changed

- **Module extraction** -- `refactor_vault()` moved to `features_refactor.py` (backward-compatible re-exports)
- **Command count** -- 15 → 18 focused commands
- **Documentation updated** -- architecture, tutorials, cookbook, CLI reference, refcard all reflect v3.2.0

---

## v3.1.0 (2026-03-06)

### Added

- **`obs ai refactor <vault>`** -- AI-powered vault reorganization with 3-phase pipeline (graph-only → AI-enhanced → prioritization)
- **`--dry-run` flag** for refactor -- preview scope without AI calls
- **Quick Reference Card** (`refcard.md`) -- printable command cheat sheet

### Changed

- **Website redesigned** -- simplified from 7 tabs to 4 (Home | Getting Started | Reference | Developer)
- **Hero landing page** with Mermaid architecture diagram and feature highlights
- **Installation guide rewritten** -- Homebrew + manual install methods, removed stale TUI references
- **Configuration guide rewritten** -- AI providers, shell integration, advanced settings
- **Cookbook expanded** -- absorbed tutorial content into task-based recipe format
- **Consolidated changelog** -- replaced 3 individual release pages with single page
- **CLI Reference promoted** to main site navigation

### Fixed

- Missing ZSH wiring for `suggest-links`, `gaps`, `summarize` subcommands
- Dead code in tag-folder analysis loop removed
- Insertion-order bias in orphan placement sampling (now uses `random.sample`)

---

## v3.0.0 (2026-03-05)

Major release: laser-focused vault management with AI-powered graph analysis. Codebase simplified from 11,500 to ~7,400 lines (36% reduction).

### Added

- **Vault Health Dashboard** (`obs health`) -- 4-dimension scoring (connectivity, link integrity, structure, freshness)
- **4 new AI commands**: `suggest-links`, `gaps`, `summarize`, `refactor`
- **Anthropic API provider** -- Claude models alongside Gemini
- **`--json` flag** on all data-outputting commands
- **Vault name/prefix lookup** -- `obs analyze Knowledge_Base` instead of hex IDs
- **Embedding cache** with mtime invalidation in SQLite
- **Obsidian CLI bridge** -- integrates with Obsidian's native CLI for backlinks/orphans

### Changed

- **CLI simplified** from 20+ to 15 focused commands
- **Gemini SDK** migrated from deprecated `google-generativeai` to `google-genai`
- **AI provider routing**: gemini-api > anthropic-api > ollama > gemini-cli > claude-cli

### Removed

- **TUI** (1,701 lines) -- CLI-only for simplicity
- **R-Dev integration** (307 lines) -- belongs in R package ecosystem
- **Legacy v1.x commands** (126 lines) -- plugin install, sync, audit

### Breaking Changes

- `obs switch`, `obs open`, `obs sync`, `obs tui`, `obs r-dev *` removed
- `textual` dependency no longer required
- `google-generativeai` replaced by `google-genai`

---

## v2.2.0 (2025-12-20)

Added complete multi-provider AI system.

### Added

- **6 AI commands**: `similar`, `analyze`, `duplicates`, `status`, `setup`, `test`
- **4 AI providers**: Gemini API, Gemini CLI, Claude CLI, Ollama
- **Smart routing** -- automatic provider selection based on operation type
- **96 new AI tests**

---

## v1.1.0

Added 10 new features including shell completion and verbose mode.

### Added

- `obs list` -- show all configured vaults
- `obs version` -- display version info
- `--verbose` / `-v` flag for debug output
- `NO_COLOR` support
- ZSH and Bash tab completion
- 22 Jest unit tests

### Changed

- `help` and `check` no longer require config file
- Better error messages with command name context
