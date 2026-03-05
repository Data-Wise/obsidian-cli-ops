# AI Features

Set up AI providers and use them to find similar notes, analyze content, detect duplicates, and get vault reorganization suggestions.

**Time:** ~25 minutes | **Level:** Advanced | **Steps:** 12

**Prerequisites:** Complete [Getting Started](getting-started.md) (vault scanned)

---

## Step 1: What Can AI Do?

obs supports multiple AI providers for advanced vault analysis:

| Feature | Command | What It Does |
|---------|---------|-------------|
| Similar Notes | `obs ai similar <note_id>` | Find semantically similar notes using embeddings |
| Note Analysis | `obs ai analyze <note_id>` | Deep analysis: topics, themes, suggestions |
| Duplicates | `obs ai duplicates <vault>` | Detect potential duplicate content |
| Suggest Links | `obs ai suggest-links <note_id>` | Find unlinked related notes |
| Knowledge Gaps | `obs ai gaps <vault>` | Detect stub notes, orphans, and gaps |
| Vault Summary | `obs ai summarize <vault>` | Theme analysis across entire vault |
| Vault Refactor | `obs ai refactor <vault>` | AI-powered reorganization suggestions |

All AI features are **optional** — obs works perfectly without them.

---

## Step 2: Check Provider Status

See which AI providers are available on your system:

```bash
obs ai status
```

**Expected output:**

```
🤖 AI Provider Status

  gemini-api    ❌ Not configured (needs API key)
  gemini-cli    ✅ Available (Gemini CLI detected)
  claude-cli    ✅ Available (Claude CLI detected)
  ollama        ❌ Not running (start with: ollama serve)
```

You need at least one provider to use AI features.

---

## Step 3: Run the Setup Wizard

The interactive wizard helps you configure providers:

```bash
obs ai setup
```

The wizard will:

1. Detect available CLIs (gemini, claude, ollama)
2. Check for API keys in environment variables
3. Let you choose a default provider
4. Test the connection

??? tip "Quick setup options"
    - **Fastest (no install):** Use `gemini-cli` or `claude-cli` if you have them
    - **Most private:** Use `ollama` for 100% local processing
    - **Best quality:** Use `gemini-api` with an API key

---

## Step 4: Test Your Providers

Verify everything works:

```bash
obs ai test
```

**Expected output:**

```
🧪 Testing AI Providers...

  gemini-cli    ✅ Working (response in 1.2s)
  claude-cli    ✅ Working (response in 0.8s)
  ollama        ❌ Connection refused

  2/3 providers available
```

---

## Step 5: Find Similar Notes

Find notes that are semantically similar to a given note:

```bash
obs ai similar <note_id>
```

??? info "Finding note IDs"
    Note IDs come from the database. Use `obs stats --vault MyVault` with verbose mode, or query the database directly.

**How it works:**

1. Generates embeddings (vector representations) for your notes
2. Compares using cosine similarity
3. Returns the most similar notes ranked by score

**Use cases:**

- Discover related notes you forgot about
- Find candidates for merging or cross-linking
- Identify knowledge clusters

---

## Step 6: Analyze a Note

Get AI-powered analysis of a single note:

```bash
obs ai analyze <note_id>
```

The analysis includes:

- **Topics** — main subjects covered
- **Themes** — recurring ideas and patterns
- **Quality** — writing clarity and completeness
- **Suggestions** — recommended improvements and connections

---

## Step 7: Detect Duplicates

Scan an entire vault for potential duplicate content:

```bash
obs ai duplicates MyVault
```

**Expected output:**

```
🔍 Scanning for duplicates in MyVault...

  Potential duplicates found: 3

  1. "Git Basics" ↔ "Git Introduction" (similarity: 0.89)
  2. "Python Setup" ↔ "Setting Up Python" (similarity: 0.85)
  3. "Meeting Notes 2024-01" ↔ "Meeting Notes Jan" (similarity: 0.82)
```

**What to do:**

- Review each pair — high similarity doesn't always mean duplicate
- Merge confirmed duplicates using Obsidian's note merge
- Differentiate near-duplicates by adding unique content

---

## Step 8: Suggest Links and Find Gaps

Use AI to discover missing connections and knowledge gaps:

```bash
# Suggest new links for a note
obs ai suggest-links <note_id>
```

**Expected output:**

```
Found 3 link suggestions:

  1. [[Graph Theory]] (78%)
     notes/graph-theory.md
  2. [[Algorithms]] (65%)
     notes/algorithms.md
```

Find areas where your vault needs expansion:

```bash
obs ai gaps MyVault
```

This detects stub notes (referenced often but underdeveloped), orphaned notes, and structural gaps.

---

## Step 9: Summarize Vault Themes

Get a bird's-eye view of your vault:

```bash
obs ai summarize MyVault
```

You can scope to a folder or tag:

```bash
obs ai summarize MyVault --folder "projects/"
obs ai summarize MyVault --tag "python"
```

---

## Step 10: Get Reorganization Suggestions

The refactor command analyzes your vault structure and suggests improvements:

```bash
obs ai refactor MyVault
```

**Expected output:**

```
🔄 Vault Refactor Analysis: MyVault
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 Analyzed 247 notes across 12 folders

🔴 HIGH PRIORITY (3 items)
  1. Move "random-thoughts.md" → inbox/
     Root-level note with no links, likely unsorted
  2. Archive folder "old-stuff/" → archive/
     3 notes, all >90 days stale, low connectivity

🟡 MEDIUM PRIORITY (5 items)
  3. Create "python/" folder for 7 notes with #python tag
     ...
```

??? tip "Dry run mode"
    Preview the scope without making AI calls:
    ```bash
    obs ai refactor MyVault --dry-run
    ```
    Get machine-readable output:
    ```bash
    obs ai refactor MyVault --json
    ```

---

## Step 11: Choose the Right Provider

Different providers excel at different tasks:

| Provider | Speed | Quality | Privacy | Cost |
|----------|-------|---------|---------|------|
| `gemini-api` | Fast | High | Cloud | API key |
| `gemini-cli` | Medium | High | Cloud | Free |
| `claude-cli` | Medium | Highest | Cloud | Free |
| `ollama` | Slow | Good | Local | Free |

**Recommendations:**

- **Privacy first:** Use `ollama` — everything stays on your machine
- **Quality first:** Use `claude-cli` for the best analysis
- **Speed first:** Use `gemini-api` for batch operations
- **No API key:** Use `gemini-cli` or `claude-cli`

obs auto-selects the best available provider, but you can override with configuration.

---

## Step 12: Next Steps

| Want to... | Action |
|------------|--------|
| Review vault health | `obs stats --vault MyVault` |
| Re-analyze after changes | `obs scan /path && obs analyze MyVault` |
| See all AI commands | `obs ai --help` |
| Configure default provider | `obs ai setup` |

---

**Summary:** You set up AI providers, tested them, found similar notes, analyzed content, detected duplicates, discovered knowledge gaps, and got vault reorganization suggestions. Your vault now has AI-powered intelligence built in.
