#!/usr/bin/env python3
"""
HuggingFace Client for Obsidian CLI Ops v2.0 - Phase 2

Free, local AI using HuggingFace sentence-transformers for embeddings.
Pure Python, no external services, works everywhere.

Requirements:
- pip install sentence-transformers

Documentation: https://www.sbert.net/
"""

from typing import List, Optional
import numpy as np

from ai_client import AIClient, SimilarityScore


class HuggingFaceClient(AIClient):
    """HuggingFace AI client for free local embeddings."""

    # Available models and their characteristics
    MODELS = {
        "all-MiniLM-L6-v2": {
            "dim": 384,
            "speed": "fast",
            "size": "~80MB",
            "desc": "Fast and small, good for testing"
        },
        "all-mpnet-base-v2": {
            "dim": 768,
            "speed": "medium",
            "size": "~420MB",
            "desc": "Balanced speed and quality (recommended)"
        },
        "bge-large-en-v1.5": {
            "dim": 1024,
            "speed": "slow",
            "size": "~1.3GB",
            "desc": "Best quality, slower, larger"
        }
    }

    def __init__(self, model_name: str = "all-mpnet-base-v2"):
        """
        Initialize HuggingFace client.

        Args:
            model_name: Model to use (default: all-mpnet-base-v2)
                       Options: all-MiniLM-L6-v2, all-mpnet-base-v2, bge-large-en-v1.5
        """
        self.model_name = model_name

        # Don't call super().__init__() since we don't need API keys
        self.api_key = None

        # Load model
        try:
            from sentence_transformers import SentenceTransformer
            self.SentenceTransformer = SentenceTransformer
        except ImportError:
            raise ImportError(
                "sentence-transformers not installed. "
                "Install with: pip install sentence-transformers"
            )

        print(f"📥 Loading HuggingFace model '{model_name}'...")
        if model_name in self.MODELS:
            print(f"   {self.MODELS[model_name]['desc']}")
            print(f"   Size: {self.MODELS[model_name]['size']}, "
                  f"Dimension: {self.MODELS[model_name]['dim']}")
        print(f"   This may take a moment on first run...")

        try:
            self.model = self.SentenceTransformer(model_name)
            print(f"✓ Model loaded successfully!")
        except Exception as e:
            raise RuntimeError(
                f"Failed to load model '{model_name}': {e}\n"
                f"Available models: {', '.join(self.MODELS.keys())}"
            )

    def _get_api_key(self) -> str:
        """HuggingFace doesn't need API keys for local models."""
        return ""

    def get_embedding(self, text: str) -> List[float]:
        """
        Get embedding vector using sentence-transformers.

        Args:
            text: Text to embed

        Returns:
            Embedding vector (dimension depends on model)
        """
        try:
            # sentence-transformers returns numpy array
            embedding = self.model.encode(text)
            return embedding.tolist()
        except Exception as e:
            raise RuntimeError(f"Embedding generation failed: {e}")

    def compare_notes(self, note1: str, note2: str) -> SimilarityScore:
        """
        Compare notes using cosine similarity of embeddings.

        Args:
            note1: First note content
            note2: Second note content

        Returns:
            Similarity score (0-1) based on embedding distance
        """
        # Get embeddings
        emb1 = np.array(self.get_embedding(note1))
        emb2 = np.array(self.get_embedding(note2))

        # Calculate cosine similarity
        similarity = np.dot(emb1, emb2) / (
            np.linalg.norm(emb1) * np.linalg.norm(emb2)
        )

        return SimilarityScore(
            note_id_1="",
            note_id_2="",
            score=float(similarity),
            reason=f"Embedding cosine similarity ({self.model_name})"
        )

    def get_embeddings_batch(self, texts: List[str],
                            batch_size: int = 32) -> List[List[float]]:
        """
        Get embeddings for multiple texts efficiently.

        Args:
            texts: List of texts to embed
            batch_size: Batch size for processing

        Returns:
            List of embedding vectors
        """
        try:
            # sentence-transformers handles batching efficiently
            embeddings = self.model.encode(
                texts,
                batch_size=batch_size,
                show_progress_bar=len(texts) > 100
            )
            return [emb.tolist() for emb in embeddings]
        except Exception as e:
            raise RuntimeError(f"Batch embedding generation failed: {e}")

    def find_most_similar(self, query: str, candidates: List[str],
                         top_k: int = 5) -> List[tuple]:
        """
        Find most similar texts to query using embeddings.

        Args:
            query: Query text
            candidates: List of candidate texts
            top_k: Number of top results to return

        Returns:
            List of (index, similarity_score) tuples
        """
        # Get embeddings
        query_emb = np.array(self.get_embedding(query))
        candidate_embs = np.array(self.get_embeddings_batch(candidates))

        # Calculate cosine similarities
        similarities = np.dot(candidate_embs, query_emb) / (
            np.linalg.norm(candidate_embs, axis=1) * np.linalg.norm(query_emb)
        )

        # Get top-k indices
        top_indices = np.argsort(similarities)[::-1][:top_k]

        return [(int(idx), float(similarities[idx])) for idx in top_indices]

    @classmethod
    def list_models(cls) -> dict:
        """
        List available models with descriptions.

        Returns:
            Dict of model names to their characteristics
        """
        return cls.MODELS


