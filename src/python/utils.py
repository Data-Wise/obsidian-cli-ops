"""
Utility functions for Obsidian CLI Ops.

Shared helpers used across CLI, TUI, and core layers.
"""

from datetime import datetime
from typing import Optional, Union


def format_relative_time(timestamp: Optional[Union[datetime, str]]) -> str:
    """Format timestamp as human-readable relative time.

    Args:
        timestamp: datetime object, ISO timestamp string, or None

    Returns:
        Human-readable relative time (e.g., "5 minutes ago", "2 days ago")

    Examples:
        >>> format_relative_time(None)
        'Never'
        >>> format_relative_time(datetime.now())
        'Just now'
    """
    if not timestamp:
        return "Never"

    try:
        if isinstance(timestamp, str):
            if not timestamp.strip():
                return "Never"
            dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        else:
            dt = timestamp

        now = datetime.now(dt.tzinfo) if dt.tzinfo else datetime.now()
        delta = now - dt

        seconds = delta.total_seconds()

        # Handle future timestamps (shouldn't happen, but just in case)
        if seconds < 0:
            return "Just now"

        if seconds < 60:
            return "Just now"
        elif seconds < 3600:
            minutes = int(seconds / 60)
            return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
        elif seconds < 86400:
            hours = int(seconds / 3600)
            return f"{hours} hour{'s' if hours != 1 else ''} ago"
        elif seconds < 604800:  # Less than a week
            days = int(seconds / 86400)
            return f"{days} day{'s' if days != 1 else ''} ago"
        elif seconds < 2592000:  # Less than 30 days
            weeks = int(seconds / 604800)
            return f"{weeks} week{'s' if weeks != 1 else ''} ago"
        else:
            # For older timestamps, show the date
            return dt.strftime('%Y-%m-%d')

    except (ValueError, TypeError, AttributeError):
        return str(timestamp) if timestamp else "Never"


def format_timestamp(timestamp: Optional[Union[datetime, str]],
                     format_str: str = '%Y-%m-%d %H:%M') -> str:
    """Format timestamp as absolute date/time string.

    Args:
        timestamp: datetime object, ISO timestamp string, or None
        format_str: strftime format string (default: '%Y-%m-%d %H:%M')

    Returns:
        Formatted date/time string or 'Never' if timestamp is None/empty
    """
    if not timestamp:
        return "Never"

    try:
        if isinstance(timestamp, str):
            if not timestamp.strip():
                return "Never"
            dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        else:
            dt = timestamp

        return dt.strftime(format_str)

    except (ValueError, TypeError, AttributeError):
        return str(timestamp) if timestamp else "Never"


def format_number(value: int, suffix: str = '') -> str:
    """Format number with thousands separator.

    Args:
        value: Integer to format
        suffix: Optional suffix (e.g., ' notes')

    Returns:
        Formatted string with commas (e.g., "1,234 notes")
    """
    return f"{value:,}{suffix}"


def truncate_string(text: str, max_length: int = 50, suffix: str = '...') -> str:
    """Truncate string to max length with suffix.

    Args:
        text: String to truncate
        max_length: Maximum length (including suffix)
        suffix: String to append when truncated

    Returns:
        Truncated string or original if shorter than max_length
    """
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix
