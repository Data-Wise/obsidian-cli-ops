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

from .base import AIProvider, ProviderType, ProviderCapabilities
from ..models import AnalysisResult, ComparisonResult

# JSON schema templates for prompts
_ANALYSIS_SCHEMA = '''{
    "summary": "Brief summary of the note",
    "themes": ["theme1", "theme2"],
    "quality_score": 0.8,
    "suggestions": ["suggestion1", "suggestion2"],
    "connections": ["related topic 1", "related topic 2"]
}'''

_COMPARISON_SCHEMA = '''{
    "similarity_score": 0.75,
    "common_themes": ["shared theme 1"],
    "differences": ["key difference 1"],
    "relationship": "complementary notes on the same topic"
}'''


class GeminiAPIProvider(AIProvider):
    """Gemini API provider - fast, supports embeddings and batch."""

    name = "gemini-api"
    provider_type = ProviderType.API
    capabilities = ProviderCapabilities(
        embeddings=True,
        batch_embeddings=True,
        analysis=True,
        comparison=True,
    )

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "gemini-2.5-flash",
        embedding_model: str = "text-embedding-004",
        **kwargs,
    ):
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
        self.model = model
        self.embedding_model = embedding_model
        self._client = None

    def _get_client(self):
        """Lazy load the Gemini client (new google-genai SDK)."""
        if self._client is None:
            try:
                from google import genai
                self._client = genai.Client(api_key=self.api_key)
            except ImportError:
                raise ImportError(
                    "google-genai not installed. "
                    "Install with: pip install google-genai"
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
                "batch_embeddings": self.capabilities.batch_embeddings,
            }
        }

    def get_embedding(self, text: str) -> List[float]:
        """Get embedding vector using Gemini."""
        client = self._get_client()
        result = client.models.embed_content(
            model=self.embedding_model,
            contents=text,
        )
        return result.embeddings[0].values

    def get_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """Get embeddings for multiple texts in a true batch call."""
        client = self._get_client()
        result = client.models.embed_content(
            model=self.embedding_model,
            contents=texts,
        )
        return [e.values for e in result.embeddings]

    def analyze_note(self, content: str, title: str = "") -> AnalysisResult:
        """Analyze a note using Gemini with structured output."""
        client = self._get_client()
        from google import genai

        prompt = f"""Analyze this Obsidian note and extract key information.

Title: {title or "Untitled"}
---
{self._truncate(content)}

Respond with ONLY valid JSON matching this schema:
{_ANALYSIS_SCHEMA}"""

        response = client.models.generate_content(
            model=self.model,
            contents=prompt,
            config=genai.types.GenerateContentConfig(
                response_mime_type="application/json",
            ),
        )
        return AnalysisResult.from_json(response.text)

    def compare_notes(
        self,
        note1_content: str,
        note2_content: str,
        note1_title: str = "",
        note2_title: str = ""
    ) -> ComparisonResult:
        """Compare two notes using Gemini with structured output."""
        client = self._get_client()
        from google import genai

        prompt = f"""Compare these two Obsidian notes for similarity.

Note 1: {note1_title or "Untitled"}
---
{self._truncate(note1_content, 1000)}

Note 2: {note2_title or "Untitled"}
---
{self._truncate(note2_content, 1000)}

Analyze topic overlap, content similarity, and their relationship.
Respond with ONLY valid JSON matching this schema:
{_COMPARISON_SCHEMA}"""

        response = client.models.generate_content(
            model=self.model,
            contents=prompt,
            config=genai.types.GenerateContentConfig(
                response_mime_type="application/json",
            ),
        )
        return ComparisonResult.from_json(response.text)
