"""
Ollama Provider - Free local AI for embeddings and analysis.

Best for:
- Privacy-first (100% local)
- Free unlimited usage
- Embeddings (nomic-embed-text)
- Offline capability

Requirements:
- Ollama installed: brew install ollama
- Models pulled: ollama pull nomic-embed-text && ollama pull llama3.1
"""

import requests
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


class OllamaProvider(AIProvider):
    """Ollama provider - free local AI."""

    name = "ollama"
    provider_type = ProviderType.LOCAL
    capabilities = ProviderCapabilities(
        embeddings=True,
        batch_embeddings=True,
        analysis=True,
        comparison=True,
    )

    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        embedding_model: str = "nomic-embed-text",
        chat_model: str = "llama3.1",
        timeout: int = 60,
        **kwargs,
    ):
        self.base_url = base_url.rstrip('/')
        self.embedding_model = embedding_model
        self.chat_model = chat_model
        self.timeout = timeout

    def _check_model(self, model_name: str) -> bool:
        """Check if model is available."""
        try:
            response = requests.get(
                f"{self.base_url}/api/tags",
                timeout=5
            )
            response.raise_for_status()
            models = response.json().get('models', [])
            return any(m['name'].startswith(model_name) for m in models)
        except Exception:
            return False

    def is_available(self) -> bool:
        """Check if Ollama is running."""
        try:
            response = requests.get(
                f"{self.base_url}/api/tags",
                timeout=5
            )
            return response.status_code == 200
        except Exception:
            return False

    def get_status(self) -> Dict[str, Any]:
        """Get provider status."""
        available = self.is_available()
        models = []
        if available:
            try:
                response = requests.get(f"{self.base_url}/api/tags", timeout=5)
                models = [m['name'] for m in response.json().get('models', [])]
            except Exception:
                pass

        return {
            "name": self.name,
            "available": available,
            "base_url": self.base_url,
            "embedding_model": self.embedding_model,
            "chat_model": self.chat_model,
            "models_available": models,
            "has_embedding_model": self._check_model(self.embedding_model),
            "has_chat_model": self._check_model(self.chat_model),
            "capabilities": {
                "embeddings": self.capabilities.embeddings,
                "batch_embeddings": self.capabilities.batch_embeddings,
            }
        }

    def get_embedding(self, text: str) -> List[float]:
        """Get embedding using Ollama."""
        if not self._check_model(self.embedding_model):
            raise ValueError(
                f"Model '{self.embedding_model}' not found. "
                f"Pull it with: ollama pull {self.embedding_model}"
            )

        try:
            response = requests.post(
                f"{self.base_url}/api/embed",
                json={
                    "model": self.embedding_model,
                    "input": text
                },
                timeout=self.timeout
            )
            response.raise_for_status()
            result = response.json()
            embeddings = result.get('embeddings', [[]])[0]

            if not embeddings:
                raise ValueError("No embedding returned from Ollama")
            return embeddings

        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"Ollama embedding request failed: {e}")

    def get_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """Get embeddings for multiple texts."""
        return [self.get_embedding(text) for text in texts]

    def _generate(self, prompt: str) -> str:
        """Generate text using chat model."""
        if not self._check_model(self.chat_model):
            raise ValueError(
                f"Model '{self.chat_model}' not found. "
                f"Pull it with: ollama pull {self.chat_model}"
            )

        try:
            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.chat_model,
                    "prompt": prompt,
                    "stream": False,
                    "format": "json"
                },
                timeout=self.timeout
            )
            response.raise_for_status()
            result = response.json()
            return result.get('response', '{}')

        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"Ollama generation failed: {e}")

    def analyze_note(self, content: str, title: str = "") -> AnalysisResult:
        """Analyze a note using Ollama."""
        prompt = f"""Analyze this Obsidian note and extract key information.

Title: {title or "Untitled"}
---
{self._truncate(content)}

Respond with ONLY valid JSON matching this schema:
{_ANALYSIS_SCHEMA}"""

        response = self._generate(prompt)
        json_str = self._extract_json(response)
        return AnalysisResult.from_json(json_str)

    def compare_notes(
        self,
        note1_content: str,
        note2_content: str,
        note1_title: str = "",
        note2_title: str = ""
    ) -> ComparisonResult:
        """Compare two notes using Ollama."""
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

        response = self._generate(prompt)
        json_str = self._extract_json(response)
        return ComparisonResult.from_json(json_str)

    def list_models(self) -> List[str]:
        """List available Ollama models."""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            response.raise_for_status()
            models = response.json().get('models', [])
            return [m['name'] for m in models]
        except Exception:
            return []
