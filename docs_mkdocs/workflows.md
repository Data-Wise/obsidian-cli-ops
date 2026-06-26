# Visual Workflows

> **TL;DR** (30 seconds)
> - **What:** Visual diagrams showing how `obs` commands fit together
> - **Why:** See the big picture before diving into individual commands
> - **How:** Follow the flowcharts — each box is a command you can run
{ .tldr }

---

## :wave: Onboarding Workflow

First time using `obs`? Follow this path:

```mermaid
graph TD
    A[Install obs] --> B[obs discover ~/Documents --scan]
    B --> C{Vaults found?}
    C -->|Yes| D[obs]
    C -->|No| E[Check vault location]
    E --> F[obs discover /other/path --scan]
    F --> C
    D --> G[obs stats MyVault]
    G --> H[obs analyze MyVault]
    H --> I{Want AI features?}
    I -->|Yes| J[obs ai setup]
    I -->|No| K[Done!]
    J --> L[obs ai test]
    L --> K
    style A fill:#6366f1,color:#fff
    style K fill:#22c55e,color:#fff
```

---

## :sun_with_face: Daily Usage Workflow

Your typical day with `obs`:

```mermaid
graph LR
    A[obs] --> B{Pick a vault}
    B --> C[obs stats Vault]
    C --> D{Issues?}
    D -->|Orphans| E[obs ai refactor Vault]
    D -->|Broken links| F[Fix in Obsidian]
    D -->|All good| G[obs analyze Vault]
    G --> H[Done]
    E --> H
    F --> H
    style A fill:#6366f1,color:#fff
    style H fill:#22c55e,color:#fff
```

!!! tip "Make it a habit"
    Run `obs health MyVault` once a week to catch issues early. Add it to your weekly review workflow.

---

## :robot: AI Analysis Pipeline

How AI features work together for deep vault analysis:

```mermaid
graph TD
    A[obs ai status] --> B{Provider available?}
    B -->|No| C[obs ai setup]
    C --> A
    B -->|Yes| D[Choose analysis type]
    D --> E[obs ai duplicates Vault]
    D --> F[obs ai gaps Vault]
    D --> G[obs ai refactor Vault]
    D --> H[obs ai summarize Vault]
    E --> I[Review duplicates]
    F --> J[Fill knowledge gaps]
    G --> K[Reorganize vault]
    H --> L[Understand themes]
    style A fill:#6366f1,color:#fff
    style I fill:#f59e0b,color:#000
    style J fill:#f59e0b,color:#000
    style K fill:#f59e0b,color:#000
    style L fill:#f59e0b,color:#000
```

??? info "AI commands are read-only"
    AI commands analyze and suggest — they never modify your vault files. You decide what to act on.

---

## :heart: Vault Health Check Workflow

Systematic health check for any vault:

```mermaid
graph TD
    A[obs health Vault] --> B{Overall score}
    B -->|90+| C[Healthy!]
    B -->|70-89| D[Minor issues]
    B -->|Below 70| E[Needs attention]
    D --> F[obs analyze Vault -v]
    E --> F
    F --> G{Top issue?}
    G -->|Low connectivity| H[obs ai suggest-links note_id]
    G -->|Many orphans| I[obs ai refactor Vault]
    G -->|Broken links| J[Fix wikilinks in Obsidian]
    G -->|Low freshness| K[Review stale notes]
    H --> L[Add suggested links]
    I --> M[Follow reorganization plan]
    J --> L
    K --> L
    L --> N[Re-scan: obs analyze Vault]
    M --> N
    style A fill:#6366f1,color:#fff
    style C fill:#22c55e,color:#fff
    style N fill:#8b5cf6,color:#fff
```

---

## :link: Note-Level Analysis Workflow

Deep dive into a single note:

```mermaid
graph LR
    A[obs ai analyze note_id] --> B[Review themes & quality]
    B --> C[obs ai similar note_id]
    C --> D[obs ai suggest-links note_id]
    D --> E[Add links in Obsidian]
    style A fill:#6366f1,color:#fff
    style E fill:#22c55e,color:#fff
```

---

## :robot_face: Claude / MCP Workflow (v3.3.0)

Use Claude Desktop to query and edit your vaults in natural language:

```mermaid
graph TD
    A[Claude Desktop] --> B{obsidian-ops MCP connected?}
    B -->|No| C[claude_desktop_config.json setup]
    C --> D[Restart Claude Desktop]
    D --> A
    B -->|Yes| E[Natural language query]
    E --> F[Search / Analyze]
    E --> G[Read / Write Notes]
    E --> H[AI Features]
    F --> I["search_notes, get_hub_notes,<br/>analyze_vault, get_vault_health"]
    G --> J["read_note, create_note,<br/>append_to_note, write_note"]
    H --> K["run_obs_ai: gaps, quality,<br/>refactor, merge-suggest"]
    style A fill:#6366f1,color:#fff
    style C fill:#f59e0b,color:#000
    style I fill:#22c55e,color:#fff
    style J fill:#22c55e,color:#fff
    style K fill:#22c55e,color:#fff
```

!!! tip "5-minute setup"
    See [Claude Integration](claude-integration.md) to connect `obs` to Claude Desktop.
    Once connected, all 42 MCP tools are available in every Claude conversation.

---

## :arrow_right: Next Steps

| Want to... | Go to |
|------------|-------|
| Start using obs | [ADHD Quick Start](adhd-quick-start.md) |
| See all commands | [CLI Reference](cli-reference.md) |
| Copy-paste recipes | [Cookbook](cookbook.md) |
| Set up AI | [AI Setup Guide](ai-setup.md) |
| Connect Claude Desktop | [Claude Integration](claude-integration.md) |
