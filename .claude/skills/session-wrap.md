# Session Wrap Skill

Generate a concise session summary for ADHD-friendly progress tracking.

## What This Skill Does

Creates a brief, scannable summary of what was accomplished in the current session:
- ✅ Lists completed tasks
- ✅ Shows files created/modified
- ✅ Highlights key decisions made
- ✅ Notes next steps
- ✅ Saves summary to `.claude/sessions/` directory

## When to Use

Use this skill:
- At the end of a work session
- Before committing major changes
- When you need to step away and come back later
- To create a checkpoint for future reference

## How to Use

```bash
# In Claude Code CLI
/session-wrap
```

Or simply say: "Wrap up" or "End session" or "Summarize"

## Output Format

### Brief Summary (Default)
~20 lines, key facts only:

```markdown
# Session: 2025-12-13 14:30

## Completed
- ✅ Created Note Explorer screen (276 lines)
- ✅ Added search/filter functionality
- ✅ Integrated note preview pane
- ✅ Updated documentation

## Files
- Created: src/python/tui/screens/notes.py (276 lines)
- Modified: .STATUS, PHASE_4_TUI_PLAN.md
- Tests: +12 (total: 190)

## Key Decisions
- Used DataTable widget for note list
- Real-time search with filtering
- Preview pane shows first 20 lines

## Next
→ Phase 4.4: Graph Visualizer
→ Test with large vault (1000+ notes)

## Commits
- abc1234: Implement Note Explorer (Phase 4.3)
```

### Full Summary (On Request)
Comprehensive session analysis with:
- Detailed chronology of work
- Technical concepts discussed
- Problems solved
- User feedback received
- Full file listings with line numbers

## Process

1. **Analyze Git History**:
   ```bash
   # Recent commits
   git log --oneline -10

   # Files changed
   git diff --stat HEAD~5..HEAD

   # Lines changed
   git diff --shortstat HEAD~5..HEAD
   ```

2. **Extract Key Info**:
   - What was built (features, files)
   - What was decided (technical choices)
   - What was learned (problems solved)
   - What's next (pending tasks)

3. **Format Summary**:
   - Use ADHD-friendly structure (emojis, bullets, short lines)
   - Show metrics (line counts, test counts)
   - Highlight next steps clearly
   - Include commit hashes for reference

4. **Save to File**:
   ```bash
   mkdir -p .claude/sessions
   # Save as: .claude/sessions/YYYY-MM-DD_HHMM.md
   ```

5. **Display Summary**:
   - Show in terminal
   - Confirm file saved

## Example Scenarios

### After Feature Implementation
```markdown
# Session: Phase 4.3 Complete

## Completed
- ✅ Note Explorer screen with search
- ✅ 12 new tests
- ✅ Documentation updated

## Stats
- Code: +276 lines
- Tests: +85 lines
- Docs: +45 lines

## Next
→ Phase 4.4: Graph Visualizer
```

### After Bug Fix
```markdown
# Session: Bug Fix - Search Crash

## Fixed
- ✅ Search crash on empty vault
- ✅ Preview pane overflow error

## Modified
- src/python/tui/screens/notes.py (lines 89-102)
- Added null checks, boundary validation

## Tests
- Added: test_search_empty_vault
- Added: test_preview_long_content

## Next
→ Manual testing with edge cases
```

### After Research/Planning
```markdown
# Session: TUI Framework Research

## Researched
- Textual vs. Rich vs. Urwid
- Graph visualization options (ASCII art)
- MCP integration possibilities

## Decided
- Use Textual (already in deps)
- ASCII graphs with networkx
- Skills over MCP for workflows

## Next
→ Implement graph visualizer
→ Create custom skills
```

## Configuration

Optional: Create `.claude/sessions/config.json`:
```json
{
  "format": "brief",
  "auto_save": true,
  "include_diffs": false,
  "commit_summary": true
}
```

## Tips

- Brief summaries are better for ADHD (scannable, actionable)
- Save summaries before long breaks
- Use full summaries for complex sessions with many decisions
- Review past summaries to see progress over time
- Include commit hashes for easy git reference

## Session Archive Structure

```
.claude/sessions/
├── 2025-12-13_1030.md  # Phase 4.1 - TUI Foundation
├── 2025-12-13_1430.md  # Phase 4.2 - Vault Browser
├── 2025-12-13_1820.md  # Phase 4.3 - Note Explorer
└── README.md           # Index of all sessions
```

## ADHD-Friendly Features

- ✅ Quick scan: See "Completed" section first
- ✅ Visual anchors: Emojis for section headers
- ✅ Metrics: Concrete numbers (lines, files, tests)
- ✅ Clear next steps: Always show "→ What's next"
- ✅ No fluff: Brevity over completeness
- ✅ Commit links: Easy reference to exact changes
