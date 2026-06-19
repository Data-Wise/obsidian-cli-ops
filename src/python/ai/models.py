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
from typing import Any, Dict, List, Optional
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


# --- v3.2.0 Quality Feature Models ---


@dataclass
class MergeCandidate:
    """A pair of notes identified as potential merge candidates.

    Used by: merge_suggest_vault(), merge_suggest_note().
    Constructed from embedding similarity + DB enrichment (not LLM output).
    """
    note_a_id: str = ""
    note_b_id: str = ""
    note_a_title: str = ""
    note_b_title: str = ""
    similarity: float = 0.0           # 0.0-1.0 cosine similarity
    shared_links: List[str] = field(default_factory=list)
    shared_tags: List[str] = field(default_factory=list)
    overlapping_sections: List[str] = field(default_factory=list)
    suggested_target: str = ""        # which note to keep
    confidence: float = 0.0           # 0.0-1.0

    @classmethod
    def from_json(cls, text: str) -> 'MergeCandidate':
        """Parse JSON string into MergeCandidate."""
        data = json.loads(text)
        if not isinstance(data, dict):
            raise ValueError(f"Expected JSON object, got {type(data).__name__}")
        return cls.from_dict(data)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MergeCandidate':
        """Create from dictionary, ignoring unknown keys."""
        filtered = {k: v for k, v in data.items() if k in cls.__dataclass_fields__}
        for key in ('similarity', 'confidence'):
            if key in filtered:
                try:
                    score = float(filtered[key])
                    filtered[key] = max(0.0, min(1.0, score))
                except (TypeError, ValueError):
                    filtered[key] = 0.0
        return cls(**filtered)

    def to_dict(self) -> dict:
        """Serialize to dictionary."""
        return {k: getattr(self, k) for k in self.__dataclass_fields__}


@dataclass
class TagSuggestion:
    """Tag suggestions for a note based on content and vault context.

    Used by: tag_suggest_vault(), tag_suggest_note().
    suggested_tags entries: {"tag": str, "confidence": float, "vault_usage_count": int}
    """
    note_id: str = ""
    note_title: str = ""
    suggested_tags: List[Dict[str, Any]] = field(default_factory=list)
    existing_tags: List[str] = field(default_factory=list)
    neighbor_tags: List[str] = field(default_factory=list)

    @classmethod
    def from_json(cls, text: str) -> 'TagSuggestion':
        """Parse JSON string into TagSuggestion."""
        data = json.loads(text)
        if not isinstance(data, dict):
            raise ValueError(f"Expected JSON object, got {type(data).__name__}")
        return cls.from_dict(data)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TagSuggestion':
        """Create from dictionary, ignoring unknown keys."""
        filtered = {k: v for k, v in data.items() if k in cls.__dataclass_fields__}
        # Clamp confidence in each suggested tag
        if 'suggested_tags' in filtered:
            for tag_entry in filtered['suggested_tags']:
                if isinstance(tag_entry, dict) and 'confidence' in tag_entry:
                    try:
                        tag_entry['confidence'] = max(0.0, min(1.0, float(tag_entry['confidence'])))
                    except (TypeError, ValueError):
                        tag_entry['confidence'] = 0.0
        return cls(**filtered)

    def to_dict(self) -> dict:
        """Serialize to dictionary."""
        return {k: getattr(self, k) for k in self.__dataclass_fields__}


# --- v3.4.0 Bridge + Temporal Models ---


