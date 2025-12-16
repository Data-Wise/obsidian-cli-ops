"""
Gemini API Provider - Default provider for Obsidian CLI Ops.

Uses Google's Gemini API for:
- Embeddings (text-embedding-004)
- Analysis (gemini-2.5-flash)
- Batch processing

Free tier: 1000 RPD, 1M TPM
"""

import os
from typing import List, Dict, Any, Optional

from .base import (
    AIProvider, ProviderType, ProviderCapabilities,
    AnalysisResult, ComparisonResult
)


class GeminiAPIProvider(AIProvider):
    """Gemini API provider - fast, supports embeddings and batch."""

    name = "gemini-api"
    provider_type = ProviderType.API
    capabilities = ProviderCapabilities(
        embeddings=True,
        analysis=True,
        comparison=True,
        batch=True,
        streaming=True
    )

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "gemini-2.5-flash",
        embedding_model: str = "text-embedding-004"
    ):
        """Initialize Gemini API provider.

        Args:
            api_key: Google API key (or set GOOGLE_API_KEY env var)
            model: Model for analysis/comparison
            embedding_model: Model for embeddings
        """
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
        self.model = model
        self.embedding_model = embedding_model
        self._client = None

    def _get_client(self):
        """Lazy load the Gemini client."""
        if self._client is None:
            try:
                import google.generativeai as genai
                genai.configure(api_key=self.api_key)
                self._client = genai
            except ImportError:
                raise ImportError(
                    "google-generativeai not installed. "
                    "Install with: pip install google-generativeai"
                )
        return self._client

    def is_available(self) -> bool:
        """Check if Gemini API is available."""
        if not self.api_key:
            return False
        try:
            self._get_client()
            return True
        except Exception:
            return False

    def get_status(self) -> Dict[str, Any]:
        """Get provider status."""
        return {
            "name": self.name,
            "available": self.is_available(),
            "api_key_set": bool(self.api_key),
            "model": self.model,
            "embedding_model": self.embedding_model,
            "capabilities": {
                "embeddings": self.capabilities.embeddings,
                "batch": self.capabilities.batch,
            }
        }

    def get_embedding(self, text: str) -> List[float]:
        """Get embedding vector using Gemini."""
        client = self._get_client()
        result = client.embed_content(
            model=f"models/{self.embedding_model}",
            content=text,
            task_type="SEMANTIC_SIMILARITY"
        )
        return result['embedding']

    def get_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """Get embeddings for multiple texts efficiently."""
        client = self._get_client()
        results = []
        for text in texts:
            result = client.embed_content(
                model=f"models/{self.embedding_model}",
                content=text,
                task_type="SEMANTIC_SIMILARITY"
            )
            results.append(result['embedding'])
        return results

    def analyze_note(self, content: str, title: str = "") -> AnalysisResult:
        """Analyze a note using Gemini."""
        client = self._get_client()
        model = client.GenerativeModel(self.model)

        prompt = f"""Analyze this Obsidian note and extract key information.

Title: {title or "Untitled"}
---
{self._truncate(content)}

Extract and respond with ONLY valid JSON:
{{
    "topics": ["topic1", "topic2", "topic3"],
    "themes": ["theme1", "theme2"],
    "suggested_tags": ["tag1", "tag2"],
    "quality": {{"completeness": 7, "clarity": 8}},
    "suggestions": ["suggestion1", "suggestion2"]
}}"""

        response = model.generate_content(prompt)
        data = self._parse_json_response(
            response.text,
            {"topics": [], "themes": [], "suggested_tags": [], "quality": {}, "suggestions": []}
        )

        return AnalysisResult(
            topics=data.get("topics", []),
            themes=data.get("themes", []),
            suggested_tags=data.get("suggested_tags", []),
            quality=data.get("quality", {"completeness": 0, "clarity": 0}),
            suggestions=data.get("suggestions", []),
            raw_response=response.text
        )

    def compare_notes(
        self,
        note1_content: str,
        note2_content: str,
        note1_title: str = "",
        note2_title: str = ""
    ) -> ComparisonResult:
        """Compare two notes using Gemini."""
        client = self._get_client()
        model = client.GenerativeModel(self.model)

        prompt = f"""Compare these two Obsidian notes for similarity.

Note 1: {note1_title or "Untitled"}
---
{self._truncate(note1_content, 1000)}

Note 2: {note2_title or "Untitled"}
---
{self._truncate(note2_content, 1000)}

Analyze topic overlap, content similarity, and whether they should be merged.
Respond with ONLY valid JSON:
{{
    "similarity_score": 0.75,
    "reason": "Both notes discuss similar topics...",
    "should_merge": false,
    "merge_strategy": null
}}"""

        response = model.generate_content(prompt)
        data = self._parse_json_response(
            response.text,
            {"similarity_score": 0.0, "reason": "", "should_merge": False}
        )

        return ComparisonResult(
            similarity_score=float(data.get("similarity_score", 0.0)),
            reason=data.get("reason", ""),
            should_merge=data.get("should_merge", False),
            merge_strategy=data.get("merge_strategy")
        )
