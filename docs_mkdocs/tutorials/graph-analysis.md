# Graph Analysis

Learn to analyze your vault's knowledge graph and interpret the metrics.

**Time:** ~15 minutes | **Level:** Intermediate | **Steps:** 9

**Prerequisites:** Complete [Getting Started](getting-started.md) (vault scanned)

---

## Step 1: What is Graph Analysis?

Your Obsidian vault is a graph — notes are nodes, wikilinks are edges. Graph analysis reveals the structure of your knowledge:

- **Hub notes** — highly connected, central to your thinking
- **Orphan notes** — isolated, may need integration
- **Clusters** — groups of tightly related notes
- **Broken links** — wikilinks pointing to non-existent notes

---

## Step 2: Run Graph Analysis

Analyze a vault by name or ID prefix:

```bash
obs analyze MyVault
```

**Expected output:**

```
📊 Graph Analysis: MyVault
   Notes: 142
   Links: 387
   Density: 0.0193
   Clusters: 8
```

??? tip "Verbose mode"
    Add `-v` for detailed output including top hub notes and orphan counts:
    ```bash
    obs analyze MyVault -v
    ```

---

## Step 3: Understand Graph Density

**Density** measures how interconnected your vault is, from 0.0 (no links) to 1.0 (every note links to every other).

| Density | Interpretation |
|---------|---------------|
| < 0.01 | Sparse — many isolated notes |
| 0.01–0.05 | Typical — healthy vault |
| 0.05–0.10 | Dense — well-connected |
| > 0.10 | Very dense — may have over-linking |

Most Obsidian vaults fall in the 0.01–0.05 range.

---

## Step 4: Find Hub Notes

Hub notes are the most connected in your vault — they're the backbone of your knowledge graph.

```bash
obs analyze MyVault -v
```

Look for the "Top Hub Notes" section:

```
  🌟 Top Hub Notes:
    • MOC - Machine Learning (47 connections)
    • Index - Projects (32 connections)
    • Daily Notes Overview (28 connections)
    • Research Methods (21 connections)
    • Tool Comparisons (18 connections)
```

**What to do with hubs:**

- Review them regularly — they influence many notes
- Consider splitting hubs with 50+ connections
- Hubs are great starting points for new readers

---

## Step 5: Find Orphaned Notes

Orphaned notes have no incoming or outgoing links. They're invisible to graph navigation.

```bash
obs stats --vault MyVault
```

Check the "Orphaned" count in Graph Health:

```
  Graph Health
    Orphaned: 12
```

**What to do with orphans:**

- Link them to relevant hub notes or MOCs (Maps of Content)
- Some orphans are fine (daily notes, templates)
- High orphan count (>20%) suggests poor linking habits

---

## Step 6: Detect Broken Links

Broken links are wikilinks (`[[target]]`) that don't resolve to any existing note.

```bash
obs stats --vault MyVault
```

Check the "Broken Links" count:

```
  Graph Health
    Broken Links: 3
```

**Common causes:**

- Renamed notes without updating links
- Deleted notes that were referenced
- Typos in wikilink targets

**Fix:** Create the missing notes, or update the links to point to correct targets.

---

## Step 7: Understand Clusters

Clusters are groups of notes that are more connected to each other than to the rest of the vault. They often represent topic areas.

The "Clusters" count in your analysis output tells you how many distinct communities exist:

```
   Clusters: 8
```

**Interpreting clusters:**

- Each cluster typically represents a topic or project
- Very few clusters (1-2) might mean your vault lacks structure
- Many small clusters might mean topics aren't cross-linked enough

---

## Step 8: Track Changes Over Time

Re-scan and re-analyze periodically to track how your vault evolves:

```bash
# Re-scan to pick up new notes and links
obs scan /path/to/vault

# Re-analyze
obs analyze MyVault -v
```

**Watch for:**

- Orphan count increasing — linking habits may be slipping
- Broken links growing — maintenance needed
- Density increasing — vault is becoming better connected
- New clusters forming — your knowledge is expanding

---

## Step 9: Next Steps

| Want to... | Action |
|------------|--------|
| Use AI to find similar notes | [AI Features Tutorial](ai-features.md) |
| Set up automated scanning | Add `obs scan` to a cron job |
| See all analysis commands | `obs help --all` |

---

**Summary:** You ran graph analysis, interpreted density, found hubs and orphans, detected broken links, and understand clusters. You can now monitor your vault's health over time.
