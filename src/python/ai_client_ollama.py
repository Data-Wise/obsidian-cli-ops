#!/usr/bin/env python3
"""
Ollama Client for Obsidian CLI Ops v2.0 - Phase 2

Free, local AI using Ollama for embeddings and note comparison.
No API costs, complete privacy, runs entirely on your machine.

Requirements:
- Ollama installed: brew install ollama
- Models pulled: ollama pull nomic-embed-text && ollama pull llama3.1

Documentation: https://ollama.com/blog/embedding-models
"""

import os
import requests
import json
from typing import List, Optional
import numpy as np

from ai_client import AIClient, SimilarityScore


class OllamaClient(AIClient):
    """Ollama AI client for free local embeddings and reasoning."""

    def __init__(self,
                 base_url: str = "http://localhost:11434",
                 embedding_model: str = "nomic-embed-text",
                 chat_model: str = "llama3.1"):
        """
        Initialize Ollama client.

        Args:
            base_url: Ollama server URL (default: http://localhost:11434)
            embedding_model: Model for embeddings (default: nomic-embed-text)
            chat_model: Model for text generation (default: llama3.1)
        """
        self.base_url = base_url.rstrip('/')
        self.embedding_model = embedding_model
        self.chat_model = chat_model

        # Don't call super().__init__() since we don't need API keys
        self.api_key = None

        # Test connection
        self._test_connection()

    def _get_api_key(self) -> str:
        """Ollama doesn't need API keys."""
        return ""

    def _test_connection(self):
        """Test connection to Ollama server."""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            raise ConnectionError(
                f"Cannot connect to Ollama at {self.base_url}. "
                f"Make sure Ollama is running: 'ollama serve'\n"
                f"Error: {e}"
            )

    def _check_model(self, model_name: str) -> bool:
        """
        Check if model is available.

        Args:
            model_name: Model to check

        Returns:
            True if model is available
        """
        try:
            response = requests.get(f"{self.base_url}/api/tags")
            response.raise_for_status()
            models = response.json().get('models', [])
            return any(m['name'].startswith(model_name) for m in models)
        except:
            return False

    def get_embedding(self, text: str) -> List[float]:
        """
        Get embedding vector using Ollama.

        Args:
            text: Text to embed

        Returns:
            Embedding vector (768 dimensions for nomic-embed-text)
        """
        # Check if embedding model is available
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
                timeout=30
            )
            response.raise_for_status()

            result = response.json()
            # Ollama returns embeddings as array under 'embeddings' key
            # For single input, it's a list with one element
            embeddings = result.get('embeddings', [[]])[0]

            if not embeddings:
                raise ValueError("No embedding returned from Ollama")

            return embeddings

        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"Ollama embedding request failed: {e}")

    def compare_notes(self, note1_content: str, note2_content: str,
                     note1_title: str = "", note2_title: str = "",
                     use_reasoning: bool = False) -> SimilarityScore:
        """
        Compare two notes using Ollama.

        Args:
            note1_content: First note content
            note2_content: Second note content
            note1_title: First note title (optional)
            note2_title: Second note title (optional)
            use_reasoning: Use chat model for reasoning (slower but better)

        Returns:
            Similarity score (0-1) with explanation
        """
        if use_reasoning:
            return self._compare_with_reasoning(
                note1_content, note2_content,
                note1_title, note2_title
            )
        else:
            return self._compare_with_embeddings(note1_content, note2_content)

    def _compare_with_embeddings(self, note1: str, note2: str) -> SimilarityScore:
        """
        Compare notes using cosine similarity of embeddings (fast).

        Args:
            note1: First note content
            note2: Second note content

        Returns:
            Similarity score based on embedding distance
        """
        # Get embeddings
        emb1 = self.get_embedding(note1)
        emb2 = self.get_embedding(note2)

        # Calculate cosine similarity
        emb1_array = np.array(emb1)
        emb2_array = np.array(emb2)

        similarity = np.dot(emb1_array, emb2_array) / (
            np.linalg.norm(emb1_array) * np.linalg.norm(emb2_array)
        )

        return SimilarityScore(
            note_id_1="",
            note_id_2="",
            score=float(similarity),
            reason=f"Embedding cosine similarity ({self.embedding_model})"
        )

    def _compare_with_reasoning(self, note1_content: str, note2_content: str,
                                note1_title: str = "", note2_title: str = "") -> SimilarityScore:
        """
        Compare notes using chat model for reasoning (slower, better quality).

        Args:
            note1_content: First note content
            note2_content: Second note content
            note1_title: First note title
            note2_title: Second note title

        Returns:
            Similarity score with reasoning
        """
        # Check if chat model is available
        if not self._check_model(self.chat_model):
            raise ValueError(
                f"Model '{self.chat_model}' not found. "
                f"Pull it with: ollama pull {self.chat_model}"
            )

        prompt = f"""Compare these two Obsidian notes and determine their similarity.

Note 1: {note1_title or "Untitled"}
---
{note1_content[:1000]}

Note 2: {note2_title or "Untitled"}
---
{note2_content[:1000]}

Analyze:
1. Topic overlap
2. Content similarity
3. Whether they might be duplicates or should be merged

Respond with ONLY valid JSON (no markdown, no extra text):
{{
    "similarity_score": 0.85,
    "reason": "brief explanation",
    "should_merge": false,
    "merge_strategy": "if applicable, how to merge"
}}"""

        try:
            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.chat_model,
                    "prompt": prompt,
                    "stream": False,
                    "format": "json"
                },
                timeout=60
            )
            response.raise_for_status()

            result = response.json()
            response_text = result.get('response', '{}')

            # Parse JSON response
            try:
                analysis = json.loads(response_text)
                score = float(analysis.get("similarity_score", 0.0))
                reason = analysis.get("reason", "")

                # Add merge info if applicable
                if analysis.get("should_merge"):
                    merge_strat = analysis.get("merge_strategy", "combine content")
                    reason += f" | Merge: {merge_strat}"

                return SimilarityScore(
                    note_id_1="",
                    note_id_2="",
                    score=max(0.0, min(1.0, score)),  # Clamp to 0-1
                    reason=reason
                )
            except (json.JSONDecodeError, ValueError, KeyError) as e:
                # Fallback: Use embeddings if JSON parsing fails
                print(f"⚠️  JSON parsing failed, falling back to embeddings: {e}")
                return self._compare_with_embeddings(note1_content, note2_content)

        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"Ollama generation request failed: {e}")

    def analyze_note(self, content: str, title: str = "") -> dict:
        """
        Analyze a note for topics, themes, and suggestions using chat model.

        Args:
            content: Note content
            title: Note title

        Returns:
            Analysis dict with topics, themes, tags, quality, suggestions
        """
        if not self._check_model(self.chat_model):
            raise ValueError(
                f"Model '{self.chat_model}' not found. "
                f"Pull it with: ollama pull {self.chat_model}"
            )

        prompt = f"""Analyze this Obsidian note and extract key information.

Title: {title or "Untitled"}
---
{content[:2000]}

Extract:
1. Main topics (3-5 keywords)
2. Themes/categories
3. Suggested tags (if missing)
4. Quality assessment (completeness 0-10, clarity 0-10)
5. Improvement suggestions

Respond with ONLY valid JSON (no markdown):
{{
    "topics": ["topic1", "topic2"],
    "themes": ["theme1", "theme2"],
    "suggested_tags": ["tag1", "tag2"],
    "quality": {{"completeness": 7, "clarity": 8}},
    "suggestions": ["suggestion1", "suggestion2"]
}}"""

        try:
            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.chat_model,
                    "prompt": prompt,
                    "stream": False,
                    "format": "json"
                },
                timeout=60
            )
            response.raise_for_status()

            result = response.json()
            response_text = result.get('response', '{}')

            return json.loads(response_text)

        except (json.JSONDecodeError, requests.exceptions.RequestException) as e:
            print(f"⚠️  Note analysis failed: {e}")
            return {
                "topics": [],
                "themes": [],
                "suggested_tags": [],
                "quality": {"completeness": 0, "clarity": 0},
                "suggestions": []
            }

    def list_models(self) -> List[str]:
        """
        List available Ollama models.

        Returns:
            List of model names
        """
        try:
            response = requests.get(f"{self.base_url}/api/tags")
            response.raise_for_status()
            models = response.json().get('models', [])
            return [m['name'] for m in models]
        except requests.exceptions.RequestException as e:
            print(f"⚠️  Failed to list models: {e}")
            return []


