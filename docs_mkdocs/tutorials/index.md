# Tutorials

Learn obs step-by-step with these progressive tutorials.

## Learning Path

```mermaid
flowchart LR
    subgraph L1["Getting Started"]
        A1[Install] --> A2[Discover]
        A2 --> A3[Scan]
        A3 --> A4[Stats]
    end

    subgraph L2["Graph Analysis"]
        B1[Analyze] --> B2[Metrics]
        B2 --> B3[Hubs & Orphans]
    end

    subgraph L3["AI Features"]
        C1[Setup] --> C2[Similar]
        C2 --> C3[Duplicates]
    end

    L1 --> L2 --> L3
```

## Tutorials

| Tutorial | Level | Time | What You'll Learn |
|----------|-------|------|-------------------|
| [Getting Started](getting-started.md) | Beginner | ~10 min | Install, discover vaults, scan, view stats |
| [Graph Analysis](graph-analysis.md) | Intermediate | ~15 min | Analyze graph, interpret metrics, find hubs & orphans |
| [AI Features](ai-features.md) | Advanced | ~20 min | Setup AI providers, find similar notes, detect duplicates |

## Prerequisites

- macOS or Linux
- Python 3.9+
- An Obsidian vault (any size)

## Tips

- Each tutorial builds on the previous one
- Commands show expected output so you can verify
- Use `--verbose` on any command for more detail
