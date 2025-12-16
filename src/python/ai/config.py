"""
AI Configuration Management.

Handles:
- Provider preferences
- API keys (from env or config file)
- Model selection
- Persistence to ~/.config/obs/ai.json
"""

import os
import json
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Any


CONFIG_DIR = Path.home() / ".config" / "obs"
CONFIG_FILE = CONFIG_DIR / "ai.json"


@dataclass
class AIConfig:
    """AI configuration settings."""

    # Provider settings
    preferred_provider: Optional[str] = None
    provider_priority: List[str] = field(default_factory=lambda: [
        "gemini-api",
        "ollama",
        "gemini-cli",
        "claude-cli",
    ])

    # Model settings
    gemini_model: str = "gemini-2.5-flash"
    gemini_embedding_model: str = "text-embedding-004"
    ollama_chat_model: str = "llama3.1"
    ollama_embedding_model: str = "nomic-embed-text"

    # Connection settings
    ollama_base_url: str = "http://localhost:11434"
    timeout: int = 60

    # Feature flags
    auto_detect_providers: bool = True
    use_embeddings_for_similarity: bool = True

    # Installation behavior: "always" | "prompt" | "never"
    auto_install: str = "prompt"
    show_install_hints: bool = True

    @classmethod
    def load(cls) -> "AIConfig":
        """Load config from file or create default."""
        if CONFIG_FILE.exists():
            try:
                with open(CONFIG_FILE) as f:
                    data = json.load(f)
                return cls(**data)
            except (json.JSONDecodeError, TypeError):
                pass
        return cls()

    def save(self):
        """Save config to file."""
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        with open(CONFIG_FILE, 'w') as f:
            json.dump(asdict(self), f, indent=2)

    def get_api_key(self, provider: str) -> Optional[str]:
        """Get API key for a provider from environment.

        API keys are NOT stored in config file for security.
        They must be set as environment variables.
        """
        if provider in ("gemini-api", "gemini"):
            return os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
        elif provider in ("claude", "anthropic"):
            return os.getenv("ANTHROPIC_API_KEY")
        return None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


def get_config() -> AIConfig:
    """Get current AI configuration."""
    return AIConfig.load()


def save_config(config: AIConfig):
    """Save AI configuration."""
    config.save()


def print_status():
    """Print AI provider status to console."""
    from .router import AIRouter, PROVIDER_CLASSES
    from .install import get_missing_deps, PROVIDER_URLS

    config = get_config()
    router = AIRouter(
        priority=config.provider_priority,
        preferred_provider=config.preferred_provider,
    )

    print("🤖 AI Provider Status")
    print("━" * 40)
    print()

    status = router.get_status()

    # Table header
    print(f"{'Provider':<14} {'Status':<12} {'Capabilities':<20}")
    print("─" * 46)

    quick_fixes = []

    # Print each provider
    for name in config.provider_priority:
        prov = status["providers"].get(name, {})
        available = prov.get("available", False)
        icon = "✓" if available else "✗"
        color = "\033[32m" if available else "\033[31m"
        reset = "\033[0m"

        # Capabilities
        caps_list = []
        if available:
            caps = prov.get("capabilities", {})
            if caps.get("embeddings"):
                caps_list.append("embeddings")
            if caps.get("batch"):
                caps_list.append("batch")
            caps_str = ", ".join(caps_list) if caps_list else "analysis"
        else:
            # Show why not available
            missing = get_missing_deps(name)
            if missing:
                caps_str = f"needs: {', '.join(missing)}"
                quick_fixes.append((name, f"pip install {' '.join(missing)}"))
            elif name == "ollama":
                caps_str = "(not running)"
                quick_fixes.append((name, "ollama serve"))
            elif name == "gemini-api":
                caps_str = "(no API key)"
                quick_fixes.append((name, f"export GOOGLE_API_KEY=..."))
            else:
                caps_str = "(not installed)"

        print(f"{color}{icon}{reset} {name:<12} {caps_str:<20}")

    print()

    # API key status
    print("🔑 API Keys")
    for key_name, env_vars in [
        ("Gemini", ["GOOGLE_API_KEY", "GEMINI_API_KEY"]),
        ("Anthropic", ["ANTHROPIC_API_KEY"]),
    ]:
        found = any(os.getenv(v) for v in env_vars)
        icon = "✓" if found else "✗"
        color = "\033[32m" if found else "\033[33m"
        reset = "\033[0m"
        print(f"   {color}{icon}{reset} {key_name}: {'set' if found else 'not set'}")

    print()

    # Config info
    print(f"📁 Config: {CONFIG_FILE}")
    print(f"   preferred: {config.preferred_provider or '(auto)'}")
    print(f"   auto_install: {config.auto_install}")

    # Quick fixes
    if quick_fixes and config.show_install_hints:
        print()
        print("💡 Quick fixes:")
        for name, fix in quick_fixes[:3]:  # Show top 3
            print(f"   • {name}: {fix}")

    print()


