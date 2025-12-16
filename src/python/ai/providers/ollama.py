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

from .base import (
    AIProvider, ProviderType, ProviderCapabilities,
    AnalysisResult, ComparisonResult
)


class OllamaProvider(AIProvider):
    """Ollama provider - free local AI."""

    name = "ollama"
    provider_type = ProviderType.LOCAL
    capabilities = ProviderCapabilities(
        embeddings=True,
        analysis=True,
        comparison=True,
        batch=True,  # Can do batch locally
        streaming=True
    )

    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        embedding_model: str = "nomic-embed-text",
        chat_model: str = "llama3.1",
        timeout: int = 60
    ):
        """Initialize Ollama provider.

        Args:
            base_url: Ollama server URL
            embedding_model: Model for embeddings (768 dims)
            chat_model: Model for text generation
            timeout: Request timeout in seconds
        """
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
                "batch": self.capabilities.batch,
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
        # Ollama handles batch internally
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

Extract and respond with ONLY valid JSON:
{{
    "topics": ["topic1", "topic2", "topic3"],
    "themes": ["theme1", "theme2"],
    "suggested_tags": ["tag1", "tag2"],
    "quality": {{"completeness": 7, "clarity": 8}},
    "suggestions": ["suggestion1", "suggestion2"]
}}"""

        response = self._generate(prompt)
        data = self._parse_json_response(
            response,
            {"topics": [], "themes": [], "suggested_tags": [], "quality": {}, "suggestions": []}
        )

        return AnalysisResult(
            topics=data.get("topics", []),
            themes=data.get("themes", []),
            suggested_tags=data.get("suggested_tags", []),
            quality=data.get("quality", {"completeness": 0, "clarity": 0}),
            suggestions=data.get("suggestions", []),
            raw_response=response
        )

    def compare_notes(
        self,
        note1_content: str,
        note2_content: str,
        note1_title: str = "",
        note2_title: str = "",
        use_embeddings: bool = True
    ) -> ComparisonResult:
        """Compare two notes using Ollama.

        Args:
            note1_content: First note content
            note2_content: Second note content
            note1_title: First note title
            note2_title: Second note title
            use_embeddings: Use fast embedding comparison (default True)
        """
        if use_embeddings:
            return self._compare_with_embeddings(note1_content, note2_content)
        return self._compare_with_reasoning(
            note1_content, note2_content,
            note1_title, note2_title
        )

    def _compare_with_embeddings(
        self,
        note1_content: str,
        note2_content: str
    ) -> ComparisonResult:
        """Fast comparison using embedding similarity."""
        import numpy as np

        emb1 = self.get_embedding(note1_content)
        emb2 = self.get_embedding(note2_content)

        emb1_arr = np.array(emb1)
        emb2_arr = np.array(emb2)

        similarity = float(
            np.dot(emb1_arr, emb2_arr) /
            (np.linalg.norm(emb1_arr) * np.linalg.norm(emb2_arr))
        )

        return ComparisonResult(
            similarity_score=similarity,
            reason=f"Embedding cosine similarity ({self.embedding_model})",
            should_merge=similarity > 0.85,
            merge_strategy="Review and combine" if similarity > 0.85 else None
        )

    def _compare_with_reasoning(
        self,
        note1_content: str,
        note2_content: str,
        note1_title: str,
        note2_title: str
    ) -> ComparisonResult:
        """Detailed comparison using chat model."""
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

        response = self._generate(prompt)
        data = self._parse_json_response(
            response,
            {"similarity_score": 0.0, "reason": "", "should_merge": False}
        )

        return ComparisonResult(
            similarity_score=max(0.0, min(1.0, float(data.get("similarity_score", 0.0)))),
            reason=data.get("reason", ""),
            should_merge=data.get("should_merge", False),
            merge_strategy=data.get("merge_strategy")
        )

    def list_models(self) -> List[str]:
        """List available Ollama models."""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            response.raise_for_status()
            models = response.json().get('models', [])
            return [m['name'] for m in models]
        except Exception:
            return []
