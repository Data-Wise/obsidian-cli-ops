---
paths:
  - ".claude/skills/**"
---

# Claude Code Skills

Custom skills for streamlined documentation, knowledge management, and session workflows. These are markdown instruction files in `.claude/skills/` that provide one-command workflows for common tasks.

## Available Skills

### docs-update
**Purpose:** Automatically update all project documentation

**Usage:**
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

### session-wrap
**Purpose:** Generate brief, ADHD-friendly session summaries

**Usage:**
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
- Next task
```

### checkpoint
**Purpose:** Complete checkpoint (docs + wrap + commit)

**Usage:**
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
- `"Quick checkpoint"` - Skip docs update (WIP commits)

## Typical Workflow

```bash
# During development
# ... implement feature ...

# Save progress (WIP)
"Quick checkpoint"

# ... continue work ...

# Feature complete
"Checkpoint"

# Review summary
cat .claude/sessions/2025-12-13_1700.md

# Push if ready
git push origin main
```

## ADHD-Friendly Design

All skills follow these principles:
- ✅ One command does everything (no multi-step processes)
- ✅ Clear visual feedback (emojis, progress indicators)
- ✅ Automatic tracking (no manual note-taking required)
- ✅ Smart defaults (minimal decisions needed)
- ✅ Brief summaries (scannable, actionable output)
- ✅ Always show next steps (never wonder "what now?")

## Documentation

See `.claude/skills/README.md` for complete usage guide and examples.