@dataclass
class BridgeStatus:
    """Status of the Obsidian CLI bridge connection.

    Used by: obs bridge status.
    cli_installed: obsidian binary found and responds to --version.
    app_running: a vault-level command succeeded (requires app IPC).
    capabilities: commands available given current status.
    """
    cli_installed: bool = False
    cli_version: str = ""
    app_running: bool = False
    capabilities: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Serialize to dictionary."""
        return {k: getattr(self, k) for k in self.__dataclass_fields__}


@dataclass
class TrendBucket:
    """Activity counts for one ISO week.

    Used by: TrendReport.buckets.
    week: ISO week label "YYYY-WNN" (e.g. "2026-W24").
    """
    week: str = ""
    notes_created: int = 0
    notes_modified: int = 0

    def to_dict(self) -> dict:
        """Serialize to dictionary."""
        return {k: getattr(self, k) for k in self.__dataclass_fields__}


@dataclass
class TrendReport:
    """Weekly activity trend report for a vault.

    Used by: obs trends.
    insufficient_data: True when fewer than 2 weeks of data.
    velocity_notes_per_week: average notes created per week.
    """
    vault_id: str = ""
    total_notes: int = 0
    lookback_days: int = 90
    buckets: List[TrendBucket] = field(default_factory=list)
    velocity_notes_per_week: float = 0.0
    insufficient_data: bool = False

    def to_dict(self) -> dict:
        """Serialize to dictionary."""
        d = {k: getattr(self, k) for k in self.__dataclass_fields__}
        d['buckets'] = [b.to_dict() for b in self.buckets]
        return d


@dataclass
class StaleNote:
    """A note ranked by importance-weighted staleness.

    staleness_score = pagerank × (days_since_modified / 365).
    Falls back to days_since_modified / 365 when pagerank unavailable.
    """
    note_id: str = ""
    title: str = ""
    path: str = ""
    days_since_modified: int = 0
    pagerank: float = 0.0
    staleness_score: float = 0.0

    def to_dict(self) -> dict:
        """Serialize to dictionary."""
        return {k: getattr(self, k) for k in self.__dataclass_fields__}


@dataclass
class StaleReport:
    """Report of stale notes for a vault.

    Used by: obs stale.
    has_graph_metrics: False means staleness_score is date-only (no PageRank).
    """
    vault_id: str = ""
    notes: List[StaleNote] = field(default_factory=list)
    has_graph_metrics: bool = False

    def to_dict(self) -> dict:
        """Serialize to dictionary."""
        d = {k: getattr(self, k) for k in self.__dataclass_fields__}
        d['notes'] = [n.to_dict() for n in self.notes]
        return d


@dataclass
class DigestReport:
    """Combined daily-digest: bridge status + trends + top stale notes.

    Used by: obs daily-digest.
    stale_limit: how many stale notes were requested (default 5).
    """
    vault_id: str = ""
    stale_limit: int = 5
    bridge: BridgeStatus = field(default_factory=BridgeStatus)
    trends: TrendReport = field(default_factory=TrendReport)
    stale: StaleReport = field(default_factory=StaleReport)

    def to_dict(self) -> dict:
        """Serialize to dictionary."""
        return {
            "vault_id": self.vault_id,
            "stale_limit": self.stale_limit,
            "bridge": self.bridge.to_dict(),
            "trends": self.trends.to_dict(),
            "stale": self.stale.to_dict(),
        }


@dataclass
class NoteQuality:
    """Quality score for a single note across multiple dimensions.

    Used by: note_quality_vault(), note_quality_note().
    dimensions: {"completeness": float, "connectivity": float,
                 "metadata": float, "freshness": float} (each 0-100)
    issues entries: {"severity": str, "description": str}
    """
    note_id: str = ""
    note_title: str = ""
    overall_score: float = 0.0        # 0-100
    dimensions: Dict[str, float] = field(default_factory=dict)
    issues: List[Dict[str, str]] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)

    @classmethod
    def from_json(cls, text: str) -> 'NoteQuality':
        """Parse JSON string into NoteQuality."""
        data = json.loads(text)
        if not isinstance(data, dict):
            raise ValueError(f"Expected JSON object, got {type(data).__name__}")
        return cls.from_dict(data)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'NoteQuality':
        """Create from dictionary, ignoring unknown keys."""
        filtered = {k: v for k, v in data.items() if k in cls.__dataclass_fields__}
        # Clamp overall_score to 0-100
        if 'overall_score' in filtered:
            try:
                score = float(filtered['overall_score'])
                filtered['overall_score'] = max(0.0, min(100.0, score))
            except (TypeError, ValueError):
                filtered['overall_score'] = 0.0
        # Clamp dimension scores to 0-100
        if 'dimensions' in filtered and isinstance(filtered['dimensions'], dict):
            for dim_key, dim_val in filtered['dimensions'].items():
                try:
                    filtered['dimensions'][dim_key] = max(0.0, min(100.0, float(dim_val)))
                except (TypeError, ValueError):
                    filtered['dimensions'][dim_key] = 0.0
        return cls(**filtered)

    def to_dict(self) -> dict:
        """Serialize to dictionary."""
        return {k: getattr(self, k) for k in self.__dataclass_fields__}
