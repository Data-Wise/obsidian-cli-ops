# Cookbook

Practical recipes for common vault management tasks.

---

## Vault Cleanup

### Find and organize orphaned notes

```bash
# See orphan count
obs health MyVault

# Get AI-powered reorganization plan
obs ai refactor MyVault

# Preview scope first (no AI calls)
obs ai refactor MyVault --dry-run
```

### Archive stale folders

The refactor command automatically detects folders where all notes are >90 days old and have low connectivity:

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

### Full vault health check

```bash
obs analyze MyVault        # Graph metrics
obs health MyVault         # Health scores
obs ai gaps MyVault        # Knowledge gaps
obs ai refactor MyVault    # Reorganization plan
```

### Find your most important notes

```bash
obs analyze MyVault --verbose
```

The verbose output shows hub notes (most connected) and orphans.

### Export graph data for external tools

```bash
# All stats as JSON
obs stats --vault MyVault --json > vault_stats.json

# Health scores as JSON
obs health MyVault --json > health.json

# Refactor plan as JSON
obs ai refactor MyVault --json > refactor_plan.json
```

---

## AI-Powered Discovery

### Find related notes you forgot about

```bash
# Find notes similar to a specific note
obs ai similar <note_id> --limit 5

# Suggest links you're missing
obs ai suggest-links <note_id>
```

### Detect duplicate content

```bash
# Scan entire vault
obs ai duplicates MyVault

# Lower threshold catches more near-duplicates
obs ai duplicates MyVault --threshold 0.75
```

### Get vault-wide themes

```bash
# Full vault summary
obs ai summarize MyVault

# Scoped to a folder
obs ai summarize MyVault --folder "projects/"

# Scoped to a tag
obs ai summarize MyVault --tag "python"
```

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
