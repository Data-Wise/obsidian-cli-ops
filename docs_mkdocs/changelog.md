# Changelog

All notable changes to Obsidian CLI Ops.

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
