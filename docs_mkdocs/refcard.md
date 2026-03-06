# Quick Reference Card

All `obs` commands at a glance. Print this page or keep it open as a cheat sheet.

---

## Core Commands

| Command | Description |
|---------|-------------|
| `obs` | List all registered vaults |
| `obs stats [vault]` | Show vault or global statistics |
| `obs discover <path>` | Find Obsidian vaults in a directory |
| `obs analyze <vault>` | Analyze vault graph metrics |
| `obs health <vault>` | Vault health dashboard (scores + recommendations) |

## AI Commands

| Command | Description |
|---------|-------------|
| `obs ai status` | Show AI provider availability |
| `obs ai setup` | Interactive provider setup wizard |
| `obs ai test` | Test all AI provider connections |
| `obs ai similar <note_id>` | Find semantically similar notes |
| `obs ai analyze <note_id>` | Deep AI analysis of a note |
| `obs ai duplicates <vault>` | Detect potential duplicate notes |
| `obs ai suggest-links <note_id>` | Suggest new links based on similarity |
| `obs ai gaps <vault>` | Find knowledge gaps in the vault |
| `obs ai summarize <vault>` | Summarize vault themes and stats |
| `obs ai refactor <vault>` | AI-powered vault reorganization suggestions |

## Utilities

| Command | Description |
|---------|-------------|
| `obs help` | Quick help (essential commands) |
| `obs help --all` | Full command reference |
| `obs version` | Show version |

## Global Flags

| Flag | Description |
|------|-------------|
| `--verbose` / `-v` | Enable verbose output |
| `--json` | Output as JSON (where supported) |

## AI Refactor Flags

| Flag | Description |
|------|-------------|
| `--dry-run` | Show scope without AI calls |
| `--provider NAME` | Force a specific AI provider |
| `--json` | Machine-readable JSON output |

## Vault Lookup

Commands accepting `<vault>` support flexible lookup:

```bash
obs stats MyVault        # By name
obs stats a812           # By ID prefix
obs analyze Research_Lab # By name
```

## AI Provider Priority

Auto-selection order (first available wins):

1. `gemini-api` (fastest, needs API key)
2. `anthropic-api` (highest quality, needs API key)
3. `ollama` (local, private)
4. `gemini-cli` (free, no API key)
5. `claude-cli` (free, no API key)

Override with `--provider`:

```bash
obs ai similar <note_id> --provider ollama
obs ai refactor MyVault --provider anthropic-api
```

## Common Workflows

```bash
# First-time setup
pip3 install -r src/python/requirements.txt
python3 src/python/obs_cli.py db init
obs discover ~/Documents --scan

# Daily check
obs
obs health MyVault

# AI analysis
obs ai status
obs ai refactor MyVault --dry-run
obs ai refactor MyVault

# Export for scripting
obs stats --vault MyVault --json
obs ai refactor MyVault --json | python3 -m json.tool
```

---

**Version:** 3.0.0 | **Commands:** 15 | **AI Providers:** 5
