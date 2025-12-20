#!/usr/bin/env python3
"""
Obsidian MCP Server

Exposes Obsidian vault operations as MCP tools for AI assistants.
Uses FastMCP for simplified implementation.

Usage:
    # Install dependencies
    pip install mcp

    # Run server (for Claude Desktop)
    python mcp_server.py
    
    # Configure in Claude Desktop settings:
    # Add to mcpServers in config
"""

import sys
from pathlib import Path
from typing import Optional
from datetime import datetime

# Add parent for imports
sys.path.insert(0, str(Path(__file__).parent))

from mcp.server.fastmcp import FastMCP

from db_manager import DatabaseManager
from core.vault_manager import VaultManager
from core.graph_analyzer import GraphAnalyzer
from utils import format_relative_time

# Initialize MCP server
mcp = FastMCP("obsidian-ops")

# Initialize core services
db = DatabaseManager()
vault_manager = VaultManager(db)
graph_analyzer = GraphAnalyzer(db)


# ============================================================================
# TOOLS - Actions the AI can perform
# ============================================================================

@mcp.tool()
def search_notes(query: str, vault_id: Optional[str] = None, limit: int = 10) -> str:
    """
    Search for notes across Obsidian vaults.
    
    Args:
        query: Search term to find in note titles and content
        vault_id: Optional vault ID to scope search (omit for all vaults)
        limit: Maximum number of results to return
    
    Returns:
        Formatted list of matching notes with snippets
    """
    try:
        results = vault_manager.search_notes(query, vault_id=vault_id, limit=limit)
        
        if not results:
            return f"No notes found matching '{query}'"
        
        output = [f"Found {len(results)} notes matching '{query}':\n"]
        for i, note in enumerate(results, 1):
            output.append(f"{i}. **{note['title']}**")
            output.append(f"   Vault: {note.get('vault_name', 'Unknown')}")
            output.append(f"   Path: {note['path']}")
            if note.get('snippet'):
                output.append(f"   Snippet: ...{note['snippet']}...")
            output.append("")
        
        return "\n".join(output)
    except Exception as e:
        return f"Error searching notes: {e}"


@mcp.tool()
def list_vaults() -> str:
    """
    List all Obsidian vaults in the database.
    
    Returns:
        Formatted list of vaults with stats
    """
    try:
        vaults = vault_manager.list_vaults()
        
        if not vaults:
            return "No vaults found. Use 'discover_vaults' to find Obsidian vaults."
        
        output = ["📚 **Obsidian Vaults**\n"]
        for vault in vaults:
            status = "✓ Scanned" if vault.last_scanned else "⊘ Pending"
            output.append(f"- **{vault.name}** ({status})")
            output.append(f"  - Notes: {vault.note_count}")
            output.append(f"  - Links: {vault.link_count}")
            output.append(f"  - Last scanned: {format_relative_time(vault.last_scanned)}")
            output.append(f"  - ID: `{vault.id}`")
            output.append("")
        
        return "\n".join(output)
    except Exception as e:
        return f"Error listing vaults: {e}"


@mcp.tool()
def get_vault_stats(vault_id: Optional[str] = None) -> str:
    """
    Get statistics for a vault or the entire database.
    
    Args:
        vault_id: Specific vault ID, or omit for global stats
    
    Returns:
        Formatted statistics including notes, links, tags, orphans
    """
    try:
        if vault_id:
            vault = db.get_vault(vault_id)
            if not vault:
                return f"Vault not found: {vault_id}"
            
            notes = db.list_notes(vault_id)
            orphans = db.get_orphaned_notes(vault_id)
            broken = db.get_broken_links(vault_id)
            
            return f"""📊 **{vault['name']}**

**Content**
- Notes: {len(notes)}
- Path: {vault['path']}
- Last scanned: {format_relative_time(vault.get('last_scanned'))}

**Graph Health**
- Orphaned notes: {len(orphans)} ({len(orphans)*100//max(len(notes),1)}%)
- Broken links: {sum(b['broken_count'] for b in broken)}
"""
        else:
            stats = db.get_stats()
            return f"""📊 **Database Overview**

**Content**
- Vaults: {stats['vaults']}
- Notes: {stats['notes']}
- Links: {stats['links']}
- Tags: {stats['tags']}

**Graph Health**
- Orphaned notes: {stats['orphaned_notes']}
- Broken links: {stats['broken_links']}
"""
    except Exception as e:
        return f"Error getting stats: {e}"


