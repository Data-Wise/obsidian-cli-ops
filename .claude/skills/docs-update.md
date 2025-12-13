# Docs Update Skill

Automatically update project documentation to reflect current state.

## What This Skill Does

Updates all project documentation files to maintain consistency and accuracy:
- ✅ Updates `.STATUS` with latest progress
- ✅ Marks completed tasks in phase plans
- ✅ Updates metrics (line counts, file counts, test counts)
- ✅ Checks for documentation inconsistencies
- ✅ Updates roadmap completion percentages

## When to Use

Use this skill:
- After completing a major feature or phase
- After making significant code changes
- Before creating a git commit
- When documentation feels stale

## How to Use

```bash
# In Claude Code CLI
/docs-update
```

Or simply say: "Update the docs" or "Run docs update"

## What Gets Updated

### 1. .STATUS File
- **Current State**: Active development phase, production ready features
- **Completed Phases**: Mark tasks as complete, add completion dates
- **Code Statistics**: Recalculate line counts with `cloc` or `find`
- **Metrics**: Update test counts, coverage percentages
- **Next Steps**: Update immediate next steps based on progress
- **Timeline**: Add completion dates

### 2. Phase Plans (e.g., PHASE_4_TUI_PLAN.md)
- **Task Completion**: Mark `[x]` for completed items
- **Status Updates**: Change status from "IN PROGRESS" to "COMPLETE"
- **Add Commits**: Reference git commit hashes for completed work
- **Implementation Details**: Add what was actually built
- **Success Criteria**: Update progress (X/Y criteria met)

### 3. PROJECT_PLAN_v2.0.md
- **Phase Status**: Update phase completion percentages
- **Timeline**: Add actual completion dates
- **Deliverables**: Mark items as delivered

### 4. CLAUDE.md
- **Roadmap Section**: Update phase statuses
- **Commands Available**: Add new commands implemented
- **Version History**: Add entries for significant updates

### 5. README.md
- **Feature Lists**: Update with new features
- **Installation**: Update if dependencies changed
- **Version Badge**: Update version number

## Process

1. **Detect Changes**:
   - Run `git status` to see what changed
   - Run `git diff HEAD` to see recent commits
   - Check for new Python files, test files, documentation

2. **Calculate Metrics**:
   ```bash
   # Line counts (ZSH)
   wc -l src/obs.zsh

   # Line counts (Python)
   find src/python -name "*.py" -not -path "*/tests/*" -exec wc -l {} + | tail -1

   # Test counts (Python)
   grep -r "def test_" src/python/tests/ | wc -l

   # Test counts (Jest)
   grep -r "test(" tests/ __tests__/ | wc -l
   ```

3. **Update Files**:
   - Use Edit tool to update each documentation file
   - Maintain existing format and structure
   - Update dates to current date (YYYY-MM-DD)
   - Update version numbers if applicable

4. **Verify Consistency**:
   - Check all docs mention same phase/version
   - Verify line counts match across docs
   - Ensure completion percentages make sense

5. **Report Changes**:
   - List files updated
   - Show key metrics changed
   - Note any inconsistencies found

## Example Output

```
📝 Documentation Update Complete

Files Updated:
  ✅ .STATUS (updated metrics, marked Phase 4.3 complete)
  ✅ PHASE_4_TUI_PLAN.md (marked tasks complete, added commit)
  ✅ PROJECT_PLAN_v2.0.md (updated timeline)

Metrics Updated:
  • Total LOC: 7,900 → 8,450 (+550)
  • Python LOC: 5,350 → 5,800 (+450)
  • Tests: 162 → 178 (+16)
  • Coverage: 70% → 75% (+5%)

Next Steps:
  → Phase 4.4: Graph Visualizer
  → CI/CD Setup
```

## Configuration

No configuration needed. Skill detects project structure automatically.

## Tips

- Run this before `checkpoint` skill for best results
- Update docs frequently to avoid large catch-up sessions
- Check git diff after updates to verify changes make sense
- ADHD-friendly: Shows clear before/after metrics
