# SPEC: nexus-cli Phase 2 — Port Remaining Features into obs

> [!warning] ARCHIVED (2026-07-01) — shipped in v4.3.0
> This spec is fully implemented. For **live state and next steps** see [`.STATUS`](../../../.STATUS). Kept for history only.

**Version**: 1.0
**Date**: 2026-07-01
**Status**: Approved (brainstorm consensus)

---

## 1. Scope

Port all remaining nexus-cli features into `obs` under the `obs research` namespace.
~4,130 LOC source + ~2,400 LOC tests + 6 plugin files to absorb.

### 1.1 Already Ported (Phase 1 — v4.0.0)

- `obs config` (5 subcommands, `config_loader.py`)
- `obs research zotero search/get/recent`
- `obs research pdf search`
- `obs research course list/show/lectures`
- `obs research manuscript list/show/stats`
- `obs research bib check`
- `obs research board`

### 1.2 To Port (Phase 2)

| # | Feature | Source | LOC | Priority |
|---|---------|--------|-----|----------|
| P1a | Zotero citation generation + tags/by-tag | `nexus/cli.py` zotero section | ~100 | high |
| P1b | PDF full-text extract | `nexus/cli.py` pdf section | ~50 | high |
| P1c | Knowledge vault ops (search, read, recent, orphans) | `nexus/knowledge/vault.py` (774) | ~774 | high |
| P1d | Unified cross-source search | `nexus/knowledge/search.py` (236) | ~236 | high |
| P2a | Interactive tutorial system (3 levels, 30 steps) | `nexus/utils/tutorial.py` (636) | ~636 | medium |
| P2b | Graph export (GraphML, D3.js, JSON) | `nexus/cli.py` + `knowledge/vault.py` | ~200 | medium |
| P2c | Batch manuscript operations | `nexus/cli.py` writing section | ~150 | medium |
| P2d | Quarto build/preview/info | `nexus/cli.py` teach section | ~200 | medium |
| P3a | PARA vault spec validator | `nexus/utils/vault_spec.py` (108) + `data/vault-spec.yaml` | ~108 | low |
| P3b | Plugin skills (4 domains) | `plugin/skills/`, `plugin/commands/` | ~150 | low |
| P3c | Integrations (aiterm, R, Git) | `nexus/integrations/` | ~50 | low |

## 2. Key Finding: Shallow CLI Wiring vs Deep Module Ports

Several "new" features require **only CLI wiring** because the Python core logic
already exists in obs's research modules (ported in Phase 1):

| Feature | Core method exists? | What's needed |
|---------|-------------------|---------------|
| Zotero cite | ✅ `ZoteroItem.citation_apa()`, `.citation_bibtex()` in `research/zotero.py` | CLI wiring only |
| Zotero tags | ✅ `ZoteroClient.tags()` in `research/zotero.py` | CLI wiring only |
| Zotero by-tag | ✅ `ZoteroClient.by_tag()` in `research/zotero.py` | CLI wiring only |
| PDF extract | ✅ `PDFExtractor.extract()` in `research/pdf.py` | CLI wiring only |
| Batch manuscript | ✅ `ManuscriptManager.batch_update_status()`, `.batch_update_progress()`, `.batch_export_metadata()` in `research/manuscript.py` | CLI wiring only |

Deep module ports needed for:

| Feature | Core module | LOC | Status |
|---------|-------------|-----|--------|
| Vault knowledge ops | `nexus/knowledge/vault.py` | 774 | Full port |
| Unified search | `nexus/knowledge/search.py` | 236 | Full port |
| Tutorial system | `nexus/utils/tutorial.py` | 636 | Full port |
| Graph export | `nexus/knowledge/vault.py` (export methods) | ~150 | Full port (part of vault knowledge) |
| Quarto build/preview | `nexus/cli.py` quarto section | ~200 | Full port |

## 3. Command Layout

All new commands live under `obs research`:

```
obs research
├── zotero
│   ├── search     (exists)
│   ├── get        (exists)
│   ├── recent     (exists)
│   ├── cite       NEW — APA/BibTeX citation from Zotero key
│   ├── tags       NEW — list tags with item counts
│   └── by-tag     NEW — filter items by tag
├── pdf
│   ├── search     (exists)
│   └── extract    NEW — full text extraction from PDF
├── course         (exists)
├── manuscript
│   ├── list/show/stats  (exists)
│   ├── batch-status     NEW — update status for multiple MSS
│   ├── batch-progress   NEW — update progress for multiple MSS
│   └── export           NEW — export metadata to JSON/CSV
├── bib            (exists)
├── learn          NEW — interactive tutorial (3 levels, 30 steps)
├── graph          NEW — export vault knowledge graph
│   └── (graphml|d3|json)
├── quarto         NEW — build/preview Quarto projects
├── knowledge      NEW — vault operations
│   ├── search     NEW — search vault notes
│   ├── read       NEW — read note by path
│   ├── recent     NEW — recently modified notes
│   ├── graph      NEW — graph metrics
│   └── orphans    NEW — find orphaned notes
├── search         NEW — unified search (vault + Zotero + PDF)
└── validate       NEW — PARA vault structure validation
```