@mcp.tool()
def find_similar_notes(note_title: str, limit: int = 5) -> str:
    """
    Find notes similar to a given topic or note title.
    
    Args:
        note_title: Title or topic to find similar notes for
        limit: Maximum number of similar notes to return
    
    Returns:
        List of similar notes with relevance
    """
    try:
        # Use search as a simple similarity proxy
        results = vault_manager.search_notes(note_title, limit=limit)
        
        if not results:
            return f"No similar notes found for '{note_title}'"
        
        output = [f"Notes related to '{note_title}':\n"]
        for i, note in enumerate(results, 1):
            output.append(f"{i}. **{note['title']}**")
            output.append(f"   Path: {note['path']}")
            output.append("")
        
        return "\n".join(output)
    except Exception as e:
        return f"Error finding similar notes: {e}"


@mcp.tool()
def get_orphaned_notes(vault_id: str, limit: int = 20) -> str:
    """
    Get notes that have no incoming or outgoing links.
    
    Args:
        vault_id: Vault ID to check for orphans
        limit: Maximum number of orphans to return
    
    Returns:
        List of orphaned notes that need linking
    """
    try:
        orphans = db.get_orphaned_notes(vault_id)
        
        if not orphans:
            return "No orphaned notes found! Your vault is well-connected."
        
        output = [f"🏝️ **{len(orphans)} Orphaned Notes** (showing first {min(limit, len(orphans))})\n"]
        output.append("These notes have no links to or from other notes:\n")
        
        for i, orphan in enumerate(orphans[:limit], 1):
            output.append(f"{i}. **{orphan['title']}**")
            output.append(f"   Path: {orphan['path']}")
        
        if len(orphans) > limit:
            output.append(f"\n... and {len(orphans) - limit} more")
        
        return "\n".join(output)
    except Exception as e:
        return f"Error getting orphaned notes: {e}"


@mcp.tool()
def get_hub_notes(vault_id: str, limit: int = 10) -> str:
    """
    Get the most connected notes in a vault (hub notes).
    
    Args:
        vault_id: Vault ID to analyze
        limit: Maximum number of hubs to return
    
    Returns:
        List of hub notes with connection counts
    """
    try:
        hubs = graph_analyzer.get_hub_notes(vault_id, limit=limit)
        
        if not hubs:
            return "No hub notes found. The vault may need more internal linking."
        
        output = ["🌟 **Hub Notes** (most connected)\n"]
        
        for i, hub in enumerate(hubs, 1):
            in_deg = hub.get('in_degree', 0)
            out_deg = hub.get('out_degree', 0)
            total = in_deg + out_deg
            output.append(f"{i}. **{hub['title']}** ({total} connections)")
            output.append(f"   ↗️ {out_deg} outgoing, ↙️ {in_deg} incoming")
        
        return "\n".join(output)
    except Exception as e:
        return f"Error getting hub notes: {e}"


# ============================================================================
# RESOURCES - Data the AI can read
# ============================================================================

@mcp.resource("vault://{vault_id}/stats")
def vault_stats_resource(vault_id: str) -> str:
    """Get vault statistics as a resource."""
    return get_vault_stats(vault_id)


@mcp.resource("obsidian://overview")
def overview_resource() -> str:
    """Get overall Obsidian database overview."""
    return get_vault_stats()


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    # Run the MCP server
    mcp.run()
