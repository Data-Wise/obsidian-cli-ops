# Changelog

All notable changes to Obsidian CLI Ops.

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
