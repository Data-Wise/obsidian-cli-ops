# Project Plan: Obsidian CLI Ops v2.0
## Intelligent Multi-Vault Knowledge Management System

> **Vision:** Transform obs from a vault management tool into an intelligent knowledge companion that learns, suggests, and adapts to how you organize information.

---

## 📋 Table of Contents

1. [Vision & Goals](#vision--goals)
2. [Design Decisions](#design-decisions)
3. [Architecture Overview](#architecture-overview)
4. [Phased Implementation](#phased-implementation)
5. [Technical Specifications](#technical-specifications)
6. [User Workflows](#user-workflows)
7. [Success Metrics](#success-metrics)

---

## 🎯 Vision & Goals

### Current State (v1.1.0)
- Basic vault management (sync config, install plugins)
- R-Dev integration with hardcoded paths
- Single-direction workflow (R → Obsidian)
- No content understanding or intelligence

### Future State (v2.0)
- **Intelligent vault ecosystem** - Understands your knowledge structure
- **AI-powered insights** - Uses Claude & Gemini for analysis
- **Learning system** - Adapts to your preferences over time
- **TUI interface** - Beautiful, ADHD-friendly visualizations
- **Multi-directional knowledge flow** - Any vault ↔ Any vault

### Core Objectives

1. **Learn** - Understand vault structure, content, and relationships
2. **Suggest** - Provide intelligent reorganization recommendations
3. **Adapt** - Learn from user feedback and corrections
4. **Visualize** - Make knowledge structure visible and interactive
5. **Protect** - Safe, reversible operations with clear confirmations

---

## 🎨 Design Decisions

### 1. Scope: TUI + CLI
**Decision:** Add TUI for visualization, keep CLI for automation

**Rationale:**
- TUI provides visual clarity for complex operations
- CLI remains for scripting and automation
- Progressive enhancement (CLI → TUI → GUI later)

**Implementation:**
```bash
obs discover              # CLI output
obs discover --tui        # Interactive browser
obs discover --json       # Machine-readable output
```

### 2. Safety: ADHD-Friendly Confirmations
**Decision:** Visual, clear confirmations with easy cancellation

**Design Principles:**
- ✅ Use colors, boxes, emojis for visual anchoring
- ✅ Show exact consequences before action
- ✅ Default to safe option (cancel)
- ✅ Provide undo capability
- ✅ Keep in trash before permanent deletion

**Example Flow:**
```
[Visual box showing what will change]
[Preview of result]
[Multiple clear options]
[Countdown for auto-cancel]
```

### 3. Privacy: Local + Cloud AI
**Decision:** Multiple AI providers with local fallback

**Configuration:**
- Primary: Claude (deep reasoning)
- Secondary: Gemini (fast embeddings, topic modeling)
- Fallback: Local models (privacy-focused users)
- User controls which AI for which tasks

### 4. Integration: Standalone
**Decision:** Remain standalone tool, not Obsidian plugin

**Rationale:**
- Works across multiple vaults simultaneously
- Independent update cycle
- Can integrate with other tools (Emacs, R, etc.)
- No Obsidian API limitations

### 5. Learning: User Feedback Loop
**Decision:** System learns from corrections and builds rules

**Learning Sources:**
1. Accepted suggestions → Increase confidence
2. Rejected suggestions → Learn exclusion rules
3. Manual corrections → Extract patterns
4. Explicit feedback → Create custom rules

---

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                     obs v2.0 System                         │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │   CLI    │  │   TUI    │  │ Learning │  │   API    │   │
│  │Interface │  │Interface │  │  Engine  │  │ (Future) │   │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └──────────┘   │
│       │             │              │                        │
│  ┌────┴─────────────┴──────────────┴─────────────────────┐ │
│  │              Command Router & Orchestrator            │ │
│  └───────────────────────────────────────────────────────┘ │
│       │             │              │             │          │
│  ┌────▼─────┐  ┌───▼──────┐  ┌───▼──────┐  ┌──▼────────┐ │
│  │  Vault   │  │   AI     │  │  Graph   │  │Operation  │ │
│  │ Scanner  │  │  Router  │  │ Builder  │  │  Logger   │ │
│  └────┬─────┘  └───┬──────┘  └───┬──────┘  └──┬────────┘ │
│       │             │              │             │          │
│  ┌────▼─────────────▼──────────────▼─────────────▼──────┐ │
│  │                  Data Layer                           │ │
│  │  ┌─────────────┐  ┌─────────────┐  ┌──────────────┐  │ │
│  │  │   SQLite    │  │    JSON     │  │    Cache     │  │ │
│  │  │  Vault DB   │  │  Learning   │  │  AI Results  │  │ │
│  │  └─────────────┘  └─────────────┘  └──────────────┘  │ │
│  └───────────────────────────────────────────────────────┘ │
│       │                     │                     │         │
│  ┌────▼──────┐         ┌───▼──────┐         ┌───▼──────┐  │
│  │  Claude   │         │  Gemini  │         │  Local   │  │
│  │    API    │         │   API    │         │  Models  │  │
│  └───────────┘         └──────────┘         └──────────┘  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
         │                    │                    │
    ┌────▼────┐          ┌───▼─────┐         ┌───▼─────┐
    │Obsidian │          │  User   │         │  Trash  │
    │ Vaults  │          │  Config │         │  Folder │
    └─────────┘          └─────────┘         └─────────┘
```

### Core Components

#### 1. Vault Scanner
- Recursively scans vault directories
- Parses markdown frontmatter, links, tags
- Extracts metadata (dates, size, word count)
- Builds file index

#### 2. Graph Builder
- Parses all `[[wikilinks]]`
- Creates node-edge graph structure
- Calculates graph metrics (centrality, clusters)
- Identifies orphans and hubs

#### 3. AI Router
- Decides which AI to use for each task
- Manages API keys and rate limits
- Caches results to reduce costs
- Falls back on failures

#### 4. Learning Engine
- Stores user corrections and feedback
- Generates rules from patterns
- Updates confidence scores
- Exports/imports rules

#### 5. Operation Logger
- Logs all destructive operations
- Enables undo functionality
- Maintains operation history
- Creates backups before changes

---

## 🚀 Phased Implementation

### Phase 1: Foundation (Weeks 1-2)
**Goal:** Build data layer and basic vault understanding

#### Deliverables
- [ ] SQLite database schema
- [ ] Vault scanner (Python/Node.js)
- [ ] Note parser (markdown, frontmatter, links)
- [ ] Basic CLI commands

#### New Commands
```bash
obs discover              # Scan all vaults
obs analyze <vault>       # Basic analysis
obs db init               # Initialize database
obs db rebuild            # Rebuild from scratch
```

#### Database Schema
```sql
-- Vaults
CREATE TABLE vaults (
  id TEXT PRIMARY KEY,
  name TEXT,
  path TEXT,
  last_scanned TIMESTAMP,
  note_count INTEGER,
  total_size INTEGER
);

-- Notes
CREATE TABLE notes (
  id TEXT PRIMARY KEY,
  vault_id TEXT,
  path TEXT,
  title TEXT,
  content_hash TEXT,
  word_count INTEGER,
  created_at TIMESTAMP,
  modified_at TIMESTAMP,
  tags TEXT,
  FOREIGN KEY (vault_id) REFERENCES vaults(id)
);

-- Links
CREATE TABLE links (
  id INTEGER PRIMARY KEY,
  source_note_id TEXT,
  target_note_id TEXT,
  link_type TEXT,
  FOREIGN KEY (source_note_id) REFERENCES notes(id),
  FOREIGN KEY (target_note_id) REFERENCES notes(id)
);

-- Graph Metrics
CREATE TABLE graph_metrics (
  note_id TEXT PRIMARY KEY,
  pagerank REAL,
  in_degree INTEGER,
  out_degree INTEGER,
  betweenness REAL,
  FOREIGN KEY (note_id) REFERENCES notes(id)
);
```

#### Success Criteria
- ✅ Can scan 1000+ notes in < 10 seconds
- ✅ Accurately parses 95%+ of links
- ✅ Database correctly stores all metadata

---

### Phase 2: AI Integration (Weeks 3-4)
**Goal:** Connect to Claude & Gemini for intelligent analysis

#### Deliverables
- [ ] AI provider abstraction layer
- [ ] Claude API integration
- [ ] Gemini API integration
- [ ] Cost tracking and caching
- [ ] AI-powered analysis

#### New Commands
```bash
obs analyze --ai          # AI-powered analysis
obs similarity <note>     # Find similar notes (embeddings)
obs topics <vault>        # Topic modeling
obs understand <note>     # Explain note's role
```

#### AI Task Distribution
| Task | AI | Rationale |
|------|-----|-----------|
| Content analysis | Claude | Superior reasoning |
| Note similarity | Gemini | Fast embeddings |
| Topic modeling | Gemini | Efficient bulk processing |
| Merge strategy | Claude | Complex decision making |
| Reorganization | Claude | Strategic planning |

#### Configuration
```json
{
  "ai": {
    "providers": {
      "claude": {
        "enabled": true,
        "model": "claude-sonnet-4-5",
        "max_tokens": 4096,
        "temperature": 0.3
      },
      "gemini": {
        "enabled": true,
        "model": "gemini-2.0-flash-exp",
        "max_tokens": 8192
      }
    },
    "cache_ttl": 86400,
    "cost_limit_daily": 5.00
  }
}
```

#### Success Criteria
- ✅ AI responses in < 3 seconds
- ✅ 90%+ cache hit rate
- ✅ Daily cost < $5
- ✅ Accurate similarity detection (>85%)

---

### Phase 3: TUI/Visualization (Weeks 5-6) 🚧 IN PROGRESS
**Goal:** Build interactive, ADHD-friendly visualization interface

**Priority:** HIGH (moved ahead of AI Suggestions)
**Status:** Active Development
**Started:** 2025-12-13

**Rationale for Priority Change:**
- Can visualize existing Phase 1 data immediately (vaults, notes, graphs, metrics)
- Better UX for vault exploration and analysis
- Foundation ready when Phase 4 (AI Suggestions) features arrive
- ADHD-friendly visual interface provides immediate value
- Standalone utility that enhances Phase 1-2 work

#### Deliverables
- [x] TUI framework setup (Textual already in requirements.txt)
- [x] Architecture design (PHASE_4_TUI_PLAN.md)
- [ ] Vault browser
- [ ] Note explorer with search/preview
- [ ] Graph visualizer (ASCII art)
- [ ] Statistics dashboard
- [ ] Keyboard navigation (arrows, vim keys, mouse)

#### New Commands
```bash
obs tui                   # Launch TUI application
obs tui --vault-id 1      # Launch directly to vault view
obs tui --screen vaults   # Open specific screen
obs tui --screen notes    # Open notes explorer
obs tui --screen graph    # Open graph visualizer
obs tui --screen stats    # Open statistics dashboard
```

#### TUI Sub-Phases

See [PHASE_4_TUI_PLAN.md](PHASE_4_TUI_PLAN.md) for complete implementation details.

##### Phase 3.1: Foundation (Days 1-2)
- Create `src/python/tui/` directory structure
- Build main app skeleton with Textual
- Implement home screen with menu
- Add keyboard navigation
- Help system

##### Phase 3.2: Vault Browser (Days 3-4)
- List all vaults from database
- Show vault statistics
- Navigate and select vaults
- Vault details panel

##### Phase 3.3: Note Explorer (Days 5-7)
- Display notes in selected vault
- Search/filter by title
- Note preview pane
- Sort by various criteria

##### Phase 3.4: Graph Visualizer (Week 2, Days 1-3)
- ASCII art graph visualization
- Show note connections
- Highlight orphans and hubs
- Display graph metrics

##### Phase 3.5: Statistics Dashboard (Week 2, Days 4-5)
- Vault-level statistics
- Tag analytics
- Link distribution charts
- Growth metrics

##### Phase 3.6: Polish & Integration (Week 2, Days 6-7)
- Error handling and loading states
- Smooth transitions
- CLI integration
- Comprehensive testing

#### Success Criteria
- ✅ TUI launches without errors
- ✅ Can browse all vaults
- ✅ Can view and search notes
- ✅ Graph visualization displays correctly
- ✅ All keyboard navigation works
- ✅ Help system is accessible
- ✅ Intuitive navigation (< 5 key presses to any feature)
- ✅ Clear visual hierarchy
- ✅ Responsive (< 100ms interactions)

---

### Phase 4: Intelligent Suggestions (Weeks 7-8) 📋 DEFERRED
**Goal:** Generate actionable reorganization suggestions

**Status:** Deferred (Phase 3 prioritized)
**Dependencies:** Phase 1-2 complete (ready to implement)
**Will integrate with:** Phase 3 TUI when complete

#### Deliverables
- [ ] Suggestion engine
- [ ] Similarity detection
- [ ] Duplicate finder
- [ ] Move/merge/split recommendations
- [ ] Confidence scoring
- [ ] TUI integration (review interface for suggestions)

#### New Commands
```bash
obs suggest               # Show all suggestions
obs suggest move          # Notes to move
obs suggest merge         # Notes to merge
obs suggest split         # Notes to split
obs suggest archive       # Notes to archive
obs suggest --execute     # Execute suggestions
obs suggest --tui         # Review suggestions in TUI (after Phase 3)
```

#### Suggestion Types

##### 1. Move Suggestions
Suggest notes that should be relocated to different folders based on content analysis.

##### 2. Merge Suggestions (TUI Example)
```
╭─ Suggestions (3 of 12) ──────────────────────────────╮
│                                                      │
│ 📝 MERGE SUGGESTION                                  │
│                                                      │
│ Source: "Mediation Analysis.md"                      │
│   • Location: Research_Lab/Methods/                  │
│   • Size: 4.2 KB | Links: 12                        │
│                                                      │
│ Target: "Causal Mediation.md"                        │
│   • Location: Research_Lab/Methods/                  │
│   • Size: 3.8 KB | Links: 8                         │
│                                                      │
│ Similarity: ████████████░░░░░░░░ 87%                │
│ Confidence: ██████████████████░░ 92%                │
│                                                      │
│ AI Reasoning:                                        │
│ Both notes cover causal mediation theory with       │
│ significant overlap in content. Target is more       │
│ comprehensive and has better structure.              │
│                                                      │
│ [✓] Accept  [✗] Reject  [?] Preview  [→] Next       │
╰──────────────────────────────────────────────────────╯
```

##### 3. Destructive Operation Confirmation
```
╭─ ⚠️  CONFIRM DESTRUCTIVE OPERATION ───────────────────╮
│                                                      │
│ ACTION: Merge 2 notes                                │
│                                                      │
│ CHANGES:                                             │
│  ✓ Content from "Mediation Analysis.md" appended    │
│  ✓ 20 backlinks will be updated                     │
│  ✓ Original file → .trash/ (restorable)             │
│  ✓ Operation logged for undo                        │
│                                                      │
│ PREVIEW:                                             │
│ ┌────────────────────────────────────────────────┐  │
│ │ # Causal Mediation                             │  │
│ │                                                │  │
│ │ [Original content...]                          │  │
│ │                                                │  │
│ │ ## Merged from Mediation Analysis              │  │
│ │ [Appended content...]                          │  │
│ └────────────────────────────────────────────────┘  │
│                                                      │
│ Auto-cancel in: 10s                                  │
│                                                      │
│ [✅ YES]  [👁️ FULL PREVIEW]  [❌ NO]  [💾 SAVE FOR LATER] │
╰──────────────────────────────────────────────────────╯
```

#### Technology Stack
- **AI Providers:** HuggingFace (embeddings), Ollama (reasoning)
- **Similarity:** Cosine similarity with sentence-transformers
- **Clustering:** scikit-learn for topic analysis
- **TUI Integration:** Textual (Phase 3) for suggestion review

#### Success Criteria
- ✅ Generates 20+ useful suggestions per vault
- ✅ 70%+ user acceptance rate
- ✅ < 5% false positive rate
- ✅ Clear, actionable recommendations with reasoning

---

### Phase 5: Learning System (Weeks 9-10)
**Goal:** Learn from user behavior and adapt

#### Deliverables
- [ ] Learning database
- [ ] Feedback collection UI
- [ ] Rule generation engine
- [ ] Confidence scoring
- [ ] Export/import rules

#### New Commands
```bash
obs learn stats           # Show what system learned
obs learn reset           # Reset learning
obs learn export          # Export rules
obs learn import <file>   # Import rules
obs learn tune            # Interactive tuning
obs feedback              # Provide explicit feedback
```

#### Learning Database Schema
```sql
-- Corrections
CREATE TABLE corrections (
  id INTEGER PRIMARY KEY,
  timestamp TIMESTAMP,
  suggestion_type TEXT,
  suggestion_data JSON,
  user_action TEXT,
  user_reason TEXT,
  learned_rule TEXT
);

-- Rules
CREATE TABLE rules (
  id INTEGER PRIMARY KEY,
  rule_type TEXT,
  condition JSON,
  action TEXT,
  confidence REAL,
  learned_from_count INTEGER,
  created_at TIMESTAMP,
  last_applied TIMESTAMP
);

-- Preferences
CREATE TABLE preferences (
  key TEXT PRIMARY KEY,
  value JSON,
  confidence REAL,
  source TEXT
);
```

#### Learning Workflows

##### When User Accepts
```python
def on_suggestion_accepted(suggestion):
    # Increase confidence in similar patterns
    increase_confidence(suggestion.pattern)

    # Extract learnable features
    features = extract_features(suggestion)

    # Update or create rule
    update_rule(features, action='accept')

    # Log for analytics
    log_acceptance(suggestion)
```

##### When User Rejects
```python
def on_suggestion_rejected(suggestion, reason):
    # Decrease confidence
    decrease_confidence(suggestion.pattern)

    # Create exclusion rule
    if reason == 'different_topics':
        create_rule({
            'type': 'never_merge',
            'condition': extract_diff_pattern(suggestion),
            'reason': reason
        })

    # Learn from reason
    learn_from_rejection(suggestion, reason)
```

##### Rule Examples
```json
{
  "rules": [
    {
      "id": 1,
      "type": "never_merge",
      "condition": {
        "tag_mismatch": ["#draft", "#published"]
      },
      "confidence": 0.95,
      "learned_from": 15
    },
    {
      "id": 2,
      "type": "auto_move",
      "condition": {
        "tags_include": ["#theory", "#derivation"],
        "current_folder": "Random"
      },
      "action": {
        "move_to": "Methods/Theory"
      },
      "confidence": 0.88,
      "learned_from": 12
    }
  ]
}
```

#### Success Criteria
- ✅ 20+ learned rules after 100 interactions
- ✅ Accuracy improves 15%+ over baseline
- ✅ User satisfaction > 80%
- ✅ Rules are human-readable

---

### Phase 6: Safety & Polish (Weeks 11-12)
**Goal:** Production-ready with comprehensive safety

#### Deliverables
- [ ] Undo system
- [ ] Trash management
- [ ] Backup creation
- [ ] Comprehensive testing
- [ ] Documentation
- [ ] Error handling

#### New Commands
```bash
obs undo                  # Undo last operation
obs undo --list           # Show operation history
obs undo --id <id>        # Undo specific operation
obs trash                 # Manage trash folder
obs trash restore <file>  # Restore from trash
obs backup create         # Create full backup
obs backup restore <id>   # Restore backup
```

#### Safety Features

##### 1. Operation Logging
```json
{
  "operations": [
    {
      "id": "op_1234567890",
      "timestamp": "2025-12-12T20:00:00Z",
      "type": "merge",
      "details": {
        "source": "path/to/note1.md",
        "target": "path/to/note2.md",
        "backlinks_updated": 20
      },
      "reversible": true,
      "trash_location": ".trash/note1_20251212.md"
    }
  ]
}
```

##### 2. Undo Implementation
```python
def undo_operation(operation_id):
    op = load_operation(operation_id)

    if not op.reversible:
        raise Error("Operation not reversible")

    if op.type == 'merge':
        # Restore from trash
        restore_file(op.trash_location, op.source)

        # Revert backlinks
        for link in op.backlinks_updated:
            revert_link(link)

        # Remove merged content
        remove_merged_section(op.target)

    # Mark as undone
    mark_undone(operation_id)
```

##### 3. Backup System
```bash
~/.config/obs/backups/
├── backup_20251212_120000/
│   ├── manifest.json
│   ├── vaults/
│   └── database/
└── backup_20251213_120000/
```

#### Success Criteria
- ✅ 100% of destructive operations reversible
- ✅ Backups complete in < 30 seconds
- ✅ Zero data loss in testing
- ✅ Comprehensive error messages

---

## 📊 Success Metrics

### User Engagement
- **Daily Active Users:** Track usage frequency
- **Suggestions Accepted:** % of suggestions user acts on
- **Learning Improvement:** Accuracy increase over time
- **Session Duration:** Time spent in TUI

### System Performance
- **Scan Speed:** Notes/second
- **AI Response Time:** < 3 seconds
- **Cache Hit Rate:** > 90%
- **Database Size:** Manageable growth

### Quality Metrics
- **Suggestion Accuracy:** > 75% acceptance rate
- **False Positive Rate:** < 5%
- **User Satisfaction:** > 80% positive feedback
- **Bug Rate:** < 1 critical bug per release

### Cost Efficiency
- **AI Cost:** < $10/month per user
- **Cache Effectiveness:** > 80% cost savings
- **Resource Usage:** < 500 MB RAM, < 1% CPU idle

---

## 🎯 Milestones

### Milestone 1: Foundation Complete (Week 2)
- ✅ Database operational
- ✅ Vault scanner working
- ✅ Basic analysis functional

### Milestone 2: AI Integration (Week 4)
- ✅ Claude & Gemini connected
- ✅ Embeddings working
- ✅ Cost tracking enabled

### Milestone 3: Intelligent Suggestions (Week 6)
- ✅ Merge suggestions working
- ✅ Move suggestions functional
- ✅ > 70% accuracy

### Milestone 4: TUI Launch (Week 8)
- ✅ Interactive interfaces complete
- ✅ ADHD-friendly confirmations
- ✅ Visual knowledge graph

### Milestone 5: Learning System (Week 10)
- ✅ Feedback collection working
- ✅ Rules being generated
- ✅ Accuracy improving

### Milestone 6: Production Release (Week 12)
- ✅ All safety features complete
- ✅ Documentation finished
- ✅ Testing comprehensive
- ✅ v2.0 released

---

## 🚧 Risks & Mitigation

### Technical Risks

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| AI costs too high | High | Medium | Aggressive caching, local fallback |
| Performance issues | High | Low | Optimize scanning, incremental updates |
| Database corruption | Critical | Low | Regular backups, WAL mode |
| API rate limits | Medium | Medium | Queue system, retry logic |

### User Experience Risks

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| Too complex | High | Medium | Progressive disclosure, tutorials |
| Poor suggestions | Medium | Medium | Learning system, confidence threshold |
| Data loss | Critical | Low | Undo system, backups, confirmations |
| Learning too slow | Medium | Low | Seed with defaults, allow manual rules |

---

## 📚 Documentation Plan

### User Documentation
- [ ] Getting Started Guide
- [ ] TUI Tutorial
- [ ] AI Configuration
- [ ] Learning System Guide
- [ ] Safety & Backups
- [ ] Troubleshooting

### Developer Documentation
- [ ] Architecture Overview
- [ ] Database Schema
- [ ] AI Integration Guide
- [ ] Contributing Guide
- [ ] API Reference
- [ ] Testing Guide

### Video Content
- [ ] Installation walkthrough
- [ ] First vault analysis
- [ ] Using suggestions
- [ ] Understanding learning
- [ ] Advanced workflows

---

## 🎓 Next Steps

### Immediate (Next Session)
1. Create database schema
2. Build basic vault scanner
3. Set up AI integration stub
4. Design TUI mockups

### Short-term (Weeks 1-4)
1. Complete Phase 1 & 2
2. Get AI working
3. Generate first suggestions
4. User testing

### Long-term (Months 2-3)
1. Polish TUI
2. Refine learning
3. Production testing
4. v2.0 release

---

**Last Updated:** 2025-12-12
**Version:** 2.0.0-planning
**Status:** 📋 Planning Phase
