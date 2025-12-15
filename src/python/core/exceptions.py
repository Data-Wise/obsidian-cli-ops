"""
Custom exceptions for Obsidian CLI Ops core layer.

These exceptions are raised by business logic and can be caught
by presentation layers for appropriate error handling.
"""


class ObsidianCoreError(Exception):
    """Base exception for all core layer errors."""
    pass


class VaultNotFoundError(ObsidianCoreError):
    """Raised when a vault cannot be found or is invalid."""
    pass


class ScanError(ObsidianCoreError):
    """Raised when vault scanning fails."""
    pass


class AnalysisError(ObsidianCoreError):
    """Raised when graph analysis fails."""
    pass


class DatabaseError(ObsidianCoreError):
    """Raised when database operations fail."""
    pass