def main():
    """Test HuggingFace client."""
    import sys

    print("🔍 Testing HuggingFace Client\n")

    # Choose model
    model_name = sys.argv[1] if len(sys.argv) > 1 else "all-MiniLM-L6-v2"

    print(f"📦 Available models:")
    for name, info in HuggingFaceClient.MODELS.items():
        marker = "→" if name == model_name else " "
        print(f"  {marker} {name}")
        print(f"    {info['desc']}")
        print(f"    Size: {info['size']}, Dimension: {info['dim']}, Speed: {info['speed']}\n")

    # Initialize client
    try:
        client = HuggingFaceClient(model_name)
    except Exception as e:
        print(f"❌ {e}")
        print("\nSetup instructions:")
        print("  pip install sentence-transformers")
        sys.exit(1)

    # Test embeddings
    print(f"\n🧮 Testing embeddings...")
    try:
        emb = client.get_embedding("Statistical mediation analysis")
        print(f"  ✓ Embedding dimension: {len(emb)}")
        print(f"  ✓ Sample values: [{emb[0]:.4f}, {emb[1]:.4f}, {emb[2]:.4f}, ...]")
    except Exception as e:
        print(f"  ❌ Error: {e}")
        sys.exit(1)

    # Test comparison
    print(f"\n🔬 Comparing notes...")
    note1 = "Statistical mediation analysis methods"
    note2 = "Causal mediation with confounding"
    note3 = "Machine learning for image classification"

    print(f"  Note 1: {note1}")
    print(f"  Note 2: {note2}")
    print(f"  Note 3: {note3}")

    try:
        score12 = client.compare_notes(note1, note2)
        score13 = client.compare_notes(note1, note3)

        print(f"\n  Note 1 vs Note 2: {score12.score:.2f} (similar topics)")
        print(f"  Note 1 vs Note 3: {score13.score:.2f} (different topics)")
    except Exception as e:
        print(f"  ❌ Error: {e}")
        sys.exit(1)

    # Test batch processing
    print(f"\n📦 Testing batch processing...")
    texts = [note1, note2, note3]
    try:
        embeddings = client.get_embeddings_batch(texts)
        print(f"  ✓ Generated {len(embeddings)} embeddings")
    except Exception as e:
        print(f"  ❌ Error: {e}")

    # Test similarity search
    print(f"\n🔍 Testing similarity search...")
    candidates = [
        "Causal inference methods",
        "Deep neural networks",
        "Mediation analysis tutorial",
        "Computer vision algorithms",
        "Statistical confounding adjustment"
    ]
    try:
        results = client.find_most_similar(note1, candidates, top_k=3)
        print(f"  Query: {note1}")
        print(f"  Top 3 similar:")
        for idx, score in results:
            print(f"    {score:.2f} - {candidates[idx]}")
    except Exception as e:
        print(f"  ❌ Error: {e}")

    print("\n✓ HuggingFace client test complete!")


if __name__ == '__main__':
    main()
