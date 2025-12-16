"""Tests for AI router module."""

import pytest
from unittest.mock import patch, MagicMock
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(__file__).rsplit('/', 2)[0])

from ai.router import (
    AIRouter,
    OperationType,
    PROVIDER_CLASSES,
    DEFAULT_PRIORITY,
    get_ai_client,
)


class TestOperationType:
    """Tests for OperationType enum."""

    def test_operation_types(self):
        """Test all operation types exist."""
        assert OperationType.EMBEDDING == "embedding"
        assert OperationType.EMBEDDINGS_BATCH == "embeddings_batch"
        assert OperationType.ANALYSIS == "analysis"
        assert OperationType.COMPARISON == "comparison"


class TestProviderClasses:
    """Tests for provider class registry."""

    def test_all_providers_registered(self):
        """Test all expected providers are registered."""
        assert "gemini-api" in PROVIDER_CLASSES
        assert "gemini-cli" in PROVIDER_CLASSES
        assert "claude-cli" in PROVIDER_CLASSES
        assert "ollama" in PROVIDER_CLASSES

    def test_provider_classes_are_types(self):
        """Test provider classes are actual types."""
        for name, cls in PROVIDER_CLASSES.items():
            assert isinstance(cls, type), f"{name} should be a class"


class TestDefaultPriority:
    """Tests for default provider priority."""

    def test_default_priority_order(self):
        """Test default priority order."""
        assert DEFAULT_PRIORITY == [
            "gemini-api",
            "ollama",
            "gemini-cli",
            "claude-cli",
        ]


class TestAIRouter:
    """Tests for AIRouter class."""

    def test_init_default(self):
        """Test router initialization with defaults."""
        router = AIRouter()

        assert router.priority == DEFAULT_PRIORITY
        assert router.preferred_provider is None
        assert router._providers == {}
        assert router._availability_cache == {}

    def test_init_custom_priority(self):
        """Test router with custom priority."""
        custom = ["ollama", "claude-cli"]
        router = AIRouter(priority=custom)

        assert router.priority == custom

    def test_init_preferred_provider(self):
        """Test router with preferred provider."""
        router = AIRouter(preferred_provider="ollama")

        assert router.preferred_provider == "ollama"

    def test_get_provider_unknown(self):
        """Test getting unknown provider raises error."""
        router = AIRouter()

        with pytest.raises(ValueError, match="Unknown provider"):
            router._get_provider("unknown-provider")

    def test_get_provider_creates_instance(self):
        """Test getting provider creates instance."""
        router = AIRouter()

        provider = router._get_provider("gemini-api")

        assert provider is not None
        assert "gemini-api" in router._providers

    def test_get_provider_cached(self):
        """Test provider instances are cached."""
        router = AIRouter()

        provider1 = router._get_provider("gemini-api")
        provider2 = router._get_provider("gemini-api")

        assert provider1 is provider2

    def test_refresh_availability(self):
        """Test refreshing availability cache."""
        router = AIRouter()
        router._availability_cache = {"test": True}

        router.refresh_availability()

        assert router._availability_cache == {}

    def test_get_status(self):
        """Test getting router status."""
        router = AIRouter()
        status = router.get_status()

        assert "priority" in status
        assert "preferred" in status
        assert "providers" in status
        assert isinstance(status["providers"], dict)

    def test_supports_operation_embeddings(self):
        """Test checking embedding support."""
        router = AIRouter()

        # GeminiAPI supports embeddings
        provider = router._get_provider("gemini-api")
        assert router._supports_operation(provider, OperationType.EMBEDDING)

        # ClaudeCLI doesn't support embeddings
        provider = router._get_provider("claude-cli")
        assert not router._supports_operation(provider, OperationType.EMBEDDING)

    def test_supports_operation_analysis(self):
        """Test checking analysis support."""
        router = AIRouter()

        # All providers support analysis
        for name in PROVIDER_CLASSES:
            provider = router._get_provider(name)
            assert router._supports_operation(provider, OperationType.ANALYSIS)


class TestGetAIClient:
    """Tests for get_ai_client function."""

    def test_returns_router(self):
        """Test get_ai_client returns AIRouter."""
        # Reset singleton
        import ai.router
        ai.router._router = None

        client = get_ai_client()

        assert isinstance(client, AIRouter)

    def test_singleton_behavior(self):
        """Test get_ai_client returns same instance."""
        import ai.router
        ai.router._router = None

        client1 = get_ai_client()
        client2 = get_ai_client()

        assert client1 is client2

    def test_new_instance_on_provider_change(self):
        """Test new instance created when provider changes."""
        import ai.router
        ai.router._router = None

        client1 = get_ai_client(provider="gemini-api")
        client2 = get_ai_client(provider="ollama")

        assert client1 is not client2
        assert client2.preferred_provider == "ollama"
