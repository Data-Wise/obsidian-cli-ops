# Obsidian CLI Ops - Claude Code Skills

Custom skills for streamlined documentation, knowledge management, and session workflows.

## Available Skills

### 📝 docs-update
**Purpose:** Update all project documentation to reflect current state

**Use when:**
- After completing a feature or phase
- Before creating a checkpoint
- When documentation feels outdated

**Example:**
```bash
/docs-update
```
Or say: "Update the docs" or "Run docs update"

**What it does:**
- Updates `.STATUS` with latest progress
- Marks completed tasks in phase plans
- Recalculates metrics (LOC, tests, coverage)
- Checks for documentation inconsistencies
- Updates version numbers

---

### 📋 session-wrap
**Purpose:** Generate brief, scannable session summary

**Use when:**
- At the end of a work session
- Before stepping away
- To create a reference point

**Example:**
```bash
/session-wrap
```
Or say: "Wrap up" or "Summarize session"

**What it does:**
- Lists completed tasks
- Shows files created/modified
- Highlights key decisions
- Notes next steps
- Saves to `.claude/sessions/YYYY-MM-DD_HHMM.md`

**Output format:**
```markdown
# Session: 2025-12-13 14:30

## Completed
- ✅ Task 1
- ✅ Task 2

## Files
- Created: file1.py (100 lines)
- Modified: file2.md

## Next
→ Next task
```

---

### 💾 checkpoint
**Purpose:** Complete checkpoint (docs + wrap + commit)

**Use when:**
- After completing work
- Before taking a break
- Want everything saved and documented

**Example:**
```bash
/checkpoint
```
Or say: "Checkpoint" or "Save my work"

**What it does:**
1. Runs `docs-update` skill
2. Runs `session-wrap` skill
3. Stages all changes with `git add`
4. Creates commit with smart message
5. Optionally creates git tag

**Options:**
- `"Checkpoint: Custom message"` - Use custom commit message
- `"Checkpoint and tag as v2.1.0"` - Create tag
- `"Quick checkpoint"` - Skip docs update

---

## Quick Reference

| Command | What It Does | When to Use |
|---------|-------------|-------------|
| `/docs-update` | Update all docs | After feature complete |
| `/session-wrap` | Generate summary | End of session |
| `/checkpoint` | Docs + wrap + commit | Save everything |
| `/checkpoint` + tag | Full checkpoint + tag | Release ready |
| Quick checkpoint | Wrap + commit only | WIP commits |

## Typical Workflows

### Feature Development

```bash
# Start work
obs tui

# ... implement feature ...

# Save progress (WIP)
"Quick checkpoint"

# ... continue work ...

# Feature complete
"Checkpoint"
```

### End of Day

```bash
# Finish up work
# ...

# Full checkpoint
"Checkpoint"

# Review summary
cat .claude/sessions/2025-12-13_1700.md

# Push if ready
git push origin main
```

### Release

```bash
# Complete final feature
# ...

# Update everything and tag
"Checkpoint and tag as v2.1.0-beta"

# Push with tags
git push origin main --tags
```

## ADHD-Friendly Design

All skills follow these principles:

✅ **One command does everything** - No multi-step processes
✅ **Clear visual feedback** - Emojis, progress indicators
✅ **Automatic tracking** - No manual note-taking required
✅ **Smart defaults** - Minimal decisions needed
✅ **Brief summaries** - Scannable, actionable output
✅ **Always show next steps** - Never wonder "what now?"

## File Locations

- **Session summaries:** `.claude/sessions/YYYY-MM-DD_HHMM.md`
- **Skills:** `.claude/skills/*.md`
- **Documentation:** `.STATUS`, `PHASE_*_PLAN.md`, `PROJECT_PLAN_v2.0.md`, `CLAUDE.md`

## Session Archive

View past sessions:
```bash
ls -lt .claude/sessions/
cat .claude/sessions/2025-12-13_1430.md
```

Sessions are automatically saved with timestamps for easy reference.

## Tips

1. **Use `checkpoint` liberally** - Creates permanent save points
2. **Review summaries before resuming** - Quick context refresh
3. **Custom messages for clarity** - "Checkpoint: Fixed critical bug"
4. **Tag releases** - "Checkpoint and tag as v2.1.0"
5. **Quick checkpoints during dev** - For incremental WIP commits

## Configuration

Skills work out-of-the-box with no configuration. Optional config files:

- `.claude/sessions/config.json` - Session wrap preferences
- `.claude/checkpoint_config.json` - Checkpoint behavior

## Examples

### After Implementing TUI Screen

```
You: "Checkpoint"

Claude:
📝 Updating documentation...
  ✅ .STATUS (marked Phase 4.3 complete)
  ✅ PHASE_4_TUI_PLAN.md (updated tasks)

📋 Wrapping session...
  ✅ Summary saved: .claude/sessions/2025-12-13_1430.md

💾 Committing changes...
  ✅ Commit: abc1234 - feat(tui): Implement Note Explorer

✨ Checkpoint complete!
Next: Phase 4.4 - Graph Visualizer
```

### Quick WIP Commit

```
You: "Quick checkpoint"

Claude:
📋 Wrapping session...
  ✅ Summary saved: .claude/sessions/2025-12-13_1545.md

💾 Committing changes...
  ✅ Commit: def5678 - WIP: Search implementation

✨ Quick checkpoint complete!
```

### Release with Tag

```
You: "Checkpoint and tag as v2.1.0-beta"

Claude:
📝 Updating documentation...
  ✅ .STATUS (updated version)
  ✅ README.md (updated badge)

📋 Wrapping session...
  ✅ Summary saved: .claude/sessions/2025-12-13_1700.md

💾 Committing changes...
  ✅ Commit: ghi9012 - release: v2.1.0-beta
  ✅ Tag: v2.1.0-beta

✨ Checkpoint complete!
Ready to push: git push origin main --tags
```

## Troubleshooting

**Skill not found:**
- Check files exist in `.claude/skills/`
- File names must match: `docs-update.md`, `session-wrap.md`, `checkpoint.md`

**Git errors:**
- Ensure you're in a git repository
- Check for uncommitted changes: `git status`
- Verify you're on the correct branch

**Permission errors:**
- Ensure `.claude/sessions/` directory exists and is writable
- Check file permissions on documentation files

## Next Steps

Start using the skills:
1. Complete some work
2. Say "Checkpoint" to save everything
3. Review your session summary in `.claude/sessions/`
4. Keep building!

---

**Version:** 1.0.0
**Created:** 2025-12-13
**Project:** Obsidian CLI Ops v2.0.0-beta