def setup_wizard():
    """Interactive setup wizard for AI providers."""
    from .router import AIRouter, PROVIDER_CLASSES
    from .install import (
        get_missing_deps, install_packages,
        PROVIDER_DEPS, PROVIDER_URLS
    )

    print("🧙 AI Provider Setup")
    print("━" * 40)
    print()

    config = get_config()

    print("Scanning system...\n")

    # Check each provider
    provider_status = {}
    installable = []

    for idx, name in enumerate(config.provider_priority, 1):
        try:
            router = AIRouter(preferred_provider=name)
            router.refresh_availability()
            available = router._is_available(name)
        except Exception:
            available = False

        missing = get_missing_deps(name)
        provider_status[name] = {
            "available": available,
            "missing": missing,
            "idx": idx
        }

        status = "✓ available" if available else "✗ not available"
        color = "\033[32m" if available else "\033[31m"
        reset = "\033[0m"

        action = ""
        if not available and missing:
            action = f"[{idx}] Install"
            installable.append(name)
        elif not available and name == "ollama":
            action = f"[{idx}] Setup guide"
            installable.append(name)
        elif not available and name == "gemini-api":
            action = f"[{idx}] Configure"
            installable.append(name)

        print(f"  {color}{'✓' if available else '✗'}{reset} {name:<14} {action}")

    print()

    # Count available
    available_providers = [n for n, s in provider_status.items() if s["available"]]

    if available_providers:
        print(f"✓ {len(available_providers)} provider(s) ready: {', '.join(available_providers)}")
    else:
        print("⚠️  No providers available yet")

    if not installable:
        print("\nAll providers configured!")
        config.preferred_provider = available_providers[0] if available_providers else None
        config.save()
        print(f"\n✓ Using '{config.preferred_provider}' as default")
        return

    # Offer installation
    print()
    print("  [A]ll  [1-4] Select  [S]kip")
    print()

    try:
        choice = input("> ").strip().lower()
    except (KeyboardInterrupt, EOFError):
        print("\nSetup cancelled")
        return

    if choice == "s" or choice == "skip":
        print("\nSkipped installation")
    elif choice == "a" or choice == "all":
        # Install all missing deps
        all_missing = []
        for name in installable:
            all_missing.extend(get_missing_deps(name))
        if all_missing:
            print(f"\nInstalling: {', '.join(set(all_missing))}...")
            success, msg = install_packages(list(set(all_missing)))
            print(f"{'✓' if success else '✗'} {msg}")
        _prompt_api_keys()
    elif choice.isdigit():
        idx = int(choice)
        for name, status in provider_status.items():
            if status["idx"] == idx:
                missing = status["missing"]
                if missing:
                    print(f"\nInstalling: {', '.join(missing)}...")
                    success, msg = install_packages(missing)
                    print(f"{'✓' if success else '✗'} {msg}")
                if name == "gemini-api":
                    _prompt_api_keys()
                elif name == "ollama":
                    _print_ollama_setup()
                break

    # Re-check and save
    print()
    for name in config.provider_priority:
        try:
            router = AIRouter(preferred_provider=name)
            router.refresh_availability()
            if router._is_available(name):
                config.preferred_provider = name
                break
        except Exception:
            pass

    config.save()
    print(f"✓ Configuration saved to {CONFIG_FILE}")
    if config.preferred_provider:
        print(f"✓ Default provider: {config.preferred_provider}")
    print("\nRun 'obs ai status' to check anytime")


def _prompt_api_keys():
    """Prompt for API key setup."""
    import os

    if not os.getenv("GOOGLE_API_KEY") and not os.getenv("GEMINI_API_KEY"):
        print()
        print("🔑 Gemini API Key")
        print("   Get one free at: https://aistudio.google.com/apikey")
        print()
        try:
            key = input("   Paste key (or Enter to skip): ").strip()
            if key:
                os.environ["GOOGLE_API_KEY"] = key
                print()
                print("   💡 Add to your shell profile for persistence:")
                print(f'      export GOOGLE_API_KEY="{key}"')
        except (KeyboardInterrupt, EOFError):
            pass


def _print_ollama_setup():
    """Print Ollama setup instructions."""
    print()
    print("📦 Ollama Setup")
    print()
    print("   1. Install Ollama:")
    print("      brew install ollama  # macOS")
    print("      # or visit: https://ollama.com/download")
    print()
    print("   2. Start the server:")
    print("      ollama serve")
    print()
    print("   3. Pull required models:")
    print("      ollama pull nomic-embed-text  # embeddings")
    print("      ollama pull llama3.1          # analysis")
    print()


if __name__ == "__main__":
    print_status()
