"""
Base AI Provider interface.

All AI providers must implement this interface for consistent behavior
across Gemini API, CLI tools, and local models.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from enum import Enum


class ProviderType(Enum):
    """Type of AI provider."""
    API = "api"       # Direct API calls (fast, batch)
    CLI = "cli"       # CLI tool wrapper (simple, subscription)
    LOCAL = "local"   # Local model (free, private)


@dataclass
class ProviderCapabilities:
    """Capabilities of an AI provider."""
    embeddings: bool = False
    analysis: bool = False
    comparison: bool = False
    batch: bool = False
    streaming: bool = False


@dataclass
class AnalysisResult:
    """Result of note analysis."""
    topics: List[str] = field(default_factory=list)
    themes: List[str] = field(default_factory=list)
    suggested_tags: List[str] = field(default_factory=list)
    quality: Dict[str, int] = field(default_factory=lambda: {"completeness": 0, "clarity": 0})
    suggestions: List[str] = field(default_factory=list)
    raw_response: Optional[str] = None


@dataclass
class ComparisonResult:
    """Result of note comparison."""
    similarity_score: float = 0.0
    reason: str = ""
    should_merge: bool = False
    merge_strategy: Optional[str] = None


@dataclass
class SimilarNote:
    """A similar note with score."""
    note_id: str
    title: str
    score: float
    reason: Optional[str] = None


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
        """Analyze a note for topics, themes, and suggestions."""
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
        """Compare two notes for similarity."""
        pass

    # Utility methods
    def _truncate(self, text: str, max_chars: int = 2000) -> str:
        """Truncate text to max characters."""
        if len(text) <= max_chars:
            return text
        return text[:max_chars] + "..."

    def _parse_json_response(self, response: str, default: Dict) -> Dict:
        """Safely parse JSON from response."""
        import json
        try:
            # Try to find JSON in response
            start = response.find('{')
            end = response.rfind('}') + 1
            if start >= 0 and end > start:
                return json.loads(response[start:end])
        except json.JSONDecodeError:
            pass
        return default
