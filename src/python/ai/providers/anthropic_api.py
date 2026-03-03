"""
Anthropic API Provider - Direct Claude API access via official SDK.

Best for:
- High-quality analysis (Claude's reasoning)
- Complex note comparisons
- When you have an Anthropic API key

Limitations:
- No embeddings (Anthropic doesn't offer them — use Gemini/Ollama)
- Paid API (no free tier)
- API key required via ANTHROPIC_API_KEY env var
"""

import os
from typing import List, Dict, Any, Optional

from .base import AIProvider, ProviderType, ProviderCapabilities, retry_with_backoff
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


class AnthropicAPIProvider(AIProvider):
    """Direct Anthropic API provider using official SDK."""

    name = "anthropic-api"
    provider_type = ProviderType.API
    capabilities = ProviderCapabilities(
        embeddings=False,
        batch_embeddings=False,
        analysis=True,
        comparison=True,
    )

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "claude-sonnet-4-6",
        max_tokens: int = 1024,
        **kwargs,
    ):
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        self.model = model
        self.max_tokens = max_tokens
        self._client = None

    def _get_client(self):
        """Lazy load the Anthropic client."""
        if self._client is None:
            try:
                import anthropic
                self._client = anthropic.Anthropic(api_key=self.api_key)
            except ImportError:
                raise ImportError(
                    "anthropic not installed. "
                    "Install with: pip install anthropic"
                )
        return self._client

    def is_available(self) -> bool:
        """Check if Anthropic API is available."""
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
            "capabilities": {
                "embeddings": self.capabilities.embeddings,
                "batch_embeddings": self.capabilities.batch_embeddings,
            }
        }

    @retry_with_backoff(max_retries=3, base_delay=1.0)
    def analyze_note(self, content: str, title: str = "") -> AnalysisResult:
        """Analyze a note using Anthropic Claude API."""
        client = self._get_client()

        prompt = f"""Analyze this Obsidian note and extract key information.

Title: {title or "Untitled"}
---
{self._truncate(content)}

Respond with ONLY valid JSON matching this schema:
{_ANALYSIS_SCHEMA}"""

        response = client.messages.create(
            model=self.model,
            max_tokens=self.max_tokens,
            messages=[{"role": "user", "content": prompt}],
        )
        text = response.content[0].text
        json_str = self._extract_json(text)
        return AnalysisResult.from_json(json_str)

    @retry_with_backoff(max_retries=3, base_delay=1.0)
    def compare_notes(
        self,
        note1_content: str,
        note2_content: str,
        note1_title: str = "",
        note2_title: str = ""
    ) -> ComparisonResult:
        """Compare two notes using Anthropic Claude API."""
        client = self._get_client()

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

        response = client.messages.create(
            model=self.model,
            max_tokens=self.max_tokens,
            messages=[{"role": "user", "content": prompt}],
        )
        text = response.content[0].text
        json_str = self._extract_json(text)
        return ComparisonResult.from_json(json_str)
