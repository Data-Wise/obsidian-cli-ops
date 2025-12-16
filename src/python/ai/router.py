"""
AI Provider Router - Smart provider selection based on operation and availability.

Routing Strategy:
1. Embeddings → gemini-api (fast batch) > ollama (local) > error
2. Analysis → gemini-api > gemini-cli > claude-cli > ollama > error
3. Comparison → Same as analysis
4. Batch → gemini-api > ollama > sequential fallback

Priority Order (configurable):
1. gemini-api (default, fast, embeddings)
2. gemini-cli (fallback, no embeddings)
3. claude-cli (high quality, slow)
4. ollama (local, free, private)
"""

from typing import List, Dict, Any, Optional, Type
from enum import Enum

from .providers.base import (
    AIProvider, ProviderCapabilities,
    AnalysisResult, ComparisonResult
)
from .providers.gemini_api import GeminiAPIProvider
from .providers.gemini_cli import GeminiCLIProvider
from .providers.claude_cli import ClaudeCLIProvider
from .providers.ollama import OllamaProvider


class OperationType(str, Enum):
    """Types of AI operations."""
    EMBEDDING = "embedding"
    EMBEDDINGS_BATCH = "embeddings_batch"
    ANALYSIS = "analysis"
    COMPARISON = "comparison"


# Default provider priority
DEFAULT_PRIORITY = [
    "gemini-api",
    "ollama",
    "gemini-cli",
    "claude-cli",
]

# Provider classes
PROVIDER_CLASSES: Dict[str, Type[AIProvider]] = {
    "gemini-api": GeminiAPIProvider,
    "gemini-cli": GeminiCLIProvider,
    "claude-cli": ClaudeCLIProvider,
    "ollama": OllamaProvider,
}


class AIRouter:
    """Smart router for AI provider selection."""

    def __init__(
        self,
        priority: Optional[List[str]] = None,
        preferred_provider: Optional[str] = None,
        **provider_kwargs
    ):
        """Initialize router with provider priority.

        Args:
            priority: List of provider names in priority order
            preferred_provider: Override to always use this provider
            **provider_kwargs: Arguments passed to provider constructors
        """
        self.priority = priority or DEFAULT_PRIORITY
        self.preferred_provider = preferred_provider
        self.provider_kwargs = provider_kwargs
        self._providers: Dict[str, AIProvider] = {}
        self._availability_cache: Dict[str, bool] = {}

    def _get_provider(self, name: str) -> AIProvider:
        """Get or create a provider instance."""
        if name not in self._providers:
            if name not in PROVIDER_CLASSES:
                raise ValueError(f"Unknown provider: {name}")
            self._providers[name] = PROVIDER_CLASSES[name](**self.provider_kwargs)
        return self._providers[name]

    def _is_available(self, name: str) -> bool:
        """Check if provider is available (cached)."""
        if name not in self._availability_cache:
            try:
                provider = self._get_provider(name)
                self._availability_cache[name] = provider.is_available()
            except Exception:
                self._availability_cache[name] = False
        return self._availability_cache[name]

    def refresh_availability(self):
        """Clear availability cache and recheck."""
        self._availability_cache.clear()

    def get_provider_for_operation(
        self,
        operation: OperationType
    ) -> Optional[AIProvider]:
        """Get the best available provider for an operation.

        Args:
            operation: The type of operation to perform

        Returns:
            Best available provider or None
        """
        # If preferred provider set, try it first
        if self.preferred_provider:
            if self._is_available(self.preferred_provider):
                provider = self._get_provider(self.preferred_provider)
                if self._supports_operation(provider, operation):
                    return provider

        # Find first available provider that supports the operation
        for name in self.priority:
            if self._is_available(name):
                provider = self._get_provider(name)
                if self._supports_operation(provider, operation):
                    return provider

        return None

    def _supports_operation(
        self,
        provider: AIProvider,
        operation: OperationType
    ) -> bool:
        """Check if provider supports an operation."""
        caps = provider.capabilities
        if operation == OperationType.EMBEDDING:
            return caps.embeddings
        elif operation == OperationType.EMBEDDINGS_BATCH:
            return caps.embeddings and caps.batch
        elif operation == OperationType.ANALYSIS:
            return caps.analysis
        elif operation == OperationType.COMPARISON:
            return caps.comparison
        return False

    def get_status(self) -> Dict[str, Any]:
        """Get status of all providers."""
        status = {
            "priority": self.priority,
            "preferred": self.preferred_provider,
            "providers": {}
        }

        for name in PROVIDER_CLASSES:
            try:
                provider = self._get_provider(name)
                status["providers"][name] = provider.get_status()
            except Exception as e:
                status["providers"][name] = {
                    "name": name,
                    "available": False,
                    "error": str(e)
                }

        return status

    # Convenience methods that route automatically

    def get_embedding(self, text: str) -> List[float]:
        """Get embedding using best available provider."""
        provider = self.get_provider_for_operation(OperationType.EMBEDDING)
        if not provider:
            raise RuntimeError(
                "No provider available for embeddings. "
                "Configure gemini-api or ollama."
            )
        return provider.get_embedding(text)

    def get_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """Get batch embeddings using best available provider."""
        provider = self.get_provider_for_operation(OperationType.EMBEDDINGS_BATCH)
        if provider:
            return provider.get_embeddings_batch(texts)

        # Fallback to sequential if no batch provider
        provider = self.get_provider_for_operation(OperationType.EMBEDDING)
        if not provider:
            raise RuntimeError("No provider available for embeddings.")
        return [provider.get_embedding(text) for text in texts]

    def analyze_note(self, content: str, title: str = "") -> AnalysisResult:
        """Analyze note using best available provider."""
        provider = self.get_provider_for_operation(OperationType.ANALYSIS)
        if not provider:
            raise RuntimeError(
                "No provider available for analysis. "
                "Configure gemini-api, gemini-cli, claude-cli, or ollama."
            )
        return provider.analyze_note(content, title)

    def compare_notes(
        self,
        note1_content: str,
        note2_content: str,
        note1_title: str = "",
        note2_title: str = ""
    ) -> ComparisonResult:
        """Compare notes using best available provider."""
        provider = self.get_provider_for_operation(OperationType.COMPARISON)
        if not provider:
            raise RuntimeError(
                "No provider available for comparison. "
                "Configure gemini-api, gemini-cli, claude-cli, or ollama."
            )
        return provider.compare_notes(
            note1_content, note2_content,
            note1_title, note2_title
        )


# Singleton instance
_router: Optional[AIRouter] = None


def get_ai_client(
    provider: Optional[str] = None,
    **kwargs
) -> AIRouter:
    """Get AI client (router) instance.

    This is the main entry point for AI operations.

    Args:
        provider: Preferred provider name (optional)
        **kwargs: Arguments passed to providers

    Returns:
        AIRouter instance

    Examples:
        # Auto-select best provider
        client = get_ai_client()
        embedding = client.get_embedding("some text")

        # Force specific provider
        client = get_ai_client(provider="ollama")

        # With configuration
        client = get_ai_client(
            api_key="...",
            base_url="http://localhost:11434"
        )
    """
    global _router

    # Create new router if needed or if provider preference changed
    if _router is None or provider != _router.preferred_provider:
        _router = AIRouter(
            preferred_provider=provider,
            **kwargs
        )

    return _router
