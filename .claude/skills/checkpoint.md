# Checkpoint Skill

Create a complete checkpoint: update docs, wrap session, and commit changes.

## What This Skill Does

Combines all end-of-work tasks into a single command:
1. ✅ Updates all documentation (via `docs-update` skill)
2. ✅ Generates session summary (via `session-wrap` skill)
3. ✅ Creates git commit with smart message
4. ✅ Optionally tags the commit

This is your "I'm done for now" command.

## When to Use

Use this skill:
- After completing a feature or phase
- Before taking a break
- At end of work session
- When you want everything saved and documented

## How to Use

```bash
# In Claude Code CLI
/checkpoint
```

Or simply say: "Checkpoint" or "Save my work" or "Create checkpoint"

### With Options

```bash
# Create checkpoint with custom message
"Checkpoint: Phase 4.3 complete"

# Create checkpoint and tag
"Checkpoint and tag as v2.1.0-alpha"

# Quick checkpoint (skip docs update)
"Quick checkpoint"
```

## Process

### Standard Checkpoint

1. **Update Documentation**:
   - Runs `docs-update` skill
   - Updates .STATUS, phase plans, README
   - Recalculates metrics
   - Reports changes

2. **Wrap Session**:
   - Runs `session-wrap` skill
   - Generates brief summary
   - Saves to `.claude/sessions/`
   - Displays summary

3. **Stage Changes**:
   ```bash
   git add .
   ```

4. **Generate Commit Message**:
   - If user provided message: Use it
   - Otherwise, auto-generate from:
     - Git diff summary
     - Session wrap summary
     - Phase/feature being worked on

5. **Create Commit**:
   ```bash
   git commit -m "<message>"
   ```

6. **Create Tag** (if requested):
   ```bash
   git tag -a v2.1.0-alpha -m "Phase 4 TUI complete"
   ```

7. **Report**:
   - Show commit hash
   - Show files committed
   - Show tag created (if any)
   - Confirm session saved

### Quick Checkpoint (No Docs)

Skip docs update, just wrap and commit:
1. Wrap session
2. Commit with simple message
3. Done

Use when: Making small incremental commits during active development.

## Commit Message Format

Auto-generated messages follow conventional commits:

```
<type>(<scope>): <description>

<body>

Session: .claude/sessions/YYYY-MM-DD_HHMM.md
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation only
- `test`: Test additions/changes
- `refactor`: Code refactoring
- `style`: Formatting changes
- `chore`: Maintenance tasks

**Examples:**

```
feat(tui): Implement Note Explorer (Phase 4.3)

- Created NoteExplorerScreen with search/filter
- Added note preview pane
- Integrated with database queries
- Added 12 new tests

Session: .claude/sessions/2025-12-13_1430.md
```

```
docs: Update documentation for Phase 4.2 completion

- Marked Phase 4.2 complete in .STATUS
- Updated PHASE_4_TUI_PLAN.md with implementation details
- Updated metrics (8,450 LOC, 178 tests)

Session: .claude/sessions/2025-12-13_1130.md
```

```
test: Add comprehensive vault scanner tests

- Created test_vault_scanner.py (450 lines, 35 tests)
- Added fixtures for temp vaults
- Tested wikilink/tag extraction
- Coverage: 25% → 70%

Session: .claude/sessions/2025-12-13_0930.md
```

## Examples

### After Feature Complete

**User says:** "Checkpoint"

**Output:**
```
📝 Updating documentation...
  ✅ .STATUS (marked Phase 4.3 complete)
  ✅ PHASE_4_TUI_PLAN.md (updated tasks)
  ✅ Metrics: 8,450 LOC, 190 tests

📋 Wrapping session...
  ✅ Summary saved: .claude/sessions/2025-12-13_1430.md

💾 Committing changes...
  ✅ Staged 5 files
  ✅ Commit: abc1234 - feat(tui): Implement Note Explorer (Phase 4.3)

✨ Checkpoint complete!

Next: Phase 4.4 - Graph Visualizer
```

### With Custom Message

**User says:** "Checkpoint: Fixed search crash bug"

**Output:**
```
📝 Updating documentation... (skipped, no major changes)

📋 Wrapping session...
  ✅ Summary saved: .claude/sessions/2025-12-13_1545.md

