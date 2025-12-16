"""Tests for AI provider implementations."""

import pytest
from unittest.mock import patch, MagicMock
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(__file__).rsplit('/', 2)[0])

from ai.providers.base import (
    AIProvider,
    ProviderType,
    ProviderCapabilities,
    AnalysisResult,
    ComparisonResult,
    SimilarNote,
)
from ai.providers.gemini_api import GeminiAPIProvider
from ai.providers.gemini_cli import GeminiCLIProvider
from ai.providers.claude_cli import ClaudeCLIProvider
from ai.providers.ollama import OllamaProvider


class TestProviderType:
    """Tests for ProviderType enum."""

    def test_provider_types(self):
        """Test all provider types exist."""
        assert ProviderType.API.value == "api"
        assert ProviderType.CLI.value == "cli"
        assert ProviderType.LOCAL.value == "local"


class TestProviderCapabilities:
    """Tests for ProviderCapabilities dataclass."""

    def test_default_capabilities(self):
        """Test default capabilities are False."""
        caps = ProviderCapabilities()

        assert caps.embeddings is False
        assert caps.analysis is False
        assert caps.comparison is False
        assert caps.batch is False
        assert caps.streaming is False

    def test_custom_capabilities(self):
        """Test custom capabilities."""
        caps = ProviderCapabilities(
            embeddings=True,
            analysis=True,
            batch=True
        )

        assert caps.embeddings is True
        assert caps.analysis is True
        assert caps.batch is True
        assert caps.comparison is False


class TestAnalysisResult:
    """Tests for AnalysisResult dataclass."""

    def test_default_values(self):
        """Test default analysis result values."""
        result = AnalysisResult()

        assert result.topics == []
        assert result.themes == []
        assert result.suggested_tags == []
        assert result.quality == {"completeness": 0, "clarity": 0}
        assert result.suggestions == []
        assert result.raw_response is None

    def test_custom_values(self):
        """Test custom analysis result."""
        result = AnalysisResult(
            topics=["python", "testing"],
            themes=["development"],
            quality={"completeness": 8, "clarity": 9}
        )

        assert result.topics == ["python", "testing"]
        assert result.themes == ["development"]
        assert result.quality["completeness"] == 8


class TestComparisonResult:
    """Tests for ComparisonResult dataclass."""

    def test_default_values(self):
        """Test default comparison result values."""
        result = ComparisonResult()

        assert result.similarity_score == 0.0
        assert result.reason == ""
        assert result.should_merge is False
        assert result.merge_strategy is None

    def test_custom_values(self):
        """Test custom comparison result."""
        result = ComparisonResult(
            similarity_score=0.85,
            reason="Similar topics",
            should_merge=True,
            merge_strategy="Combine content"
        )

        assert result.similarity_score == 0.85
        assert result.should_merge is True


class TestGeminiAPIProvider:
    """Tests for GeminiAPIProvider."""

    def test_provider_attributes(self):
        """Test provider class attributes."""
        assert GeminiAPIProvider.name == "gemini-api"
        assert GeminiAPIProvider.provider_type == ProviderType.API
        assert GeminiAPIProvider.capabilities.embeddings is True
        assert GeminiAPIProvider.capabilities.batch is True
        assert GeminiAPIProvider.capabilities.analysis is True

    def test_init_default(self):
        """Test default initialization."""
        provider = GeminiAPIProvider()

        assert provider.model == "gemini-2.5-flash"
        assert provider.embedding_model == "text-embedding-004"
        assert provider._client is None

    def test_init_custom(self):
        """Test custom initialization."""
        provider = GeminiAPIProvider(
            api_key="test-key",
            model="custom-model"
        )

        assert provider.api_key == "test-key"
        assert provider.model == "custom-model"

    def test_is_available_no_key(self):
        """Test is_available returns False without API key."""
        with patch.dict('os.environ', {}, clear=True):
            provider = GeminiAPIProvider(api_key=None)
            # Clear any cached key
            provider.api_key = None
            assert provider.is_available() is False

    def test_get_status(self):
        """Test get_status returns dict."""
        provider = GeminiAPIProvider()
        status = provider.get_status()

        assert isinstance(status, dict)
        assert "name" in status
        assert "available" in status
        assert status["name"] == "gemini-api"


