"""
Unit tests for AI client classes.

Tests AI client factory, HuggingFace client, and Ollama client (mocked).
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

sys.path.insert(0, str(Path(__file__).parent.parent))

from ai_client import get_ai_client, AIClient


class TestAIClientFactory:
    """Test AI client factory pattern."""

    def test_get_huggingface_client(self):
        """Test getting HuggingFace client."""
        try:
            client = get_ai_client("huggingface", model_name="all-MiniLM-L6-v2")
            assert client is not None
            assert hasattr(client, 'get_embedding')
            assert hasattr(client, 'compare_notes')
        except ImportError:
            pytest.skip("sentence-transformers not installed")

    @patch('ai_client.requests')
    def test_get_ollama_client(self, mock_requests):
        """Test getting Ollama client."""
        # Mock Ollama connection test
        mock_response = Mock()
        mock_response.status_code = 200
        mock_requests.get.return_value = mock_response

        try:
            client = get_ai_client("ollama")
            assert client is not None
            assert hasattr(client, 'get_embedding')
        except ImportError:
            pytest.skip("requests not installed")

    def test_unsupported_provider(self):
        """Test requesting unsupported provider."""
        with pytest.raises((ValueError, ImportError)):
            get_ai_client("unsupported_provider")

    def test_default_provider(self):
        """Test default provider selection."""
        # Default should be ollama or huggingface
        try:
            client = get_ai_client()
            assert client is not None
        except ImportError:
            pytest.skip("No AI providers installed")


class TestHuggingFaceClient:
    """Test HuggingFace client functionality."""

    @pytest.mark.ai
    def test_get_embedding(self):
        """Test getting embedding vector."""
        try:
            from ai_client_hf import HuggingFaceClient

            client = HuggingFaceClient(model_name="all-MiniLM-L6-v2")
            embedding = client.get_embedding("Test note content")

            assert embedding is not None
            assert isinstance(embedding, list)
            assert len(embedding) == 384  # MiniLM dimension
        except ImportError:
            pytest.skip("sentence-transformers not installed")

    @pytest.mark.ai
    def test_compare_notes(self):
        """Test comparing two notes."""
        try:
            from ai_client_hf import HuggingFaceClient

            client = HuggingFaceClient(model_name="all-MiniLM-L6-v2")

            note1 = "This is about machine learning and AI."
            note2 = "This discusses artificial intelligence and ML."
            note3 = "This is about cooking recipes."

            score12 = client.compare_notes(note1, note2)
            score13 = client.compare_notes(note1, note3)

            # Similar notes should have higher score
            assert score12.score > score13.score
            assert 0 <= score12.score <= 1
            assert 0 <= score13.score <= 1
        except ImportError:
            pytest.skip("sentence-transformers not installed")

    @pytest.mark.ai
    def test_batch_embeddings(self):
        """Test batch embedding generation."""
        try:
            from ai_client_hf import HuggingFaceClient

            client = HuggingFaceClient(model_name="all-MiniLM-L6-v2")

            texts = ["Note 1", "Note 2", "Note 3"]
            embeddings = client.get_embeddings_batch(texts)

            assert len(embeddings) == 3
            assert all(len(e) == 384 for e in embeddings)
        except (ImportError, AttributeError):
            pytest.skip("batch method not available")


class TestOllamaClient:
    """Test Ollama client functionality (mocked)."""

    @patch('ai_client_ollama.requests.post')
    def test_get_embedding_mocked(self, mock_post):
        """Test getting embedding from Ollama (mocked)."""
        try:
            from ai_client_ollama import OllamaClient

            # Mock response
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                'embeddings': [[0.1] * 768]
            }
            mock_post.return_value = mock_response

            client = OllamaClient()
            embedding = client.get_embedding("Test content")

            assert embedding is not None
            assert len(embedding) == 768
        except ImportError:
            pytest.skip("Ollama client not available")

    @patch('ai_client_ollama.requests.post')
    def test_compare_notes_mocked(self, mock_post):
        """Test comparing notes with Ollama (mocked)."""
        try:
            from ai_client_ollama import OllamaClient

            # Mock embedding responses
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                'embeddings': [[0.5] * 768]
            }
            mock_post.return_value = mock_response

            client = OllamaClient()
            score = client.compare_notes("Note 1", "Note 2")

            assert score is not None
            assert hasattr(score, 'score')
        except ImportError:
            pytest.skip("Ollama client not available")


class TestAIClientInterface:
    """Test that all clients implement required interface."""

    def test_huggingface_implements_interface(self):
        """Test HuggingFace client implements AIClient interface."""
        try:
            from ai_client_hf import HuggingFaceClient

            client = HuggingFaceClient(model_name="all-MiniLM-L6-v2")

            # Check methods exist
            assert hasattr(client, 'get_embedding')
            assert hasattr(client, 'compare_notes')
            assert callable(client.get_embedding)
            assert callable(client.compare_notes)
        except ImportError:
            pytest.skip("HuggingFace client not available")

    @patch('ai_client_ollama.requests')
    def test_ollama_implements_interface(self, mock_requests):
        """Test Ollama client implements AIClient interface."""
        try:
            from ai_client_ollama import OllamaClient

            # Mock connection
            mock_response = Mock()
            mock_response.status_code = 200
            mock_requests.get.return_value = mock_response

            client = OllamaClient()

            # Check methods exist
            assert hasattr(client, 'get_embedding')
            assert hasattr(client, 'compare_notes')
            assert callable(client.get_embedding)
            assert callable(client.compare_notes)
        except ImportError:
            pytest.skip("Ollama client not available")


@pytest.mark.unit
class TestSimilarityScoring:
    """Test similarity scoring functionality."""

    @pytest.mark.ai
    def test_similarity_score_range(self):
        """Test that similarity scores are in valid range."""
        try:
            from ai_client_hf import HuggingFaceClient

            client = HuggingFaceClient(model_name="all-MiniLM-L6-v2")

            score = client.compare_notes("Test 1", "Test 2")

            # Score should be between 0 and 1
            assert 0 <= score.score <= 1
        except ImportError:
            pytest.skip("HuggingFace client not available")

    @pytest.mark.ai
    def test_identical_notes_high_score(self):
        """Test that identical notes have high similarity."""
        try:
            from ai_client_hf import HuggingFaceClient

            client = HuggingFaceClient(model_name="all-MiniLM-L6-v2")

            note = "This is a test note with specific content."
            score = client.compare_notes(note, note)

            # Identical notes should have very high similarity
            assert score.score > 0.99
        except ImportError:
            pytest.skip("HuggingFace client not available")


@pytest.mark.slow
@pytest.mark.integration
class TestRealAIProviders:
    """Integration tests with real AI providers (skipped by default)."""

    def test_huggingface_real_embedding(self):
        """Test real HuggingFace embedding generation."""
        pytest.skip("Requires HuggingFace installation and time")

    def test_ollama_real_connection(self):
        """Test real Ollama connection."""
        pytest.skip("Requires Ollama service running")
