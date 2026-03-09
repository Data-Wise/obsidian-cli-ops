# UX Spec: AI Suggestion Review Dashboard

**Command**: `obs ai review <vault>`
**Date**: 2026-03-06
**Status**: Design spec (no code)

---

## Design Principles

1. **One thing at a time** -- present a single suggestion, full context, clear actions
2. **Progressive disclosure** -- show summary first, details on demand (d key)
3. **ADHD-friendly** -- bold visual anchors, no walls of text, clear progress signal
4. **Consistent with existing `obs` patterns** -- cyan borders, ROUNDED box, bold cyan headers

### Existing Design Language (carried forward)

| Element          | Style                          |
|------------------|--------------------------------|
| Panel borders    | `border_style="cyan"`, ROUNDED |
| Headers          | `bold cyan`                    |
| Status: good     | `[green]`                      |
| Status: warning  | `[yellow]`                     |
| Status: error    | `[red]`                        |
| Dim/secondary    | `[dim]`                        |
| Score bars       | Full block + light shade       |

---

## 1. ASCII Wireframes

### 1A. Session Header (shown once at launch)

```
+--[ AI Review: Research Vault ]------------------------------------------+
|                                                                          |
|  Suggestions: 17 total                                                   |
|    Merge candidates  .... 4   (2 high, 1 med, 1 low)                    |
|    Tag suggestions   .... 8   (3 high, 5 med)                           |
|    Quality issues    .... 5   (1 high, 2 med, 2 low)                    |
|                                                                          |
|  Priority breakdown:  HIGH 6  |  MED 8  |  LOW 3                        |
|                                                                          |
|  [y] approve  [n] reject  [s] skip  [d] details  [a] apply-all  [q] quit|
+--------------------------------------------------------------------------+
```

After this header, the tool presents items one at a time.
High-priority items appear first across all categories (not grouped by type).

---

### 1B. Merge Candidate Review Screen

```
  Reviewing 3 of 17                                 [=========>          ] 18%

+--[ MERGE ]-- High Priority -----------------------------------------+
|                                                                       |
|  "API Authentication Notes"  +  "OAuth Setup Guide"                   |
|   api-auth.md (342 words)       oauth-setup.md (289 words)            |
|                                                                       |
|  Similarity: 87%  ████████▓░  |  Shared links: 4  |  Shared tags: 2  |
|                                                                       |
|  Overlapping sections:                                                |
|    - "Bearer token flow"       (both notes, ~80% similar)             |
|    - "Token refresh"           (both notes, ~72% similar)             |
|                                                                       |
|  Suggested result: Keep "API Authentication Notes", merge in unique   |
|                    content from "OAuth Setup Guide"                    |
|                                                                       |
+-----------------------------------------------------------------------+

  [y] approve merge  [n] reject  [s] skip  [d] show diff  [q] quit
  >
```

**Details view** (shown when user presses `d`):

```
+--[ Diff Preview ]----------------------------------------------------+
|                                                                       |
|  === Sections unique to "OAuth Setup Guide" (will be added) ===       |
|                                                                       |
|    ## Redirect URI Configuration              (4 lines)               |
|    > Configure callback URLs for each                                 |
|    > environment. Production uses...                                  |
|                                                                       |
|    ## PKCE Flow                                (7 lines)              |
|    > For public clients, use Proof Key...                             |
|                                                                       |
|  === Sections that overlap (will be deduplicated) ===                 |
|                                                                       |
|  - "Bearer token flow"                                                |
|    LEFT:  "Send the token in the Authorization header..."             |
|    RIGHT: "Include bearer token in the Auth header..."                |
|    KEEP:  Left version (longer, more detail)                          |
|                                                                       |
+-----------------------------------------------------------------------+

  [y] approve merge  [n] reject  [s] skip  [b] back  [q] quit
  >
```

---

### 1C. Tag Suggestion Review Screen

