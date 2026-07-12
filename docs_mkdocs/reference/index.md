# Reference

Every reference page in one place — commands, flags, providers, MCP tools, schemas, and changelog.

---

## Quick Reference Card

[![Quick Reference Card](../refcard.md)](../refcard.md){ .md-button }
A printable cheat sheet covering every `obs` command, MCP tool, AI provider,
and workflow — all on one page.

| Section | What's inside |
|---------|---------------|
| Core commands | `obs`, `search`, `stats`, `scan`, `analyze`, `health` |
| Monitoring & diagnostics | `bridge`, `trends`, `stale`, `daily-digest`, `doctor`, `board` |
| AI commands | All 13 AI subcommands from `status` to `quality` |
| Config | `show`, `validate`, `migrate`, `init`, `edit` |
| Research | Zotero, PDF, courses, manuscripts, bibliography |
| MCP tools | 42 tools in 10 groups |
| Native Obsidian CLI | Side-by-side comparison |

---

## In-Depth References

| Page | What it covers |
|------|----------------|
| [CLI Reference](../cli-reference.md) | Full command syntax with all flags, options, and examples |
| [Visual Workflows](../workflows.md) | Decision flowcharts — which command to run for each task |
| [AI Setup Guide](../ai-setup.md) | Provider installation, API keys, and configuration |
| [Claude Integration](../claude-integration.md) | MCP server setup for Claude Desktop, Claude Code, and Cowork |
| [Changelog](../changelog.md) | Version history with all additions, fixes, and changes |

---

## Quick Links by Category

### Vault Management

| Command | Refcard | CLI Reference |
|---------|---------|---------------|
| `obs` / `obs vaults` | [List vaults](../refcard.md#core-commands) | [CLI details](../cli-reference.md#vault-management) |
| `obs discover` | [Find vaults](../refcard.md) | [Full syntax](../cli-reference.md#obs-discover) |
| `obs scan` | [Scan vault](../refcard.md) | [--prune docs](../cli-reference.md#obs-scan) |
| `obs stats` | [Show stats](../refcard.md) | [Examples](../cli-reference.md#obs-stats) |
| `obs vault info` | [Metadata](../refcard.md#vault-lookup) | [Details](../cli-reference.md#obs-vault-info) |
| `obs vault rename` | — | [Rename rules](../cli-reference.md#obs-vault-rename) |
| `obs vault delete` | — | [Safety notes](../cli-reference.md#obs-vault-delete) |

### Graph & Health

| Command | Refcard | CLI Reference |
|---------|---------|---------------|
| `obs analyze` | [Graph metrics](../refcard.md) | [Details](../cli-reference.md#graph-analysis) |
| `obs health` | [Health dashboard](../refcard.md) | [4 dimensions](../cli-reference.md#obs-health) |
| `obs doctor` | [Diagnostics](../refcard.md#monitoring-diagnostics) | [7 layers](../cli-reference.md#obs-doctor) |

### Board Management

| Command | Refcard | CLI Reference |
|---------|---------|---------------|
| `obs board refresh` | [Refresh board](../refcard.md#monitoring-diagnostics) | [--vault/--all/--dry-run](../cli-reference.md#board-management) |
| `obs board status` | [Board status](../refcard.md#monitoring-diagnostics) | [--vault/--all/--json](../cli-reference.md#board-management) |

### AI

| Command | Refcard | CLI Reference |
|---------|---------|---------------|
| All 13 subcommands | [AI section](../refcard.md#ai-commands) | [Full details](../cli-reference.md#ai-features) |

### Research

| Command | Refcard | CLI Reference |
|---------|---------|---------------|
| Zotero, PDF, courses, manuscripts, bib | [Research section](../refcard.md#research-commands) | [Research domain](../cli-reference.md#research-domain) |

### MCP Tools

| Toolset | Refcard | Integration |
|---------|---------|-------------|
| 42 tools in 10 groups | [MCP table](../refcard.md#claude-mcp-tools) | [Setup guide](../claude-integration.md) |

---

**Version:** 4.3.0 | **Last updated:** 2026-07-01
