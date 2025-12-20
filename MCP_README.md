# Obsidian MCP Server

MCP server for Claude Desktop to interact with Obsidian vaults.

## Setup

1. **Install dependencies:**

```bash
pip install mcp
```

2. **Add to Claude Desktop config:**

Edit `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "obsidian-ops": {
      "command": "python3",
      "args": ["/Users/dt/projects/dev-tools/mcp-servers/obsidian-ops/mcp_server.py"]
    }
  }
}
```

3. **Restart Claude Desktop**

## Tools Available

| Tool | Description |
|------|-------------|
| `search_notes` | Search across vaults |
| `list_vaults` | Show all vaults |
| `get_vault_stats` | Get statistics |
| `get_orphaned_notes` | Find unlinked notes |
| `get_hub_notes` | Find most connected notes |

## Usage in Claude

- "Search my Obsidian for causal inference"
- "Show my vault statistics"
- "Find orphaned notes"
