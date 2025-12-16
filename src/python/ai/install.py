"""
Dependency Installation Helper.

Handles:
- Checking if packages are installed
- Prompting user for installation
- Installing packages via pip
- Provider-specific setup (API keys, etc.)
"""

import sys
import subprocess
import importlib.util
from typing import List, Dict, Optional, Tuple
from enum import Enum


class InstallMode(str, Enum):
    """Auto-install behavior modes."""
    ALWAYS = "always"    # Install without asking
    PROMPT = "prompt"    # Ask before installing (default)
    NEVER = "never"      # Never auto-install, just error


# Provider dependency mappings
PROVIDER_DEPS: Dict[str, List[str]] = {
    "gemini-api": ["google-generativeai"],
    "gemini-cli": [],  # Uses npx, no pip deps
    "claude-cli": [],  # Uses system claude command
    "ollama": ["numpy"],  # For embedding similarity
}

# Package to import name mapping (when different)
IMPORT_NAMES: Dict[str, str] = {
    "google-generativeai": "google.generativeai",
    "python-frontmatter": "frontmatter",
    "PyYAML": "yaml",
    "scikit-learn": "sklearn",
}

# Provider setup URLs
PROVIDER_URLS: Dict[str, str] = {
    "gemini-api": "https://aistudio.google.com/apikey",
    "ollama": "https://ollama.com/download",
    "gemini-cli": "https://github.com/anthropics/anthropic-cookbook",
}


def is_package_installed(package: str) -> bool:
    """Check if a Python package is installed."""
    import_name = IMPORT_NAMES.get(package, package.replace("-", "_"))

    # Handle nested imports like google.generativeai
    top_level = import_name.split(".")[0]
    return importlib.util.find_spec(top_level) is not None


def get_missing_deps(provider: str) -> List[str]:
    """Get list of missing dependencies for a provider."""
    deps = PROVIDER_DEPS.get(provider, [])
    return [d for d in deps if not is_package_installed(d)]


def install_packages(packages: List[str], quiet: bool = False) -> Tuple[bool, str]:
    """Install packages via pip.

    Args:
        packages: List of package names to install
        quiet: Suppress pip output

    Returns:
        Tuple of (success, message)
    """
    if not packages:
        return True, "No packages to install"

    cmd = [sys.executable, "-m", "pip", "install"] + packages
    if quiet:
        cmd.append("-q")

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=120
        )
        if result.returncode == 0:
            return True, f"Installed: {', '.join(packages)}"
        else:
            return False, f"pip error: {result.stderr}"
    except subprocess.TimeoutExpired:
        return False, "Installation timed out"
    except Exception as e:
        return False, f"Installation failed: {e}"


def prompt_install_choice(provider: str, missing: List[str]) -> str:
    """Prompt user for installation choice.

    Returns:
        "install" | "wizard" | "cancel"
    """
    print(f"\n📦 Provider '{provider}' needs: {', '.join(missing)}\n")
    print("   [I]nstall now  |  [S]etup wizard  |  [C]ancel\n")

    try:
        choice = input("> ").strip().lower()
        if choice in ("i", "install", ""):
            return "install"
        elif choice in ("s", "setup", "wizard"):
            return "wizard"
        else:
            return "cancel"
    except (KeyboardInterrupt, EOFError):
        print()
        return "cancel"


def ensure_provider_available(
    provider: str,
    mode: InstallMode = InstallMode.PROMPT
) -> Tuple[bool, str]:
    """Ensure a provider's dependencies are available.

    Args:
        provider: Provider name
        mode: Installation behavior mode

    Returns:
        Tuple of (available, message)
    """
    missing = get_missing_deps(provider)

    if not missing:
        return True, "Dependencies satisfied"

    # Never mode - just report what's missing
    if mode == InstallMode.NEVER:
        return False, (
            f"Missing packages for {provider}: {', '.join(missing)}\n"
            f"Install with: pip install {' '.join(missing)}"
        )

    # Always mode - install without asking
    if mode == InstallMode.ALWAYS:
        print(f"📦 Installing {', '.join(missing)}...")
        success, msg = install_packages(missing)
        if success:
            print(f"✓ {msg}")
        else:
            print(f"✗ {msg}")
        return success, msg

    # Prompt mode - ask user
    choice = prompt_install_choice(provider, missing)

    if choice == "install":
        print(f"\nInstalling {', '.join(missing)}...")
        success, msg = install_packages(missing)
        if success:
            print(f"✓ {msg}\n")
            # Check if API key needed
            return _check_api_key_needed(provider)
        else:
            print(f"✗ {msg}")
            return False, msg

    elif choice == "wizard":
        from .config import setup_wizard
        setup_wizard()
        # Re-check after wizard
        missing = get_missing_deps(provider)
        return len(missing) == 0, "Setup complete" if not missing else "Setup incomplete"

    else:
        return False, "Installation cancelled"


def _check_api_key_needed(provider: str) -> Tuple[bool, str]:
    """Check if provider needs an API key and prompt if missing."""
    import os
    from .config import get_config, save_config

    if provider == "gemini-api":
        key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
        if not key:
            print("🔑 GOOGLE_API_KEY not set.")
            print(f"   Get one free at: {PROVIDER_URLS['gemini-api']}")
            print()
            try:
                key = input("   Paste API key (or Enter to skip): ").strip()
                if key:
                    # Save to config for reference, but env var is preferred
                    print("\n   💡 Add to your shell profile:")
                    print(f'      export GOOGLE_API_KEY="{key}"')
                    print()
                    # Set for current session
                    os.environ["GOOGLE_API_KEY"] = key
                    return True, "API key configured"
            except (KeyboardInterrupt, EOFError):
                print()
            return True, "Packages installed (API key not set)"

    return True, "Ready"


def print_install_help(provider: str):
    """Print installation help for a provider."""
    deps = PROVIDER_DEPS.get(provider, [])
    url = PROVIDER_URLS.get(provider, "")

    print(f"\n📦 Setup '{provider}':\n")

    if deps:
        print(f"   pip install {' '.join(deps)}")

    if provider == "gemini-api":
        print(f"\n   Then set API key:")
        print(f"   export GOOGLE_API_KEY='your-key'")
        print(f"\n   Get a free key at: {url}")

    elif provider == "ollama":
        print(f"\n   Install Ollama:")
        print(f"   brew install ollama  # macOS")
        print(f"   # or visit: {url}")
        print(f"\n   Start server and pull models:")
        print(f"   ollama serve")
        print(f"   ollama pull nomic-embed-text llama3.1")

    elif provider == "gemini-cli":
        print(f"\n   Install via npm:")
        print(f"   npm install -g @google/gemini-cli")

    elif provider == "claude-cli":
        print(f"\n   Install Claude Code:")
        print(f"   https://claude.ai/code")

    print()
