"""Tests for AI providers (Gemini SDK, Anthropic API, base utilities)."""

import json
import pytest
from unittest.mock import patch, MagicMock

from ai.models import AnalysisResult, ComparisonResult
from ai.providers.base import AIProvider, ProviderCapabilities


# --- Base provider utility tests ---

class TestExtractJson:
    """Tests for _extract_json on base AIProvider."""

    def setup_method(self):
        """Create a concrete provider for testing."""
        # Use Ollama since it's simplest to instantiate without deps
        from ai.providers.ollama import OllamaProvider
        self.provider = OllamaProvider()

    def test_extract_json_clean(self):
        raw = '{"key": "value"}'
        assert self.provider._extract_json(raw) == '{"key": "value"}'

    def test_extract_json_with_surrounding_text(self):
        raw = 'Here is the JSON:\n{"key": "value"}\nDone!'
        assert self.provider._extract_json(raw) == '{"key": "value"}'

    def test_extract_json_no_json_raises(self):
        with pytest.raises(ValueError, match="No JSON object found"):
            self.provider._extract_json("no json here")

    def test_truncate_short_text(self):
        assert self.provider._truncate("hello", 10) == "hello"

    def test_truncate_long_text(self):
        result = self.provider._truncate("hello world", 5)
        assert result == "hello..."


# --- Gemini API provider tests ---

class TestGeminiAPIProvider:
    """Tests for Gemini API provider with new google-genai SDK."""

    def test_capabilities(self):
        from ai.providers.gemini_api import GeminiAPIProvider
        p = GeminiAPIProvider(api_key="test-key")
        assert p.capabilities.embeddings is True
        assert p.capabilities.batch_embeddings is True
        assert p.capabilities.analysis is True
        assert p.capabilities.comparison is True

    def test_not_available_without_key(self):
        from ai.providers.gemini_api import GeminiAPIProvider
        p = GeminiAPIProvider(api_key=None)
        with patch.dict('os.environ', {}, clear=True):
            # Force no env vars
            p.api_key = None
            assert p.is_available() is False

    def test_status_reports_key(self):
        from ai.providers.gemini_api import GeminiAPIProvider
        p = GeminiAPIProvider(api_key="test-key")
        status = p.get_status()
        assert status["name"] == "gemini-api"
        assert status["api_key_set"] is True
        assert status["model"] == "gemini-2.5-flash"

    @patch("ai.providers.gemini_api.GeminiAPIProvider._get_client")
    def test_analyze_note_returns_analysis_result(self, mock_client):
        from ai.providers.gemini_api import GeminiAPIProvider
        mock_response = MagicMock()
        mock_response.text = json.dumps({
            "summary": "A note about Python testing",
            "themes": ["testing", "python"],
            "quality_score": 0.85,
            "suggestions": ["Add examples"],
            "connections": ["pytest", "unittest"],
        })
        mock_client.return_value.models.generate_content.return_value = mock_response

        p = GeminiAPIProvider(api_key="test-key")
        # Mock the _genai module so genai.types.GenerateContentConfig works
        p._genai = MagicMock()
        result = p.analyze_note("Content about testing", "Testing Guide")
        assert isinstance(result, AnalysisResult)
        assert result.summary == "A note about Python testing"
        assert result.quality_score == 0.85

    @patch("ai.providers.gemini_api.GeminiAPIProvider._get_client")
    def test_compare_notes_returns_comparison_result(self, mock_client):
        from ai.providers.gemini_api import GeminiAPIProvider
        mock_response = MagicMock()
        mock_response.text = json.dumps({
            "similarity_score": 0.72,
            "common_themes": ["python"],
            "differences": ["scope"],
            "relationship": "complementary",
        })
        mock_client.return_value.models.generate_content.return_value = mock_response

        p = GeminiAPIProvider(api_key="test-key")
        p._genai = MagicMock()
        result = p.compare_notes("Content 1", "Content 2", "Note 1", "Note 2")
        assert isinstance(result, ComparisonResult)
        assert result.similarity_score == 0.72
        assert result.relationship == "complementary"

    @patch("ai.providers.gemini_api.GeminiAPIProvider._get_client")
    def test_get_embedding(self, mock_client):
        from ai.providers.gemini_api import GeminiAPIProvider
        mock_embedding = MagicMock()
        mock_embedding.values = [0.1, 0.2, 0.3]
        mock_result = MagicMock()
        mock_result.embeddings = [mock_embedding]
        mock_client.return_value.models.embed_content.return_value = mock_result

        p = GeminiAPIProvider(api_key="test-key")
        embedding = p.get_embedding("test text")
        assert embedding == [0.1, 0.2, 0.3]

    @patch("ai.providers.gemini_api.GeminiAPIProvider._get_client")
    def test_get_embeddings_batch(self, mock_client):
        from ai.providers.gemini_api import GeminiAPIProvider
        emb1 = MagicMock()
        emb1.values = [0.1, 0.2]
        emb2 = MagicMock()
        emb2.values = [0.3, 0.4]
        mock_result = MagicMock()
        mock_result.embeddings = [emb1, emb2]
        mock_client.return_value.models.embed_content.return_value = mock_result

        p = GeminiAPIProvider(api_key="test-key")
        embeddings = p.get_embeddings_batch(["text1", "text2"])
        assert len(embeddings) == 2
        assert embeddings[0] == [0.1, 0.2]