## 3. File Layout

```
src/python/research/
├── __init__.py
├── bibliography.py         (existing)
├── courses.py              (existing)
├── manuscript.py           (existing)
├── obs_link.py             (existing)
├── pdf.py                  (extend with extract method)
├── research_board.py       (existing)
├── zotero.py               (extend with citation, tags, by-tag)
├── vault_knowledge.py      NEW — port of nexus/knowledge/vault.py
├── unified_search.py       NEW — port of nexus/knowledge/search.py
├── tutorial.py             NEW — port of nexus/utils/tutorial.py
├── graph_export.py         NEW — port graph export logic
├── vault_spec.py           NEW — port of nexus/utils/vault_spec.py
├── quarto_manager.py       NEW — port quarto build/preview
```

## 4. Testing Strategy

### 4.1 Unit Tests

Port nexus-cli unit tests into `src/python/tests/`:

| Test file | Source | Coverage target |
|-----------|--------|-----------------|
| `test_zotero_extras.py` | `test_zotero_client.py` | ≥90% |
| `test_pdf_extract.py` | `test_pdf_extractor.py` | ≥90% |
| `test_vault_knowledge.py` | `test_vault.py` | ≥80% |
| `test_unified_search.py` | `test_search.py` | ≥80% |
| `test_tutorial.py` | `test_tutorial.py` | ≥80% |
| `test_graph_export.py` | `test_graph_export.py` | ≥80% |
| `test_manuscript_batch.py` | `test_manuscript_batch.py` | ≥80% |
| `test_quarto_manager.py` | `test_quarto_manager.py` | ≥80% |
| `test_vault_spec.py` | `test_vault_spec.py` | ≥90% |

### 4.2 E2E Tests

Add to `test_e2e_research.py`:

- `test_research_zotero_cite` — APA + BibTeX output
- `test_research_zotero_tags` — tag listing
- `test_research_pdf_extract` — text extraction
- `test_research_knowledge_search` — vault search through research CLI
- `test_research_knowledge_orphans` — orphan detection
- `test_research_unified_search` — cross-source search
- `test_research_learn_list` — tutorial listing
- `test_research_graph_export` — graph export (smoke test)
- `test_research_quarto_info` — quarto project info
- `test_research_validate` — PARA validation (smoke test)

## 5. Delivery Phases

### Phase 1 — Research Extensions (P1a–P1d)

Extends existing `obs research` subcommands with minimal new CLI surface:
- Zotero cite (+ tests): ~150 LOC
- Zotero tags/by-tag (+ tests): ~150 LOC
- PDF extract (+ tests): ~200 LOC
- Vault knowledge (+ tests): ~800 LOC
- Unified search (+ tests): ~300 LOC

**Total**: ~1,600 LOC · **Estimated**: 2–3 sessions

### Phase 2 — New Research Subcommands (P2a–P2d)

New feature modules under `obs research`:
- Tutorial system (+ tests): ~700 LOC
- Graph export (+ tests): ~350 LOC
- Batch manuscript ops (+ tests): ~250 LOC
- Quarto manager (+ tests): ~350 LOC

**Total**: ~1,650 LOC · **Estimated**: 2–3 sessions

### Phase 3 — Infrastructure (P3a–P3c)

Lower-priority extras:
- PARA vault spec (+ tests): ~200 LOC
- Plugin skills port: ~150 LOC
- Integrations: ~50 LOC

**Total**: ~400 LOC · **Estimated**: 1 session

### Grand Total

- Source: ~2,700 LOC · Tests: ~2,400 LOC · E2E: ~600 LOC
- **All-in**: ~5,700 LOC across all phases
- **Estimated**: 5–7 sessions

## 6. Configuration

The existing `config_loader.py` already supports the research section needed
for all new features (zotero DB, pdf dirs, courses dir, manuscripts dir).
No config schema changes required.

The vault spec validator uses `~/.config/obs/vault-spec.yaml` with fallback
to bundled `nexus/data/vault-spec.yaml` (to be placed at
`src/python/data/vault-spec.yaml`).

## 7. Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| Tutorial system is 636 LOC of stateful CLI — fragile to port | Port as isolated module first, write E2E tests, then adapt CLI layer |
| Vault knowledge ops overlap with existing obs vault features | Audit overlap before porting — may need to refactor rather than duplicate |
| PDF extract requires `pdftotext` binary | Gate with `shutil.which()` and skip tests gracefully |
| Quarto build requires `quarto` CLI | Same — gate with availability check |