def main():
    """Test Ollama client."""
    import sys

    print("🔍 Testing Ollama Client\n")

    # Initialize client
    try:
        client = OllamaClient()
        print(f"✓ Connected to Ollama at {client.base_url}")
    except ConnectionError as e:
        print(f"❌ {e}")
        print("\nSetup instructions:")
        print("  1. Install: brew install ollama")
        print("  2. Start: ollama serve")
        print("  3. Pull models:")
        print("     ollama pull nomic-embed-text")
        print("     ollama pull llama3.1")
        sys.exit(1)

    # List models
    print(f"\n📦 Available models:")
    models = client.list_models()
    for model in models:
        print(f"  - {model}")

    # Test embeddings
    if client._check_model(client.embedding_model):
        print(f"\n🧮 Testing embeddings ({client.embedding_model})...")
        try:
            emb = client.get_embedding("Statistical mediation analysis")
            print(f"  ✓ Embedding dimension: {len(emb)}")
            print(f"  ✓ Sample values: [{emb[0]:.4f}, {emb[1]:.4f}, {emb[2]:.4f}, ...]")
        except Exception as e:
            print(f"  ❌ Error: {e}")
    else:
        print(f"\n⚠️  Model '{client.embedding_model}' not found")
        print(f"  Pull it with: ollama pull {client.embedding_model}")

    # Test comparison
    if len(sys.argv) > 2:
        note1 = sys.argv[1]
        note2 = sys.argv[2]
        use_reasoning = len(sys.argv) > 3 and sys.argv[3] == "--reasoning"

        print(f"\n🔬 Comparing notes...")
        print(f"  Note 1: {note1[:50]}...")
        print(f"  Note 2: {note2[:50]}...")
        print(f"  Method: {'Reasoning' if use_reasoning else 'Embeddings'}")

        try:
            score = client.compare_notes(note1, note2, use_reasoning=use_reasoning)
            print(f"\n  Similarity: {score.score:.2f}")
            print(f"  Reason: {score.reason}")
        except Exception as e:
            print(f"  ❌ Error: {e}")

    print("\n✓ Ollama client test complete!")


if __name__ == '__main__':
    main()