# --- Anthropic API provider tests ---

class TestAnthropicAPIProvider:
    """Tests for Anthropic API provider."""

    def test_capabilities(self):
        from ai.providers.anthropic_api import AnthropicAPIProvider
        p = AnthropicAPIProvider(api_key="test-key")
        assert p.capabilities.embeddings is False
        assert p.capabilities.batch_embeddings is False
        assert p.capabilities.analysis is True
        assert p.capabilities.comparison is True

    def test_not_available_without_key(self):
        from ai.providers.anthropic_api import AnthropicAPIProvider
        p = AnthropicAPIProvider(api_key=None)
        with patch.dict('os.environ', {}, clear=True):
            p.api_key = None
            assert p.is_available() is False

    def test_status_reports_model(self):
        from ai.providers.anthropic_api import AnthropicAPIProvider
        p = AnthropicAPIProvider(api_key="test-key")
        status = p.get_status()
        assert status["name"] == "anthropic-api"
        assert status["api_key_set"] is True
        assert status["model"] == "claude-sonnet-4-6"

    @patch("ai.providers.anthropic_api.AnthropicAPIProvider._get_client")
    def test_analyze_note_returns_analysis_result(self, mock_client):
        from ai.providers.anthropic_api import AnthropicAPIProvider
        mock_content = MagicMock()
        mock_content.text = json.dumps({
            "summary": "Deep analysis of note",
            "themes": ["AI", "research"],
            "quality_score": 0.9,
            "suggestions": ["Add citations"],
            "connections": ["machine learning"],
        })
        mock_response = MagicMock()
        mock_response.content = [mock_content]
        mock_client.return_value.messages.create.return_value = mock_response

        p = AnthropicAPIProvider(api_key="test-key")
        result = p.analyze_note("AI research content", "AI Research")
        assert isinstance(result, AnalysisResult)
        assert result.summary == "Deep analysis of note"
        assert result.quality_score == 0.9

    @patch("ai.providers.anthropic_api.AnthropicAPIProvider._get_client")
    def test_compare_notes_returns_comparison_result(self, mock_client):
        from ai.providers.anthropic_api import AnthropicAPIProvider
        mock_content = MagicMock()
        mock_content.text = json.dumps({
            "similarity_score": 0.65,
            "common_themes": ["AI"],
            "differences": ["depth of coverage"],
            "relationship": "one expands on the other",
        })
        mock_response = MagicMock()
        mock_response.content = [mock_content]
        mock_client.return_value.messages.create.return_value = mock_response

        p = AnthropicAPIProvider(api_key="test-key")
        result = p.compare_notes("Content A", "Content B")
        assert isinstance(result, ComparisonResult)
        assert result.similarity_score == 0.65
        assert "expands" in result.relationship


# --- Router integration tests ---

class TestRouterWithNewProviders:
    """Tests for router with updated provider set."""

    def test_default_priority_includes_anthropic(self):
        from ai.router import DEFAULT_PRIORITY
        assert "anthropic-api" in DEFAULT_PRIORITY
        # Verify order: gemini-api > anthropic-api > ollama
        gemini_idx = DEFAULT_PRIORITY.index("gemini-api")
        anthropic_idx = DEFAULT_PRIORITY.index("anthropic-api")
        ollama_idx = DEFAULT_PRIORITY.index("ollama")
        assert gemini_idx < anthropic_idx < ollama_idx

    def test_provider_classes_has_all(self):
        from ai.router import PROVIDER_CLASSES
        assert "gemini-api" in PROVIDER_CLASSES
        assert "anthropic-api" in PROVIDER_CLASSES
        assert "ollama" in PROVIDER_CLASSES
        assert "gemini-cli" in PROVIDER_CLASSES
        assert "claude-cli" in PROVIDER_CLASSES

    def test_router_creates_anthropic_provider(self):
        from ai.router import AIRouter
        router = AIRouter()
        provider = router._get_provider("anthropic-api")
        assert provider.name == "anthropic-api"
