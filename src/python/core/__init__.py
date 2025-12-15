"""
Core business logic layer for Obsidian CLI Ops.

This package contains interface-agnostic business logic that can be used
by CLI, TUI, GUI, or any other presentation layer.

Architecture:
    - models.py: Domain models (Vault, Note, ScanResult, etc.)
    - vault_manager.py: Vault operations orchestrator
    - graph_analyzer.py: Graph analysis orchestrator
    - exceptions.py: Custom exceptions for domain logic
"""

from .models import (
    Vault,
    Note,
    ScanResult,
    GraphMetrics,
    VaultStats,
)
from .vault_manager import VaultManager
from .graph_analyzer import GraphAnalyzer
from .exceptions import (
    ObsidianCoreError,
    VaultNotFoundError,
    ScanError,
    AnalysisError,
)

__all__ = [
    # Models
    'Vault',
    'Note',
    'ScanResult',
    'GraphMetrics',
    'VaultStats',
    # Managers
    'VaultManager',
    'GraphAnalyzer',
    # Exceptions
    'ObsidianCoreError',
    'VaultNotFoundError',
    'ScanError',
    'AnalysisError',
]
