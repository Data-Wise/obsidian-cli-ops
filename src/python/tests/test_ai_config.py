"""Tests for AI config module."""

import pytest
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, str(__file__).rsplit('/', 2)[0])

from ai.config import AIConfig, get_config, save_config


class TestAIConfig:
    """Tests for AIConfig dataclass."""

    def test_default_values(self):
        """Test default configuration values."""
        config = AIConfig()

        assert config.preferred_provider is None
        assert config.provider_priority == [
            "gemini-api", "ollama", "gemini-cli", "claude-cli"
        ]
        assert config.gemini_model == "gemini-2.5-flash"
        assert config.gemini_embedding_model == "text-embedding-004"
        assert config.ollama_chat_model == "llama3.1"
        assert config.ollama_embedding_model == "nomic-embed-text"
        assert config.ollama_base_url == "http://localhost:11434"
        assert config.timeout == 60
        assert config.auto_install == "prompt"
        assert config.show_install_hints is True

    def test_custom_values(self):
        """Test configuration with custom values."""
        config = AIConfig(
            preferred_provider="ollama",
            timeout=120,
            auto_install="never"
        )

        assert config.preferred_provider == "ollama"
        assert config.timeout == 120
        assert config.auto_install == "never"

    def test_to_dict(self):
        """Test conversion to dictionary."""
        config = AIConfig()
        data = config.to_dict()

        assert isinstance(data, dict)
        assert "preferred_provider" in data
        assert "provider_priority" in data
        assert "auto_install" in data

    def test_save_and_load(self):
        """Test saving and loading config."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = Path(tmpdir) / "ai.json"

            # Patch CONFIG_FILE to use temp directory
            with patch('ai.config.CONFIG_FILE', config_file):
                with patch('ai.config.CONFIG_DIR', Path(tmpdir)):
                    # Create and save config
                    config = AIConfig(
                        preferred_provider="ollama",
                        auto_install="always"
                    )
                    config.save()

                    # Verify file exists
                    assert config_file.exists()

                    # Load and verify
                    loaded = AIConfig.load()
                    assert loaded.preferred_provider == "ollama"
                    assert loaded.auto_install == "always"

    def test_load_missing_file(self):
        """Test loading when config file doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = Path(tmpdir) / "nonexistent.json"

            with patch('ai.config.CONFIG_FILE', config_file):
                config = AIConfig.load()
                # Should return default config
                assert config.preferred_provider is None
                assert config.auto_install == "prompt"

    def test_load_invalid_json(self):
        """Test loading invalid JSON file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = Path(tmpdir) / "ai.json"
            config_file.write_text("invalid json {{{")

            with patch('ai.config.CONFIG_FILE', config_file):
                config = AIConfig.load()
                # Should return default config on error
                assert config.preferred_provider is None


class TestGetApiKey:
    """Tests for get_api_key method."""

    def test_gemini_api_key_google(self):
        """Test getting Gemini API key from GOOGLE_API_KEY."""
        config = AIConfig()

        with patch.dict(os.environ, {"GOOGLE_API_KEY": "test-key"}, clear=False):
            key = config.get_api_key("gemini-api")
            assert key == "test-key"

    def test_gemini_api_key_gemini(self):
        """Test getting Gemini API key from GEMINI_API_KEY."""
        config = AIConfig()

        with patch.dict(os.environ, {"GEMINI_API_KEY": "test-key-2"}, clear=False):
            # Clear GOOGLE_API_KEY if set
            env = {"GEMINI_API_KEY": "test-key-2"}
            if "GOOGLE_API_KEY" in os.environ:
                env["GOOGLE_API_KEY"] = ""

            with patch.dict(os.environ, env, clear=False):
                key = config.get_api_key("gemini")
                # Will return GOOGLE_API_KEY first if set, then GEMINI_API_KEY
                assert key is not None

    def test_anthropic_api_key(self):
        """Test getting Anthropic API key."""
        config = AIConfig()

        with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "anthropic-key"}, clear=False):
            key = config.get_api_key("claude")
            assert key == "anthropic-key"

    def test_unknown_provider_key(self):
        """Test getting key for unknown provider."""
        config = AIConfig()
        key = config.get_api_key("unknown")
        assert key is None


class TestConfigHelpers:
    """Tests for config helper functions."""

    def test_get_config(self):
        """Test get_config returns AIConfig instance."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = Path(tmpdir) / "ai.json"

            with patch('ai.config.CONFIG_FILE', config_file):
                config = get_config()
                assert isinstance(config, AIConfig)

    def test_save_config(self):
        """Test save_config saves to file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = Path(tmpdir) / "ai.json"

            with patch('ai.config.CONFIG_FILE', config_file):
                with patch('ai.config.CONFIG_DIR', Path(tmpdir)):
                    config = AIConfig(preferred_provider="test")
                    save_config(config)

                    assert config_file.exists()
                    data = json.loads(config_file.read_text())
                    assert data["preferred_provider"] == "test"
