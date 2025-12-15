#!/usr/bin/env python3
"""Generate keyboard shortcuts documentation from TUI BINDINGS."""

import re
from pathlib import Path
from datetime import datetime


def extract_bindings_from_file(filepath: Path) -> dict:
    """Extract BINDINGS from a Python file.

    Args:
        filepath: Path to Python file

    Returns:
        Dict with screen name and list of binding dicts
    """
    content = filepath.read_text()

    # Find class name
    class_match = re.search(r'class (\w+)\(Screen\):', content)
    if not class_match:
        return {}

    screen_name = class_match.group(1)

    # Find BINDINGS array
    bindings_match = re.search(r'BINDINGS = \[(.*?)\]', content, re.DOTALL)
    if not bindings_match:
        return {}

    bindings_str = bindings_match.group(1)

    # Parse bindings (simple regex approach)
    binding_pattern = r'Binding\("([^"]+)",\s*"([^"]+)",\s*"([^"]+)"(?:,\s*show=(True|False))?\)'
    bindings = []

    for match in re.finditer(binding_pattern, bindings_str):
        key, action, label = match.groups()[:3]
        show = match.groups()[3] if len(match.groups()) > 3 else "True"

        bindings.append({
            "key": key,
            "action": action,
            "label": label,
            "show": show == "True"
        })

    return {screen_name: bindings}


def generate_markdown(all_bindings: dict) -> str:
    """Generate markdown documentation from bindings.

    Args:
        all_bindings: Dict mapping screen names to binding lists

    Returns:
        Markdown formatted string
    """
    lines = [
        "# Keyboard Shortcuts Reference",
        "",
        "**Obsidian CLI Ops - Interactive TUI**",
        "",
        "---",
        "",
    ]

    # Global shortcuts (present in all screens)
    lines.extend([
        "## Global Shortcuts",
        "",
        "These shortcuts work in most screens:",
        "",
        "| Key | Action | Description |",
        "|-----|--------|-------------|",
        "| `q` | Quit | Exit the application |",
        "| `Esc` | Back | Go to previous screen |",
        "| `?` | Help | Show help screen |",
        "",
        "---",
        "",
    ])

    # Screen-specific shortcuts
    screen_order = ["HomeScreen", "VaultBrowserScreen", "NoteExplorerScreen",
                    "GraphVisualizerScreen", "StatisticsDashboardScreen", "HelpScreen"]

    screen_titles = {
        "HomeScreen": "Home Screen",
        "VaultBrowserScreen": "Vault Browser",
        "NoteExplorerScreen": "Note Explorer",
        "GraphVisualizerScreen": "Graph Visualizer",
        "StatisticsDashboardScreen": "Statistics Dashboard",
        "HelpScreen": "Help Screen",
    }

    for screen_name in screen_order:
        if screen_name not in all_bindings:
            continue

        bindings = all_bindings[screen_name]
        title = screen_titles.get(screen_name, screen_name)

        lines.extend([
            f"## {title}",
            "",
            "| Key | Action | Description |",
            "|-----|--------|-------------|",
        ])

        for binding in bindings:
            key = binding["key"]
            if key == "escape":
                key = "Esc"
            elif key == "enter":
                key = "Enter"
            elif key == "tab":
                key = "Tab"

            label = binding["label"]
            action = binding["action"].replace("_", " ").title()

            lines.append(f"| `{key}` | {action} | {label} |")

        lines.extend(["", ""])

    # Footer
    lines.extend([
        "---",
        "",
        "**Generated automatically from TUI BINDINGS**",
        "",
        f"*Last updated: {datetime.now().strftime('%Y-%m-%d')}*",
    ])

    return "\n".join(lines)


def main():
    """Generate keyboard shortcuts documentation."""
    # Find all screen files
    screens_dir = Path(__file__).parent / "tui" / "screens"
    app_file = Path(__file__).parent / "tui" / "app.py"

    all_bindings = {}

    # Extract from screens
    for screen_file in screens_dir.glob("*.py"):
        if screen_file.name == "__init__.py":
            continue
        bindings = extract_bindings_from_file(screen_file)
        all_bindings.update(bindings)

    # Extract from app.py (HomeScreen, HelpScreen)
    bindings = extract_bindings_from_file(app_file)
    all_bindings.update(bindings)

    # Generate markdown
    markdown = generate_markdown(all_bindings)

    # Write to project root
    output_file = Path(__file__).parent.parent.parent / "KEYBOARD_SHORTCUTS.md"
    output_file.write_text(markdown)

    print(f"✅ Generated keyboard shortcuts documentation: {output_file}")
    print(f"   Found {len(all_bindings)} screens with {sum(len(b) for b in all_bindings.values())} bindings")


if __name__ == "__main__":
    main()
