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

    config = get_config()
    router = AIRouter(
        priority=config.provider_priority,
        preferred_provider=config.preferred_provider,
    )

    print("🤖 AI Provider Status\n")
    print(f"Config file: {CONFIG_FILE}")
    print(f"Preferred: {config.preferred_provider or '(auto)'}")
    print(f"Priority: {' → '.join(config.provider_priority)}\n")

    status = router.get_status()

    # Print each provider
    for name in config.provider_priority:
        prov = status["providers"].get(name, {})
        available = prov.get("available", False)
        icon = "✓" if available else "✗"
        color_start = "\033[32m" if available else "\033[31m"
        color_end = "\033[0m"

        print(f"{color_start}{icon}{color_end} {name}")

        if available:
            caps = prov.get("capabilities", {})
            features = []
            if caps.get("embeddings"):
                features.append("embeddings")
            if caps.get("batch"):
                features.append("batch")
            if features:
                print(f"    Features: {', '.join(features)}")

            # Provider-specific info
            if "model" in prov:
                print(f"    Model: {prov['model']}")
            if "embedding_model" in prov:
                print(f"    Embedding: {prov['embedding_model']}")
            if "models_available" in prov and prov["models_available"]:
                print(f"    Ollama models: {len(prov['models_available'])}")
        else:
            error = prov.get("error", "Not configured")
            print(f"    Status: {error}")

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
        print(f"  {color}{icon}\033[0m {key_name}: {'set' if found else 'not set'}")

    print()


def setup_wizard():
    """Interactive setup wizard for AI providers."""
    print("🧙 AI Provider Setup Wizard\n")

    config = get_config()

    # Check what's available
    from .router import AIRouter, PROVIDER_CLASSES

    print("Checking available providers...\n")

    available = []
    for name in PROVIDER_CLASSES:
        try:
            router = AIRouter(preferred_provider=name)
            router.refresh_availability()
            if router._is_available(name):
                available.append(name)
                print(f"  ✓ {name} is available")
            else:
                print(f"  ✗ {name} not available")
        except Exception as e:
            print(f"  ✗ {name} error: {e}")

    if not available:
        print("\n⚠️  No providers available!")
        print("\nSetup options:")
        print("  1. Set GOOGLE_API_KEY for Gemini API (recommended)")
        print("  2. Install Ollama for local AI:")
        print("     brew install ollama && ollama serve")
        print("     ollama pull nomic-embed-text llama3.1")
        print("  3. Install Gemini CLI:")
        print("     npm install -g @google/gemini-cli")
        return

    print(f"\n✓ {len(available)} provider(s) available: {', '.join(available)}")

    # Set preferred provider
    if len(available) == 1:
        config.preferred_provider = available[0]
    else:
        # Default to gemini-api if available, otherwise first available
        if "gemini-api" in available:
            config.preferred_provider = "gemini-api"
        else:
            config.preferred_provider = available[0]

    print(f"\nUsing '{config.preferred_provider}' as default provider")

    # Save config
    config.save()
    print(f"\n✓ Configuration saved to {CONFIG_FILE}")


if __name__ == "__main__":
    print_status()
