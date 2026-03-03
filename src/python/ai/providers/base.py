"""
Base AI Provider interface.

All AI providers must implement this interface for consistent behavior
across Gemini API, Anthropic API, CLI tools, and local models.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Dict, Any
from enum import Enum

# Import shared models — all providers use these types
from ..models import AnalysisResult, ComparisonResult, SimilarNote


class ProviderType(Enum):
    """Type of AI provider."""
    API = "api"       # Direct API calls (fast, batch)
    CLI = "cli"       # CLI tool wrapper (simple, subscription)
    LOCAL = "local"   # Local model (free, private)


@dataclass
class ProviderCapabilities:
    """Capabilities of an AI provider."""
    embeddings: bool = False
    batch_embeddings: bool = False
    analysis: bool = False
    comparison: bool = False


class AIProvider(ABC):
    """Abstract base class for AI providers."""

    name: str = "base"
    provider_type: ProviderType = ProviderType.API
    capabilities: ProviderCapabilities = ProviderCapabilities()

    @abstractmethod
    def is_available(self) -> bool:
        """Check if provider is available and configured."""
        pass

    @abstractmethod
    def get_status(self) -> Dict[str, Any]:
        """Get provider status info."""
        pass

    # Embedding operations (API and Local only)
    def get_embedding(self, text: str) -> List[float]:
        """Get embedding vector for text."""
        raise NotImplementedError(f"{self.name} does not support embeddings")

    def get_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """Get embeddings for multiple texts."""
        return [self.get_embedding(t) for t in texts]

    # Analysis operations (all providers)
    @abstractmethod
    def analyze_note(self, content: str, title: str = "") -> AnalysisResult:
        """Analyze a note and return structured AnalysisResult."""
        pass

    # Comparison operations (all providers)
    @abstractmethod
    def compare_notes(
        self,
        note1_content: str,
        note2_content: str,
        note1_title: str = "",
        note2_title: str = ""
    ) -> ComparisonResult:
        """Compare two notes and return structured ComparisonResult."""
        pass

    # Utility methods
    def _truncate(self, text: str, max_chars: int = 2000) -> str:
        """Truncate text to max characters."""
        if len(text) <= max_chars:
            return text
        return text[:max_chars] + "..."

    def _extract_json(self, response: str) -> str:
        """Extract JSON object from a response that may contain extra text.

        Finds the first { ... } block. Used by CLI/Ollama providers
        before passing to Model.from_json().
        """
        start = response.find('{')
        end = response.rfind('}') + 1
        if start >= 0 and end > start:
            return response[start:end]
        raise ValueError(f"No JSON object found in response: {response[:100]}")
