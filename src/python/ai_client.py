#!/usr/bin/env python3
"""
AI Client for Obsidian CLI Ops v2.0 - Phase 2

Provides AI-powered analysis using Claude and Gemini APIs:
- Note similarity detection
- Semantic embeddings
- Topic modeling
- Duplicate detection
"""

import os
from typing import List, Dict, Optional, Tuple
from abc import ABC, abstractmethod
from dataclasses import dataclass
import json


@dataclass
class NoteEmbedding:
    """Embedding for a note."""
    note_id: str
    embedding: List[float]
    model: str
    created_at: str


@dataclass
class SimilarityScore:
    """Similarity between two notes."""
    note_id_1: str
    note_id_2: str
    score: float
    reason: Optional[str] = None


class AIClient(ABC):
    """Base class for AI API clients."""

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize AI client.

        Args:
            api_key: API key (if None, reads from environment)
        """
        self.api_key = api_key or self._get_api_key()

    @abstractmethod
    def _get_api_key(self) -> str:
        """Get API key from environment."""
        pass

    @abstractmethod
    def get_embedding(self, text: str) -> List[float]:
        """
        Get embedding vector for text.

        Args:
            text: Text to embed

        Returns:
            Embedding vector
        """
        pass

    @abstractmethod
    def compare_notes(self, note1: str, note2: str) -> SimilarityScore:
        """
        Compare two notes for similarity.

        Args:
            note1: First note content
            note2: Second note content

        Returns:
            Similarity score with reasoning
        """
        pass


class ClaudeClient(AIClient):
    """Claude API client for note analysis."""

    def __init__(self, api_key: Optional[str] = None, model: str = "claude-3-5-sonnet-20241022"):
        """
        Initialize Claude client.

        Args:
            api_key: Anthropic API key
            model: Claude model to use
        """
        self.model = model
        super().__init__(api_key)

        # Import anthropic only when needed
        try:
            from anthropic import Anthropic
            self.client = Anthropic(api_key=self.api_key)
        except ImportError:
            raise ImportError(
                "anthropic package not installed. "
                "Install with: pip install anthropic"
            )

    def _get_api_key(self) -> str:
        """Get Anthropic API key from environment."""
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError(
                "ANTHROPIC_API_KEY not found in environment. "
                "Set it with: export ANTHROPIC_API_KEY='your-key'"
            )
        return api_key

    def get_embedding(self, text: str) -> List[float]:
        """
        Claude doesn't provide embeddings directly.
        Use Gemini or a separate embedding model.
        """
        raise NotImplementedError(
            "Claude doesn't provide embeddings. Use GeminiClient instead."
        )

    def compare_notes(self, note1_content: str, note2_content: str,
                     note1_title: str = "", note2_title: str = "") -> SimilarityScore:
        """
        Compare two notes using Claude's reasoning.

        Args:
            note1_content: First note content
            note2_content: Second note content
            note1_title: First note title (optional)
            note2_title: Second note title (optional)

        Returns:
            Similarity score (0-1) with reasoning
        """
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

Respond with JSON:
{{
    "similarity_score": 0.0-1.0,
    "reason": "brief explanation",
    "should_merge": true/false,
    "merge_strategy": "if should_merge, how to merge them"
}}"""

        response = self.client.messages.create(
            model=self.model,
            max_tokens=1024,
            messages=[{
                "role": "user",
                "content": prompt
            }]
        )

        # Parse JSON response
        try:
            result = json.loads(response.content[0].text)
            score = result.get("similarity_score", 0.0)
            reason = result.get("reason", "")

            # Store merge info in reason if applicable
            if result.get("should_merge"):
                reason += f" | Merge: {result.get('merge_strategy', 'combine content')}"

            return SimilarityScore(
                note_id_1="",  # Will be filled by caller
                note_id_2="",
                score=score,
                reason=reason
            )
        except (json.JSONDecodeError, KeyError) as e:
            # Fallback if JSON parsing fails
            return SimilarityScore(
                note_id_1="",
                note_id_2="",
                score=0.0,
                reason=f"Error parsing response: {e}"
            )

    def analyze_note(self, content: str, title: str = "") -> Dict:
        """
        Analyze a single note for topics and themes.

        Args:
            content: Note content
            title: Note title (optional)

        Returns:
            Analysis with topics, themes, and suggestions
        """
        prompt = f"""Analyze this Obsidian note and extract key information.

Title: {title or "Untitled"}
---
{content[:2000]}

Extract:
1. Main topics (3-5 keywords)
2. Themes/categories
3. Suggested tags (if current tags are missing)
4. Quality assessment (completeness, clarity)

Respond with JSON:
{{
    "topics": ["topic1", "topic2", ...],
    "themes": ["theme1", "theme2", ...],
    "suggested_tags": ["tag1", "tag2", ...],
    "quality": {{"completeness": 0-10, "clarity": 0-10}},
    "suggestions": ["improvement1", "improvement2", ...]
}}"""

        response = self.client.messages.create(
            model=self.model,
            max_tokens=1024,
            messages=[{
                "role": "user",
                "content": prompt
            }]
        )

        try:
            return json.loads(response.content[0].text)
        except json.JSONDecodeError:
            return {
                "topics": [],
                "themes": [],
                "suggested_tags": [],
                "quality": {"completeness": 0, "clarity": 0},
                "suggestions": []
            }