```
  Reviewing 7 of 17                                 [==================>] 41%

+--[ TAGS ]-- High Priority -------------------------------------------+
|                                                                       |
|  "Kubernetes Pod Networking"                                          |
|   k8s-networking.md  |  518 words  |  12 links  |  NO TAGS            |
|                                                                       |
|  Suggested tags:                                                      |
|                                                                       |
|    #kubernetes   95%  █████████▓  (used 23x in vault)                 |
|    #networking   88%  ████████▓░  (used 14x in vault)                 |
|    #devops       71%  ███████░░░  (used 31x in vault)                 |
|    #containers   64%  ██████░░░░  (used 9x in vault)                  |
|                                                                       |
|  Top linked notes (all tagged):                                       |
|    "K8s Services"       #kubernetes #networking                       |
|    "Docker Networking"  #containers #networking #devops               |
|                                                                       |
+-----------------------------------------------------------------------+

  [y] approve all tags  [n] reject  [s] skip  [d] pick individual  [q] quit
  >
```

**Details/pick view** (shown when user presses `d`):

```
  Pick tags to apply (space to toggle, enter to confirm):

    [x] #kubernetes   95%
    [x] #networking   88%
    [ ] #devops       71%
    [ ] #containers   64%

  2 of 4 selected                            [enter] confirm  [esc] cancel
```

---

### 1D. Quality Score Review Screen

```
  Reviewing 12 of 17                                [=====================> ] 71%

+--[ QUALITY ]-- Medium Priority ---------------------------------------+
|                                                                        |
|  "Meeting Notes 2025-11-03"                                            |
|   meetings/2025-11-03.md  |  89 words  |  0 links  |  0 tags          |
|                                                                        |
|  Quality: 24/100  ██░░░░░░░░                                           |
|                                                                        |
|  Issues found:                                                         |
|    [!] No outgoing links       (orphan note)                           |
|    [!] No tags                                                         |
|    [~] Very short              (89 words, vault avg: 340)              |
|    [~] No headings             (flat structure)                        |
|                                                                        |
|  Suggested improvements:                                               |
|    1. Add links to: "Project Alpha", "Team Standup"                    |
|    2. Add tags: #meetings #project-alpha                               |
|    3. Add structure: split into Decisions / Action Items               |
|                                                                        |
+------------------------------------------------------------------------+

  [y] approve suggestions  [n] reject  [s] skip  [d] view note  [q] quit
  >
```

**Details view** (shown when user presses `d`):

```
+--[ Note Preview: Meeting Notes 2025-11-03 ]--------------------------+
|                                                                       |
|  Met with Sarah about API migration.                                  |
|  Need to update the auth module by Friday.                            |
|  John will handle the database schema changes.                        |
|  Discussed moving to OAuth 2.0 for third-party access.               |
|                                                                       |
|  Also talked about Q1 planning -- see slack thread.                   |
|                                                                       |
+-----------------------------------------------------------------------+

  [y] approve  [n] reject  [s] skip  [b] back  [q] quit
  >
```

---

### 1E. Session Summary (shown at end or on `q`)

```
+--[ Review Complete ]--------------------------------------------------+
|                                                                        |
|  Session: Research Vault                                               |
|  Duration: 4m 32s                                                      |
|                                                                        |
|  Results:                                                              |
|    Approved   9  ████████████████████░░░░░░░░░░  53%                   |
|    Rejected   3  ██████░░░░░░░░░░░░░░░░░░░░░░░░  18%                  |
|    Skipped    5  ██████████░░░░░░░░░░░░░░░░░░░░  29%                   |
|                                                                        |
|  By type:                                                              |
|    Merges:   2 approved, 1 rejected, 1 skipped                         |
|    Tags:     5 approved, 1 rejected, 2 skipped                         |
|    Quality:  2 approved, 1 rejected, 2 skipped                         |
|                                                                        |
|  Apply 9 approved changes now? [y/n]                                   |
|                                                                        |
+------------------------------------------------------------------------+
```

---

## 2. Interaction Flow

### 2A. Main Loop

```
START
  |
  v
Load suggestions from DB/AI cache
  |
  v
Sort by priority (HIGH > MED > LOW), then by type within same priority
  |
  v
Check for saved session --> resume? [y/n]
  |
  v
Show Session Header (counts, keybinds)
  |
  v
+--> Show next suggestion card
|      |
|      +--> [y] Approve --> mark approved, advance
|      |
|      +--> [n] Reject --> mark rejected, advance
|      |
|      +--> [s] Skip --> mark skipped, advance
|      |
|      +--> [d] Details --> show expanded view
|      |      |
|      |      +--> [b] Back --> return to card
|      |      +--> [y/n/s] --> act and advance
|      |
|      +--> [a] Apply all remaining --> confirm? [y/n]
|      |      |
|      |      +--> [y] --> mark all remaining approved, go to summary
|      |      +--> [n] --> return to current card
|      |
|      +--> [q] Quit --> save session, show summary
|      |
|      +--> [?] Help --> show keybind reference
|
+--- loop until all reviewed or quit
  |
  v
Show Summary
  |
  v
"Apply N approved changes now?" [y/n]
  |
  +--> [y] --> apply changes, report results
  +--> [n] --> "Saved. Run 'obs ai apply' to apply later."
  |
  v
END
```

