"""
Utility functions for Obsidian CLI Ops.

Shared helpers used across CLI, TUI, and core layers.
"""

from datetime import datetime
from typing import Optional, Union
import logging
import os
from pathlib import Path
import subprocess
import platform


def copy_to_clipboard(text: str) -> bool:
    """
    Copy text to system clipboard using native tools.
    
    Args:
        text: Text to copy
        
    Returns:
        True if successful, False otherwise
    """
    system = platform.system()
    try:
        if system == 'Darwin':  # macOS
            process = subprocess.Popen(['pbcopy'], stdin=subprocess.PIPE)
            process.communicate(text.encode('utf-8'))
            return process.returncode == 0
            
        elif system == 'Windows':
            process = subprocess.Popen(['clip'], stdin=subprocess.PIPE, shell=True)
            process.communicate(text.encode('utf-8'))
            return process.returncode == 0
            
        elif system == 'Linux':
            # Try wl-copy first (Wayland)
            try:
                process = subprocess.Popen(['wl-copy'], stdin=subprocess.PIPE)
                process.communicate(text.encode('utf-8'))
                return process.returncode == 0
            except FileNotFoundError:
                pass
                
            # Try xclip (X11)
            try:
                process = subprocess.Popen(['xclip', '-selection', 'clipboard'], stdin=subprocess.PIPE)
                process.communicate(text.encode('utf-8'))
                return process.returncode == 0
            except FileNotFoundError:
                pass
                
            # Try xsel (X11)
            try:
                process = subprocess.Popen(['xsel', '--clipboard', '--input'], stdin=subprocess.PIPE)
                process.communicate(text.encode('utf-8'))
                return process.returncode == 0
            except FileNotFoundError:
                pass

    except Exception as e:
        logging.error(f"Clipboard copy failed: {e}")
        
    return False


def get_log_file_path() -> Path:
    """Get the path to the log file."""
    config_dir = Path.home() / ".config" / "obs"
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir / "obs.log"


from logging.handlers import RotatingFileHandler

def setup_logging(level=logging.INFO) -> Path:
    """
    Configure logging to file with rotation and return the log file path.
    
    Args:
        level: Logging level (default: logging.INFO)
        
    Returns:
        Path to the log file
    """
    log_file = get_log_file_path()
    
    # Create a rotating file handler
    # Max size: 5MB, Backup count: 3
    handler = RotatingFileHandler(
        log_file,
        maxBytes=5*1024*1024,
        backupCount=3,
        encoding='utf-8'
    )
    
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - [%(levelname)s] - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    handler.setFormatter(formatter)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    
    # Remove existing handlers to avoid duplicates
    if root_logger.hasHandlers():
        root_logger.handlers.clear()
        
    root_logger.addHandler(handler)
    
    return log_file


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
