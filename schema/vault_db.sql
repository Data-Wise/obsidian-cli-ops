-- Obsidian CLI Ops v2.0 Database Schema
-- SQLite database for vault analysis and knowledge management
-- Created: 2025-12-12

-- ============================================================================
-- VAULTS TABLE
-- Stores information about each Obsidian vault
-- ============================================================================

CREATE TABLE IF NOT EXISTS vaults (
    id TEXT PRIMARY KEY,                    -- Unique vault identifier (hash of path)
    name TEXT NOT NULL,                     -- Vault display name
    path TEXT NOT NULL UNIQUE,              -- Absolute path to vault
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_scanned TIMESTAMP,                 -- Last full scan
    note_count INTEGER DEFAULT 0,           -- Cached count
    total_size INTEGER DEFAULT 0,           -- Total size in bytes
    metadata JSON                           -- Flexible metadata storage
);

CREATE INDEX idx_vaults_path ON vaults(path);
CREATE INDEX idx_vaults_last_scanned ON vaults(last_scanned);

-- ============================================================================
-- NOTES TABLE
-- Stores information about each note (markdown file)
-- ============================================================================

CREATE TABLE IF NOT EXISTS notes (
    id TEXT PRIMARY KEY,                    -- Unique note identifier (hash)
    vault_id TEXT NOT NULL,                 -- Parent vault
    path TEXT NOT NULL,                     -- Relative path within vault
    title TEXT NOT NULL,                    -- Note title (from filename or frontmatter)
    content_hash TEXT NOT NULL,             -- SHA256 of content for change detection
    word_count INTEGER DEFAULT 0,
    char_count INTEGER DEFAULT 0,
    created_at TIMESTAMP,                   -- From file metadata
    modified_at TIMESTAMP,                  -- From file metadata
    scanned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    tags TEXT,                              -- Comma-separated tags
    aliases TEXT,                           -- Comma-separated aliases
    metadata JSON,                          -- Frontmatter + custom metadata
    FOREIGN KEY (vault_id) REFERENCES vaults(id) ON DELETE CASCADE
);

CREATE INDEX idx_notes_vault ON notes(vault_id);
CREATE INDEX idx_notes_path ON notes(vault_id, path);
CREATE INDEX idx_notes_title ON notes(title);
CREATE INDEX idx_notes_modified ON notes(modified_at);
CREATE INDEX idx_notes_content_hash ON notes(content_hash);
CREATE INDEX idx_notes_tags ON notes(tags);

-- ============================================================================
-- LINKS TABLE
-- Stores all wikilinks between notes
-- ============================================================================

CREATE TABLE IF NOT EXISTS links (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_note_id TEXT NOT NULL,           -- Note containing the link
    target_note_id TEXT,                    -- Note being linked to (NULL if broken)
    target_path TEXT NOT NULL,              -- Link target (as written)
    link_type TEXT DEFAULT 'internal',      -- internal, external, broken
    link_text TEXT,                         -- Display text (if different from target)
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (source_note_id) REFERENCES notes(id) ON DELETE CASCADE,
    FOREIGN KEY (target_note_id) REFERENCES notes(id) ON DELETE SET NULL
);

CREATE INDEX idx_links_source ON links(source_note_id);
CREATE INDEX idx_links_target ON links(target_note_id);
CREATE INDEX idx_links_type ON links(link_type);

-- ============================================================================
-- GRAPH_METRICS TABLE
-- Stores computed graph metrics for each note
-- ============================================================================

CREATE TABLE IF NOT EXISTS graph_metrics (
    note_id TEXT PRIMARY KEY,
    pagerank REAL DEFAULT 0.0,              -- PageRank score
    in_degree INTEGER DEFAULT 0,            -- Number of incoming links
    out_degree INTEGER DEFAULT 0,           -- Number of outgoing links
    betweenness REAL DEFAULT 0.0,           -- Betweenness centrality
    closeness REAL DEFAULT 0.0,             -- Closeness centrality
    clustering_coefficient REAL DEFAULT 0.0,
    computed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (note_id) REFERENCES notes(id) ON DELETE CASCADE
);

CREATE INDEX idx_metrics_pagerank ON graph_metrics(pagerank DESC);
CREATE INDEX idx_metrics_in_degree ON graph_metrics(in_degree DESC);

-- ============================================================================
-- TAGS TABLE
-- Normalized tag storage for efficient queries
-- ============================================================================