### 2B. Keypress Reference

| Key | Context        | Action                                      |
|-----|----------------|---------------------------------------------|
| `y` | Card view      | Approve this suggestion                     |
| `n` | Card view      | Reject this suggestion                      |
| `s` | Card view      | Skip (decide later)                         |
| `d` | Card view      | Show details (diff/preview/pick)            |
| `a` | Card view      | Approve ALL remaining (with confirmation)   |
| `q` | Any            | Save session and quit                       |
| `?` | Any            | Show help overlay                           |
| `b` | Details view   | Back to card view                           |
| `space` | Tag pick   | Toggle individual tag selection              |
| `enter` | Tag pick   | Confirm tag selection                       |
| `esc`   | Tag pick   | Cancel, return to card                      |

### 2C. State Transitions per Item

```
  PENDING --> APPROVED
  PENDING --> REJECTED
  PENDING --> SKIPPED
  SKIPPED --> APPROVED  (on re-review in future session)
  SKIPPED --> REJECTED  (on re-review in future session)
```

Approved and Rejected are final within a session. Skipped items reappear next session.

---

## 3. Color Scheme and Visual Hierarchy

### Priority Colors (border + label)

| Priority | Border Color   | Label Style          |
|----------|----------------|----------------------|
| HIGH     | `bold red`     | `[bold red]High[/]`  |
| MEDIUM   | `yellow`       | `[yellow]Medium[/]`  |
| LOW      | `dim cyan`     | `[dim]Low[/]`        |

### Type Badge Colors (left of panel title)

| Type    | Style                        |
|---------|------------------------------|
| MERGE   | `[bold magenta]MERGE[/]`     |
| TAGS    | `[bold green]TAGS[/]`        |
| QUALITY | `[bold yellow]QUALITY[/]`    |

### Confidence/Similarity Score Bars

```
  95-100%   [bold green]    █████████▓
  80-94%    [green]         ████████▓░
  60-79%    [yellow]        ██████▓░░░
  40-59%    [dim yellow]    ████▓░░░░░
  <40%      [red]           ██▓░░░░░░░
```

Uses the same full-block + light-shade pattern as the existing health dashboard.

### Visual Hierarchy (top to bottom on each card)

1. **Progress bar** -- always visible, top of screen, dim style so it anchors without distracting
2. **Type badge + Priority** -- bold, colored, immediate identification
3. **Note title(s)** -- `[bold white]`, largest text on card
4. **Metadata line** -- `[dim]` filename, word count, link/tag counts
5. **Score/similarity** -- colored bar, quantitative anchor
6. **Key findings** -- 2-4 bullet points max, uses `[!]` for critical and `[~]` for minor
7. **Suggested action** -- what will happen if approved
8. **Keybinds** -- `[dim]` at bottom, always present

### ADHD-Specific Design Decisions

- **No scrolling within cards** -- if content exceeds terminal height, truncate with "press d for full view"
- **Maximum 4 bullet points** per card -- forces AI to prioritize
- **Bold first word** in each bullet -- scannable anchors
- **Progress percentage** shown numerically AND as a bar -- dopamine from visible progress
- **Type badges use distinct colors** -- pattern recognition without reading
- **Keybind bar always visible** -- no memorization required

---

## 4. Handling Large Lists

### Pagination Strategy

The design uses **sequential card presentation** (one item at a time), not pagination or scrolling. This is deliberate:

- **Prevents overwhelm** -- ADHD users freeze when shown a list of 50 items
- **Forces a decision** -- each card requires y/n/s before advancing
- **Progress bar provides context** -- "I am on 7 of 23" replaces the need to see the whole list

### For Very Large Sets (50+ suggestions)

Add a **filter prompt** before the main loop:

```
  17 suggestions found. Review:
    [a] All 17
    [h] High priority only (6)
    [t] By type: merges (4) | tags (8) | quality (5)
    [q] Quit

  >
```

This narrows the working set before entering the one-at-a-time flow.

### Performance Guardrails

- **Generate suggestions in batches of 25** -- do not compute all 200 at once
- **Cache suggestions to SQLite** -- `ai_suggestions` table with status column
- **Lazy-load details** -- diff computation happens only when `d` is pressed, not at card render time

---

## 5. Exit/Resume Capability

### Session Persistence

All review state is saved to a SQLite table:

```
Table: ai_review_sessions
  - session_id    TEXT PRIMARY KEY
  - vault_id      TEXT
  - created_at    TIMESTAMP
  - updated_at    TIMESTAMP
  - total_items   INTEGER
  - reviewed       INTEGER
  - status        TEXT  (active | completed | abandoned)

Table: ai_suggestions
  - suggestion_id  TEXT PRIMARY KEY
  - session_id     TEXT FK
  - type           TEXT  (merge | tag | quality)
  - priority       TEXT  (high | medium | low)
  - status         TEXT  (pending | approved | rejected | skipped)
  - data           JSON  (suggestion payload)
  - reviewed_at    TIMESTAMP
```

### Resume Flow

```
$ obs ai review research

  Found saved session (started 2h ago, 7 of 17 reviewed).
  Resume? [y/n/r=restart]

  > y

  Resuming from item 8 of 17...
```

### Quit Behavior

On `q`:
1. Save all decisions made so far
2. Show partial summary
3. Print: `Saved. Resume with 'obs ai review <vault>'`
4. Skipped items remain SKIPPED (re-presented on resume)
5. Approved/rejected items are NOT re-presented

### Apply Later

Approved changes are not applied immediately by default. The summary screen offers to apply, and if declined:

```
  Saved 9 approved changes.
  Apply later with: obs ai apply research
```

This separates review (thinking) from execution (doing) -- important for ADHD users who want to review with confidence that nothing changes until they say so.

---

## 6. Terminal Width Handling

### 80-Column Layout

All wireframes above are designed for 80 columns. The key constraints:

- Panel width: 72 characters inner content + 4 for borders + 4 for padding = 80
- Note titles truncated at 40 characters with ellipsis
- File paths truncated at 30 characters with leading ellipsis (`...eeting-notes.md`)
- Score bars are 10 characters wide (fixed)
- Keybind bar uses abbreviations at narrow widths

### Wider Terminals (120+)

If terminal width exceeds 100 columns:
- Show both notes side-by-side for merge cards (two columns)
- Expand note preview to show more lines
- Show full file paths without truncation

Detection: `console.width` from Rich, check once at session start.

---

## 7. Error States

### No Suggestions Found

```
+--[ AI Review: Research Vault ]----------------------------------------+
|                                                                        |
|  No suggestions to review.                                             |
|                                                                        |
|  Your vault looks good! Run 'obs ai analyze <vault>' to generate      |
|  new suggestions, or 'obs health <vault>' to check vault health.      |
|                                                                        |
+------------------------------------------------------------------------+
```

### AI Provider Unavailable

```
  [!] AI provider not available. Run 'obs ai status' to check setup.
```

Show this before entering the review loop. Do not start a session with stale/missing data.

### Vault Not Scanned Recently

```
  [~] Vault last scanned 14 days ago. Results may be outdated.
      Run 'obs discover --scan' to refresh.
      Continue anyway? [y/n]
```

---

## 8. Accessibility Notes

- All keybinds are single lowercase letters (no modifier keys)
- Color is never the only indicator -- type badges use text labels, scores use numbers alongside bars
- Screen reader: Rich `Console` supports `force_terminal=True` for consistent output; card content is linear and reads top-to-bottom
- No blinking, animation, or auto-advance -- user controls all transitions
- `?` help overlay available at any time

---

## Summary of Deliverables

| # | Deliverable                    | Section |
|---|--------------------------------|---------|
| 1 | ASCII wireframes (5 screens)   | 1A-1E   |
| 2 | Interaction flow diagram       | 2A-2C   |
| 3 | Color scheme + visual hierarchy| 3       |
| 4 | Large list handling            | 4       |
| 5 | Exit/resume capability         | 5       |
