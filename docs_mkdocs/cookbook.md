# Cookbook

Practical recipes for common vault management tasks.

---

## Getting Started

### First-time setup

```bash
# Install
brew install data-wise/tap/obsidian-cli-ops

# Initialize the database
python3 src/python/obs_cli.py db init

# Discover and scan vaults in one step
obs discover ~/Documents --scan

# Check what was found
obs
```

### Discover vaults from iCloud

```bash
obs discover ~/Library/Mobile\ Documents/iCloud~md~obsidian/Documents --scan
```

obs also auto-checks this location when you run `obs` with no arguments.

### Scan an existing vault

```bash
# Scan by path (first time)
obs scan /path/to/your/vault

# Re-scan to pick up new notes
obs scan /path/to/your/vault
```

Scanning reads all markdown files, extracts wikilinks, tags, and metadata into the knowledge graph.

---

## Vault Health & Cleanup

### Run a full health check

```bash
obs analyze MyVault        # Graph metrics (density, clusters)
obs health MyVault         # Health scores (4 dimensions)
obs ai gaps MyVault        # Knowledge gaps
obs ai refactor MyVault    # Reorganization plan
```

### Find and organize orphaned notes

Orphaned notes have no incoming or outgoing links. They're invisible to graph navigation.

```bash
# See orphan count
obs health MyVault

# Get AI-powered reorganization plan
obs ai refactor MyVault

# Preview scope first (no AI calls)
obs ai refactor MyVault --dry-run
```

**What to do with orphans:**

- Link them to relevant hub notes or MOCs (Maps of Content)
- Some orphans are fine (daily notes, templates)
- High orphan count (>20%) suggests poor linking habits

### Archive stale folders

The refactor command detects folders where all notes are >90 days old with low connectivity:

```bash
obs ai refactor MyVault --json | python3 -c "
import json, sys
plan = json.load(sys.stdin)
for s in plan['suggestions']:
    if s['category'] == 'archive':
        print(f\"Archive: {s['affected_paths']}\")
"
```

### Consolidate small folders

Folders with fewer than 3 notes are flagged for merging:

```bash
obs ai refactor MyVault --json | python3 -c "
import json, sys
plan = json.load(sys.stdin)
for s in plan['suggestions']:
    if s['category'] == 'merge-folder':
        print(s['description'])
"
```

---

## Knowledge Graph Analysis

### Understand graph density

Run `obs analyze MyVault` and check the density value:

| Density | Interpretation |
|---------|---------------|
| < 0.01 | Sparse -- many isolated notes |
| 0.01-0.05 | Typical -- healthy vault |
| 0.05-0.10 | Dense -- well-connected |
| > 0.10 | Very dense -- may have over-linking |

### Find hub notes (most connected)

```bash
obs analyze MyVault --verbose
```

Hub notes are the backbone of your knowledge graph. Review them regularly -- they influence many notes. Consider splitting hubs with 50+ connections.

### Understand clusters

Clusters are groups of notes more connected to each other than to the rest. The cluster count in `obs analyze` output tells you how many topic communities exist:

- Very few clusters (1-2): vault may lack structure
- Many small clusters: topics may not be cross-linked enough
- Each cluster typically represents a topic or project

### Export graph data for external tools

```bash
# All stats as JSON
obs stats --vault MyVault --json > vault_stats.json

# Health scores as JSON
obs health MyVault --json > health.json

# Refactor plan as JSON
obs ai refactor MyVault --json > refactor_plan.json
```

### Track changes over time

Re-scan and re-analyze periodically:

```bash
obs scan /path/to/vault && obs analyze MyVault -v
```

Watch for: orphan count increasing, broken links growing, density increasing (good), new clusters forming.

---

## AI-Powered Discovery

### Set up AI providers

```bash
# Check what's available
obs ai status

# Run the interactive wizard
obs ai setup

# Test all providers
obs ai test
```

**Quick options:**

- **Fastest (no install):** Use `gemini-cli` or `claude-cli` if you have them
- **Most private:** Use `ollama` for 100% local processing
- **Best quality:** Use `gemini-api` or `anthropic-api` with an API key

### Find related notes you forgot about

```bash
# Find notes similar to a specific note
obs ai similar <note_id> --limit 5

# Suggest links you're missing
obs ai suggest-links <note_id>
```

### Analyze a note in depth

```bash
obs ai analyze <note_id>
```

Returns topics, themes, quality scores, and improvement suggestions.

### Detect duplicate content

```bash
# Scan entire vault
obs ai duplicates MyVault

# Lower threshold catches more near-duplicates
obs ai duplicates MyVault --threshold 0.75
```

Review each pair -- high similarity doesn't always mean duplicate.

### Find knowledge gaps

```bash
obs ai gaps MyVault
```

Detects stub notes (referenced often but underdeveloped), orphaned notes, and structural gaps.

### Get vault-wide themes

```bash
# Full vault summary
obs ai summarize MyVault

# Scoped to a folder
obs ai summarize MyVault --folder "projects/"

# Scoped to a tag
obs ai summarize MyVault --tag "python"
```

### Get reorganization suggestions

```bash
# Full analysis with AI
obs ai refactor MyVault

# Preview scope without AI calls
obs ai refactor MyVault --dry-run

# Machine-readable output
obs ai refactor MyVault --json
```

Suggestion categories: `move` (unsorted notes), `archive` (stale folders), `merge-folder` (small folders), `create-folder` (scattered tags), `connect` (orphans near clusters).

---

## Multi-Vault Management

### Discover all vaults on your system

```bash
# Standard locations
obs discover ~/Documents --scan
obs discover ~/Library/Mobile\ Documents/iCloud~md~obsidian/Documents --scan

# List everything found
obs
```

### Compare vault health across vaults

```bash
for vault in MyVault WorkNotes Research; do
    echo "=== $vault ==="
    obs health "$vault" --json | python3 -c "
import json, sys
h = json.load(sys.stdin)
print(f\"  Overall: {h['overall']}/100\")
"
done
```

---

## Scripting & Automation

### JSON output for all data commands

Most commands support `--json`:

```bash
obs stats --json                          # Global stats
obs stats --vault MyVault --json          # Vault stats
obs health MyVault --json                 # Health scores
obs analyze MyVault --json                # Graph metrics
obs ai refactor MyVault --json            # Refactor plan
obs ai duplicates MyVault --json          # Duplicate groups
obs ai suggest-links <note_id> --json     # Link suggestions
obs ai gaps MyVault --json                # Knowledge gaps
obs ai summarize MyVault --json           # Vault summary
```

### Pipe refactor suggestions to a checklist

```bash
obs ai refactor MyVault --json | python3 -c "
import json, sys
plan = json.load(sys.stdin)
for s in plan['suggestions']:
    priority = {'high': '!!!', 'medium': '!!', 'low': '!'}[s['priority']]
    print(f'- [ ] {priority} {s[\"description\"]}')
" > vault_cleanup_tasks.md
```

---

## Next Steps

- [CLI Reference](cli-reference.md) -- Full command documentation
- [AI Setup Guide](ai-setup.md) -- Configure AI providers
