"""
Shared structured output models for AI providers.

All providers return these dataclass types. API providers (Gemini, Anthropic)
can use native structured output; CLI/Ollama providers parse JSON into
dataclasses via from_json().

Design decisions:
- Dataclasses over Pydantic (zero new dependencies)
- from_json() ignores extra keys (LLMs often return unexpected fields)
- to_dict() for serialization
- Default values for all fields (graceful degradation on partial responses)
"""

from dataclasses import dataclass, field
from typing import List, Optional
import json


@dataclass
class AnalysisResult:
    """Result of AI note analysis.

    Used by: analyze_note(), summarize commands.
    """
    summary: str = ""
    themes: List[str] = field(default_factory=list)
    quality_score: float = 0.0  # 0.0-1.0
    suggestions: List[str] = field(default_factory=list)
    connections: List[str] = field(default_factory=list)

    @classmethod
    def from_json(cls, text: str) -> 'AnalysisResult':
        """Parse JSON string into AnalysisResult.

        Ignores extra keys from LLM responses. Raises ValueError
        on invalid JSON.
        """
        data = json.loads(text)
        if not isinstance(data, dict):
            raise ValueError(f"Expected JSON object, got {type(data).__name__}")
        filtered = {k: v for k, v in data.items() if k in cls.__dataclass_fields__}
        # Clamp quality_score to 0.0-1.0
        if 'quality_score' in filtered:
            try:
                score = float(filtered['quality_score'])
                filtered['quality_score'] = max(0.0, min(1.0, score))
            except (TypeError, ValueError):
                filtered['quality_score'] = 0.0
        return cls(**filtered)

    def to_dict(self) -> dict:
        """Serialize to dictionary."""
        return {k: getattr(self, k) for k in self.__dataclass_fields__}


@dataclass
class ComparisonResult:
    """Result of comparing two notes.

    Used by: compare_notes(), find_duplicates().
    """
    similarity_score: float = 0.0  # 0.0-1.0
    common_themes: List[str] = field(default_factory=list)
    differences: List[str] = field(default_factory=list)
    relationship: str = ""

    @classmethod
    def from_json(cls, text: str) -> 'ComparisonResult':
        """Parse JSON string into ComparisonResult."""
        data = json.loads(text)
        if not isinstance(data, dict):
            raise ValueError(f"Expected JSON object, got {type(data).__name__}")
        filtered = {k: v for k, v in data.items() if k in cls.__dataclass_fields__}
        # Clamp similarity_score to 0.0-1.0
        if 'similarity_score' in filtered:
            try:
                score = float(filtered['similarity_score'])
                filtered['similarity_score'] = max(0.0, min(1.0, score))
            except (TypeError, ValueError):
                filtered['similarity_score'] = 0.0
        return cls(**filtered)

    def to_dict(self) -> dict:
        """Serialize to dictionary."""
        return {k: getattr(self, k) for k in self.__dataclass_fields__}


@dataclass
class SimilarNote:
    """A note found to be similar to a query note.

    Used by: suggest-links, find_similar_notes().
    """
    note_id: int = 0
    title: str = ""
    similarity: float = 0.0
    reason: Optional[str] = None

    @classmethod
    def from_json(cls, text: str) -> 'SimilarNote':
        """Parse JSON string into SimilarNote."""
        data = json.loads(text)
        if not isinstance(data, dict):
            raise ValueError(f"Expected JSON object, got {type(data).__name__}")
        filtered = {k: v for k, v in data.items() if k in cls.__dataclass_fields__}
        return cls(**filtered)

    def to_dict(self) -> dict:
        """Serialize to dictionary."""
        return {k: getattr(self, k) for k in self.__dataclass_fields__}
