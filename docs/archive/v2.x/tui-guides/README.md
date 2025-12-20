# TUI Navigation Guides

Complete guides for navigating the Obsidian CLI Ops Terminal UI (TUI) using vim-style keyboard shortcuts.

## 📚 Available Guides

### 1. [Vim Tutorial](vim-tutorial.md) - **Start Here!**
**Complete beginner's guide to vim navigation**

- Philosophy of vim motions (home row efficiency)
- 4 learning levels (Essential → Advanced)
- Day-by-day learning path
- Common workflows with examples
- Tips for vim beginners
- FAQ section

**Best for:** First-time users, vim beginners

---

### 2. [Quick Reference](quick-reference.md)
**Detailed reference card with all shortcuts**

- All keyboard shortcuts organized by screen
- Vim motion cheat sheet with visual diagrams
- Common workflows
- All keys listed alphabetically
- Pro tips and learning priorities

**Best for:** Quick lookups, learning specific screens

---

### 3. [Cheat Sheet](cheat-sheet.txt) - **Print This!**
**Printable one-page reference**

- ASCII art format (great in terminal)
- All shortcuts at a glance
- Quick workflows
- Can print and keep at desk

**Best for:** Desk reference, terminal display

---

## 🎓 Learning Path

**Day 1:** Essential Movement
1. Read [Vim Tutorial](vim-tutorial.md) - Level 1 & 2
2. Print [Cheat Sheet](cheat-sheet.txt)
3. Practice: `j` (down), `k` (up), `Enter`, `Esc`, `q`

**Day 2-3:** Add Vim Motions
- Replace arrow keys with `j/k`
- Keep using `Enter`, `Esc`, `q`

**Week 1:** Screen Actions
- Learn `g` (graph), `s` (stats), `d` (discover)
- Practice `/` for search
- Try `r` for refresh

**Week 2+:** Flow State
- Navigation becomes automatic
- Hands stay on home row
- Fast exploration without thinking

---

## 🚀 Quick Start

```bash
# Launch TUI
obs

# Basic navigation
j j j           # Move down (or use arrow keys)
Enter           # Open something
Esc             # Go back
q               # Quit
```

## ✨ New in v2.2.0: ADHD-Friendly Dashboard

We've redesigned the TUI to be more focused and navigable.

### 1. Vault-First Workflow
The app now opens directly to the **Vault Browser**.
1. Select a vault.
2. You land on the **Vault Dashboard**.
3. Choose your task (Notes, Graph, Stats).

### 2. Global Navigation Keys
Jump anywhere instantly with these keys:

| Key | Action | Description |
|-----|--------|-------------|
| `h` | **Home** | Go to Vault Dashboard |
| `v` | **Vaults** | Switch Vault / Open Browser |
| `n` | **Notes** | Open Note Explorer |
| `g` | **Graph** | Open Graph Visualizer |
| `s` | **Stats** | Open Statistics |
| `l` | **Logs** | View Error Logs (New!) |
| `?` | **Help** | Show Key Bindings |

---

[← Back to User Guides](../README.md) | [← Back to Docs Index](../../../README.md)