class TestGeminiCLIProvider:
    """Tests for GeminiCLIProvider."""

    def test_provider_attributes(self):
        """Test provider class attributes."""
        assert GeminiCLIProvider.name == "gemini-cli"
        assert GeminiCLIProvider.provider_type == ProviderType.CLI
        assert GeminiCLIProvider.capabilities.embeddings is False
        assert GeminiCLIProvider.capabilities.analysis is True

    def test_init(self):
        """Test initialization."""
        provider = GeminiCLIProvider(timeout=30)
        assert provider.timeout == 30

    def test_embedding_not_supported(self):
        """Test embeddings raise NotImplementedError."""
        provider = GeminiCLIProvider()

        with pytest.raises(NotImplementedError):
            provider.get_embedding("test")

        with pytest.raises(NotImplementedError):
            provider.get_embeddings_batch(["test"])


class TestClaudeCLIProvider:
    """Tests for ClaudeCLIProvider."""

    def test_provider_attributes(self):
        """Test provider class attributes."""
        assert ClaudeCLIProvider.name == "claude-cli"
        assert ClaudeCLIProvider.provider_type == ProviderType.CLI
        assert ClaudeCLIProvider.capabilities.embeddings is False
        assert ClaudeCLIProvider.capabilities.analysis is True

    def test_init(self):
        """Test initialization."""
        provider = ClaudeCLIProvider(timeout=180)
        assert provider.timeout == 180

    def test_embedding_not_supported(self):
        """Test embeddings raise NotImplementedError."""
        provider = ClaudeCLIProvider()

        with pytest.raises(NotImplementedError):
            provider.get_embedding("test")


class TestOllamaProvider:
    """Tests for OllamaProvider."""

    def test_provider_attributes(self):
        """Test provider class attributes."""
        assert OllamaProvider.name == "ollama"
        assert OllamaProvider.provider_type == ProviderType.LOCAL
        assert OllamaProvider.capabilities.embeddings is True
        assert OllamaProvider.capabilities.analysis is True

    def test_init_default(self):
        """Test default initialization."""
        provider = OllamaProvider()

        assert provider.base_url == "http://localhost:11434"
        assert provider.embedding_model == "nomic-embed-text"
        assert provider.chat_model == "llama3.1"

    def test_init_custom(self):
        """Test custom initialization."""
        provider = OllamaProvider(
            base_url="http://custom:8080",
            chat_model="mistral"
        )

        assert provider.base_url == "http://custom:8080"
        assert provider.chat_model == "mistral"

    @patch('requests.get')
    def test_is_available_running(self, mock_get):
        """Test is_available when Ollama is running."""
        mock_get.return_value = MagicMock(status_code=200)

        provider = OllamaProvider()
        assert provider.is_available() is True

    @patch('requests.get')
    def test_is_available_not_running(self, mock_get):
        """Test is_available when Ollama is not running."""
        mock_get.side_effect = Exception("Connection refused")

        provider = OllamaProvider()
        assert provider.is_available() is False

    def test_get_status(self):
        """Test get_status returns dict."""
        provider = OllamaProvider()
        status = provider.get_status()

        assert isinstance(status, dict)
        assert "name" in status
        assert "base_url" in status
        assert status["name"] == "ollama"


class TestBaseProviderMethods:
    """Tests for base provider utility methods."""

    def test_truncate_short_text(self):
        """Test truncate with short text."""
        provider = GeminiAPIProvider()
        text = "Short text"

        result = provider._truncate(text, 100)

        assert result == text

    def test_truncate_long_text(self):
        """Test truncate with long text."""
        provider = GeminiAPIProvider()
        text = "A" * 100

        result = provider._truncate(text, 50)

        assert len(result) == 53  # 50 + "..."
        assert result.endswith("...")

    def test_parse_json_response_valid(self):
        """Test parsing valid JSON response."""
        provider = GeminiAPIProvider()
        response = '{"score": 0.85, "reason": "Similar"}'

        result = provider._parse_json_response(response, {})

        assert result["score"] == 0.85
        assert result["reason"] == "Similar"

    def test_parse_json_response_with_text(self):
        """Test parsing JSON embedded in text."""
        provider = GeminiAPIProvider()
        response = 'Here is the analysis: {"score": 0.5} end.'

        result = provider._parse_json_response(response, {})

        assert result["score"] == 0.5

    def test_parse_json_response_invalid(self):
        """Test parsing invalid JSON returns default."""
        provider = GeminiAPIProvider()
        response = "not valid json"
        default = {"default": True}

        result = provider._parse_json_response(response, default)

        assert result == default