CREATE TABLE IF NOT EXISTS tags (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tag TEXT NOT NULL UNIQUE,               -- Tag name (without #)
    note_count INTEGER DEFAULT 0,           -- Cached count
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_tags_name ON tags(tag);
CREATE INDEX idx_tags_count ON tags(note_count DESC);

-- ============================================================================
-- NOTE_TAGS TABLE
-- Many-to-many relationship between notes and tags
-- ============================================================================

CREATE TABLE IF NOT EXISTS note_tags (
    note_id TEXT NOT NULL,
    tag_id INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (note_id, tag_id),
    FOREIGN KEY (note_id) REFERENCES notes(id) ON DELETE CASCADE,
    FOREIGN KEY (tag_id) REFERENCES tags(id) ON DELETE CASCADE
);

CREATE INDEX idx_note_tags_note ON note_tags(note_id);
CREATE INDEX idx_note_tags_tag ON note_tags(tag_id);

-- ============================================================================
-- SCAN_HISTORY TABLE
-- Tracks vault scans for analytics and debugging
-- ============================================================================

CREATE TABLE IF NOT EXISTS scan_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    vault_id TEXT NOT NULL,
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    notes_scanned INTEGER DEFAULT 0,
    notes_added INTEGER DEFAULT 0,
    notes_updated INTEGER DEFAULT 0,
    notes_deleted INTEGER DEFAULT 0,
    duration_seconds REAL,
    status TEXT DEFAULT 'running',          -- running, completed, failed
    error_message TEXT,
    FOREIGN KEY (vault_id) REFERENCES vaults(id) ON DELETE CASCADE
);

CREATE INDEX idx_scan_history_vault ON scan_history(vault_id);
CREATE INDEX idx_scan_history_started ON scan_history(started_at);

-- ============================================================================
-- ORPHANS VIEW
-- Notes with no incoming or outgoing links
-- ============================================================================

CREATE VIEW IF NOT EXISTS orphaned_notes AS
SELECT
    n.id,
    n.vault_id,
    n.path,
    n.title,
    n.modified_at
FROM notes n
LEFT JOIN links l_out ON n.id = l_out.source_note_id
LEFT JOIN links l_in ON n.id = l_in.target_note_id
WHERE l_out.id IS NULL AND l_in.id IS NULL;

-- ============================================================================
-- HUBS VIEW
-- Highly connected notes (potential important nodes)
-- ============================================================================

CREATE VIEW IF NOT EXISTS hub_notes AS
SELECT
    n.id,
    n.vault_id,
    n.path,
    n.title,
    gm.pagerank,
    gm.in_degree,
    gm.out_degree,
    (gm.in_degree + gm.out_degree) as total_degree
FROM notes n
JOIN graph_metrics gm ON n.id = gm.note_id
WHERE (gm.in_degree + gm.out_degree) > 10
ORDER BY total_degree DESC;

-- ============================================================================
-- BROKEN_LINKS VIEW
-- Links that don't resolve to actual notes
-- ============================================================================

CREATE VIEW IF NOT EXISTS broken_links AS
SELECT
    n.path as source_path,
    n.title as source_title,
    l.target_path,
    COUNT(*) as broken_count
FROM links l
JOIN notes n ON l.source_note_id = n.id
WHERE l.link_type = 'broken'
GROUP BY l.source_note_id, l.target_path;

-- ============================================================================
-- UTILITY FUNCTIONS (Triggers)
-- ============================================================================

-- Trigger to update vault note_count when notes change
CREATE TRIGGER IF NOT EXISTS update_vault_note_count_insert
AFTER INSERT ON notes
BEGIN
    UPDATE vaults
    SET note_count = note_count + 1
    WHERE id = NEW.vault_id;
END;

CREATE TRIGGER IF NOT EXISTS update_vault_note_count_delete
AFTER DELETE ON notes
BEGIN
    UPDATE vaults
    SET note_count = note_count - 1
    WHERE id = OLD.vault_id;
END;

-- Trigger to update tag note_count
CREATE TRIGGER IF NOT EXISTS update_tag_count_insert
AFTER INSERT ON note_tags
BEGIN
    UPDATE tags
    SET note_count = note_count + 1
    WHERE id = NEW.tag_id;
END;

CREATE TRIGGER IF NOT EXISTS update_tag_count_delete
AFTER DELETE ON note_tags
BEGIN
    UPDATE tags
    SET note_count = note_count - 1
    WHERE id = OLD.tag_id;
END;

-- Trigger to update graph metrics in_degree and out_degree
CREATE TRIGGER IF NOT EXISTS update_graph_metrics_insert
AFTER INSERT ON links
BEGIN
    -- Update source out_degree
    UPDATE graph_metrics
    SET out_degree = out_degree + 1
    WHERE note_id = NEW.source_note_id;

    -- Update target in_degree (if target exists)
    UPDATE graph_metrics
    SET in_degree = in_degree + 1
    WHERE note_id = NEW.target_note_id AND NEW.target_note_id IS NOT NULL;
END;

CREATE TRIGGER IF NOT EXISTS update_graph_metrics_delete
AFTER DELETE ON links
BEGIN
    -- Update source out_degree
    UPDATE graph_metrics
    SET out_degree = out_degree - 1
    WHERE note_id = OLD.source_note_id;

    -- Update target in_degree (if target exists)
    UPDATE graph_metrics
    SET in_degree = in_degree - 1
    WHERE note_id = OLD.target_note_id AND OLD.target_note_id IS NOT NULL;
END;

-- ============================================================================
-- INITIAL DATA
-- ============================================================================

-- Schema version tracking
CREATE TABLE IF NOT EXISTS schema_version (
    version INTEGER PRIMARY KEY,
    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    description TEXT
);

INSERT INTO schema_version (version, description) VALUES
    (1, 'Initial schema - Phase 1 Foundation');

-- ============================================================================
-- INDEXES FOR PERFORMANCE
-- ============================================================================

-- Composite indexes for common queries
CREATE INDEX IF NOT EXISTS idx_notes_vault_modified ON notes(vault_id, modified_at DESC);
CREATE INDEX IF NOT EXISTS idx_links_source_target ON links(source_note_id, target_note_id);

-- Full-text search setup (for future use)
-- Note: Will be implemented in Phase 2 with AI integration

-- ============================================================================
-- COMMENTS
-- ============================================================================

-- This schema supports:
-- 1. Multi-vault management
-- 2. Full knowledge graph representation
-- 3. Efficient link resolution
-- 4. Tag-based organization
-- 5. Graph metrics computation
-- 6. Orphan and hub detection
-- 7. Broken link tracking
-- 8. Scan history and analytics

-- Future enhancements (Phase 2+):
-- - AI embeddings table for semantic search
-- - Suggestions table for recommendations
-- - Learning/rules table for user preferences
-- - Operation log for undo functionality