💾 Committing changes...
  ✅ Staged 2 files
  ✅ Commit: def5678 - fix(tui): Fixed search crash bug

✨ Checkpoint complete!
```

### With Tag

**User says:** "Checkpoint and tag as v2.1.0-beta"

**Output:**
```
📝 Updating documentation...
  ✅ .STATUS (updated version to v2.1.0-beta)
  ✅ README.md (updated version badge)

📋 Wrapping session...
  ✅ Summary saved: .claude/sessions/2025-12-13_1700.md

💾 Committing changes...
  ✅ Staged 8 files
  ✅ Commit: ghi9012 - release: v2.1.0-beta - Phase 4 TUI complete
  ✅ Tag: v2.1.0-beta

✨ Checkpoint complete!

Ready to push:
  git push origin main --tags
```

### Quick Checkpoint

**User says:** "Quick checkpoint"

**Output:**
```
📋 Wrapping session...
  ✅ Summary saved: .claude/sessions/2025-12-13_1620.md

💾 Committing changes...
  ✅ Staged 1 file
  ✅ Commit: jkl3456 - WIP: Note Explorer search implementation

✨ Quick checkpoint complete!
```

## Configuration

Optional: Create `.claude/checkpoint_config.json`:
```json
{
  "auto_docs_update": true,
  "auto_session_wrap": true,
  "commit_format": "conventional",
  "include_session_link": true,
  "auto_push": false,
  "tag_pattern": "v{version}"
}
```

## Safety Features

- ✅ **No auto-push**: Never pushes to remote without explicit request
- ✅ **Git status check**: Shows what will be committed before committing
- ✅ **Dirty check**: Warns if uncommitted changes exist from previous work
- ✅ **Branch check**: Warns if not on expected branch

## Smart Behaviors

### Auto-Detect Checkpoint Type

Based on changes, automatically determines:
- **Feature checkpoint**: New files, substantial additions
- **Docs checkpoint**: Only documentation changed
- **Test checkpoint**: Only tests changed
- **Fix checkpoint**: Small changes to existing files

### Session Continuity

Links to previous checkpoints:
```markdown
# Session: 2025-12-13 14:30
Previous: 2025-12-13_1030.md (Phase 4.2 complete)

## Completed
...
```

### Metrics Tracking

Tracks cumulative progress:
```
Phase 4 Progress:
  4.1 ✅ Foundation (994ae42)
  4.2 ✅ Vault Browser (707f3d7)
  4.3 ✅ Note Explorer (abc1234) ← Current checkpoint
  4.4 ⏳ Graph Visualizer
  4.5 ⏳ Statistics Dashboard
  4.6 ⏳ Polish & Integration
```

## Tips

- Use `checkpoint` after every significant piece of work
- Use `quick checkpoint` for incremental WIP commits during active dev
- Add custom messages for clarity: "Checkpoint: Fixed critical bug"
- Tag releases: "Checkpoint and tag as v2.1.0"
- Review session summaries before resuming work
- ADHD-friendly: One command does everything

## What Gets Committed

The checkpoint will stage and commit:
- ✅ Source code changes (src/*)
- ✅ Test files (tests/*, src/python/tests/*)
- ✅ Documentation (*.md, docs_mkdocs/*)
- ✅ Configuration files (*.json, *.ini, *.yml)
- ✅ Session summaries (.claude/sessions/*)

**Never commits:**
- ❌ `node_modules/`
- ❌ `.venv/`, `__pycache__/`
- ❌ `.env`, secrets
- ❌ Build artifacts

(Respects `.gitignore`)

## Example Workflow

```bash
# Morning: Start working
obs tui  # Launch TUI

# Implement feature
# ... code changes ...

# Midday: Save progress
"Quick checkpoint"  # WIP commit

# ... more work ...

# Afternoon: Feature complete
"Checkpoint"  # Full docs + commit

# Evening: Ready to release
"Checkpoint and tag as v2.1.0-beta"

# Push to remote
git push origin main --tags
```

## ADHD-Friendly Features

- ✅ One command does everything (no multi-step process)
- ✅ Clear progress indicators (emoji, percentages)
- ✅ Automatic session summaries (no manual note-taking)
- ✅ Smart commit messages (no decision fatigue)
- ✅ Visual feedback (shows what's happening)
- ✅ Next steps always shown (no wondering "what now?")
