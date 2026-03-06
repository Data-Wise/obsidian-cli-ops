# Changelog

All notable changes to Obsidian CLI Ops.

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
