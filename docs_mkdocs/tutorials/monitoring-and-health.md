# Monitoring & Health

Track your vault's evolution over time — note velocity, stale content, and daily digests — using the temporal tools added in v4.0.0.

**Time:** ~10 minutes | **Level:** 🔵 Intermediate | **Steps:** 5

**Prerequisites:** Complete [Getting Started](getting-started.md) and have at least one scanned vault.

---

## What Are the Temporal Tools?

Three MCP tools expose time-based vault intelligence. Use them from Claude Desktop or directly via the MCP server:

| MCP Tool | What it shows |
|----------|--------------|
| `get_trends` | Note creation velocity, link growth over time |
| `get_stale_notes` | Top stale notes ranked by staleness score (pagerank × age) |
| `get_daily_digest` | Today's snapshot: new notes, edits, pending links |

These complement the static health tools (`obs health`, `obs analyze`) with a time dimension.

---

## Step 1: Check Vault Health (baseline)

Before monitoring trends, establish a baseline with the static health tools:

```bash
obs health Research           # 4-dimension score (connectivity, links, structure, freshness)
obs analyze Research          # graph metrics (density, clusters, hub/orphan counts)
obs analyze Research --json | python3 -c "
import json, sys
m = json.load(sys.stdin)
print(f\"Density: {m['density']:.4f}\")
print(f\"Orphans: {m['orphan_count']}\")
print(f\"Clusters: {m['cluster_count']}\")
"
```

Run this weekly and compare numbers over time.

---

## Step 2: Find Stale Notes (via Claude Desktop)

From Claude Desktop, after connecting the MCP server:

> *"Show me my most stale notes in Research"*

```
Claude calls: get_stale_notes("Research", limit=20)
Returns:
  has_graph_metrics: true
  notes:
    - {title: "Collider Bias", days_since_modified: 187, pagerank: 0.021, staleness_score: 0.011}
    - {title: "Old Draft Notes", days_since_modified: 312, pagerank: 0.003, staleness_score: 0.003}
    - ...
```

`staleness_score = pagerank × (days_since_modified / 365)` — a high score means an important note (high PageRank) that hasn't been touched in a long time. When `has_graph_metrics` is false, results are sorted by `days_since_modified` only.

Stale notes to prioritize:
- High incoming links + no recent edits → hub notes that may need updating
- Zero links + no recent edits → candidates for archiving
- Recent creation + no edits → early drafts that need attention

---

## Step 3: Track Growth Trends (via Claude Desktop)

> *"Show me the writing velocity for Research over the last 30 days"*

```
Claude calls: get_trends("Research", days=30)
Returns:
  total_notes: 847
  lookback_days: 30
  velocity_notes_per_week: 2.8
  insufficient_data: false
  buckets:
    - {week: "2026-05-26", notes_created: 3, notes_modified: 8}
    - {week: "2026-06-02", notes_created: 1, notes_modified: 12}
    - {week: "2026-06-09", notes_created: 5, notes_modified: 9}
    - {week: "2026-06-16", notes_created: 3, notes_modified: 5}
```

Use this to understand your vault's growth patterns and whether you're linking as you write.

---

## Step 4: Daily Digest (via Claude Desktop)

Start each morning with:

> *"Give me a daily digest of my Research vault"*

```
Claude calls: get_daily_digest("Research")
Returns:
  - Notes created today: 0
  - Notes modified today: 2
  - Notes with no links (new orphans): 1
  - Pending: 3 notes modified >7 days ago with no incoming links
```

!!! tip "Automate the morning digest"
    Add to your morning workflow: open Claude Desktop, type *"Daily digest for Research"*.
    Takes 2 seconds. Catches orphaned notes before your vault grows chaotic.

---

## Step 5: Quality Sweep (weekly)

Combine temporal and AI tools for a weekly review:

```bash
# 1. Find the worst-scoring notes
obs ai quality Research --json | python3 -c "
import json, sys
scores = sorted(json.load(sys.stdin), key=lambda x: x['overall_score'])
for s in scores[:5]:
    print(f\"  {s['overall_score']:3.0f}  {s['title']}\")
"

# 2. Scan for stale content (CLI equivalent — uses graph freshness, not timestamps)
obs health Research --json | python3 -c "
import json, sys
h = json.load(sys.stdin)
print(f\"Freshness score: {h['freshness']['score']}/100\")
print(f\"Structural score: {h['structure']['score']}/100\")
"

# 3. Re-scan so metrics are fresh
obs scan /path/to/Research
```

---

## Weekly Monitoring Routine

```bash
# Monday morning (5 minutes)
obs health Research             # any score drops?
obs analyze Research -v         # orphan/cluster drift?
obs ai quality Research         # 5 worst notes (fix 1-2)
obs ai gaps Research            # any new knowledge gaps?
```

From Claude Desktop, all of the above becomes:
> *"Run my weekly vault review for Research — health, trends, quality scores, and gaps"*

Claude chains `get_vault_health` → `get_trends` → `run_obs_ai("quality", "Research")` → `run_obs_ai("gaps", "Research")` and summarizes in one response.

---

## What's Next

| Goal | Resource |
|------|----------|
| Research tools (Zotero, PDFs) | [Research Setup](research-setup.md) |
| MCP tool reference | [Claude Integration](../claude-integration.md#temporal-tools) |
| All health commands | [CLI Reference — Health section](../cli-reference.md#obs-health) |