class GeminiClient(AIClient):
    """Gemini API client for embeddings and topic modeling."""

    def __init__(self, api_key: Optional[str] = None, model: str = "gemini-2.0-flash-exp"):
        """
        Initialize Gemini client.

        Args:
            api_key: Google API key
            model: Gemini model to use
        """
        self.model = model
        super().__init__(api_key)

        # Import google.generativeai only when needed
        try:
            import google.generativeai as genai
            genai.configure(api_key=self.api_key)
            self.client = genai
        except ImportError:
            raise ImportError(
                "google-generativeai package not installed. "
                "Install with: pip install google-generativeai"
            )

    def _get_api_key(self) -> str:
        """Get Google API key from environment."""
        api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError(
                "GOOGLE_API_KEY or GEMINI_API_KEY not found in environment. "
                "Set it with: export GOOGLE_API_KEY='your-key'"
            )
        return api_key

    def get_embedding(self, text: str, task_type: str = "SEMANTIC_SIMILARITY") -> List[float]:
        """
        Get embedding vector using Gemini.

        Args:
            text: Text to embed
            task_type: Embedding task type
                      (SEMANTIC_SIMILARITY, RETRIEVAL_QUERY, RETRIEVAL_DOCUMENT)

        Returns:
            Embedding vector (768 dimensions)
        """
        result = self.client.embed_content(
            model="models/text-embedding-004",
            content=text,
            task_type=task_type
        )
        return result['embedding']

    def compare_notes(self, note1: str, note2: str) -> SimilarityScore:
        """
        Compare notes using cosine similarity of embeddings.

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
        import numpy as np
        similarity = np.dot(emb1, emb2) / (np.linalg.norm(emb1) * np.linalg.norm(emb2))

        return SimilarityScore(
            note_id_1="",
            note_id_2="",
            score=float(similarity),
            reason="Cosine similarity of embeddings"
        )

    def generate_topics(self, notes: List[str], num_topics: int = 5) -> List[Dict]:
        """
        Generate topic clusters from notes.

        Args:
            notes: List of note contents
            num_topics: Number of topics to extract

        Returns:
            List of topics with representative notes
        """
        # Get embeddings for all notes
        embeddings = [self.get_embedding(note) for note in notes]

        # Use clustering to find topics (simplified)
        import numpy as np
        from sklearn.cluster import KMeans

        # Convert to numpy array
        X = np.array(embeddings)

        # Cluster
        kmeans = KMeans(n_clusters=min(num_topics, len(notes)), random_state=42)
        labels = kmeans.fit_predict(X)

        # Group notes by topic
        topics = []
        for i in range(num_topics):
            topic_notes = [notes[j] for j in range(len(notes)) if labels[j] == i]
            if topic_notes:
                topics.append({
                    "topic_id": i,
                    "note_count": len(topic_notes),
                    "sample_content": topic_notes[0][:200]
                })

        return topics


def get_ai_client(provider: str = "claude", **kwargs) -> AIClient:
    """
    Factory function to get AI client.

    Args:
        provider: 'claude' or 'gemini'
        **kwargs: Additional arguments for client

    Returns:
        AI client instance
    """
    if provider.lower() == "claude":
        return ClaudeClient(**kwargs)
    elif provider.lower() == "gemini":
        return GeminiClient(**kwargs)
    else:
        raise ValueError(f"Unknown provider: {provider}. Use 'claude' or 'gemini'.")


def main():
    """Test AI clients."""
    import sys

    if len(sys.argv) < 2:
        print("Usage: python ai_client.py <provider> [note1] [note2]")
        print("  provider: 'claude' or 'gemini'")
        sys.exit(1)

    provider = sys.argv[1]
    note1 = sys.argv[2] if len(sys.argv) > 2 else "Statistical mediation analysis"
    note2 = sys.argv[3] if len(sys.argv) > 3 else "Causal mediation methods"

    try:
        client = get_ai_client(provider)
        print(f"✓ {provider.title()} client initialized")

        if provider.lower() == "gemini":
            print(f"\nGetting embeddings...")
            emb1 = client.get_embedding(note1)
            print(f"  Embedding dimension: {len(emb1)}")

        print(f"\nComparing notes...")
        score = client.compare_notes(note1, note2)
        print(f"  Similarity: {score.score:.2f}")
        print(f"  Reason: {score.reason}")

    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
