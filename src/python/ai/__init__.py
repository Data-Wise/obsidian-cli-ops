"""
AI Module for Obsidian CLI Ops.

Multi-provider AI architecture supporting:
- Gemini API (default, fast, batch, embeddings)
- Gemini CLI (fallback, free tier)
- Claude CLI (high quality)
- Ollama (local, free, private)

Usage:
    from ai import get_ai_client

    # Auto-select best provider
    client = get_ai_client()
    embedding = client.get_embedding("some text")
    analysis = client.analyze_note(content, title)

    # Force specific provider
    client = get_ai_client(provider="ollama")

    # Check status
    from ai.config import print_status
    print_status()
"""

from .router import AIRouter, get_ai_client, OperationType
from .config import AIConfig, get_config, print_status, setup_wizard
from .providers.base import (
    AIProvider,
    ProviderType,
    ProviderCapabilities,
    AnalysisResult,
    ComparisonResult,
)

__all__ = [
    # Main entry points
    'get_ai_client',
    'AIRouter',
    'OperationType',
    # Configuration
    'AIConfig',
    'get_config',
    'print_status',
    'setup_wizard',
    # Base types
    'AIProvider',
    'ProviderType',
    'ProviderCapabilities',
    'AnalysisResult',
    'ComparisonResult',
]
