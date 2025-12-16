"""Tests for utility functions."""

import pytest
from datetime import datetime, timedelta
from utils import (
    format_relative_time,
    format_timestamp,
    format_number,
    truncate_string,
)


class TestFormatRelativeTime:
    """Tests for format_relative_time function."""

    def test_none_returns_never(self):
        """Test None input returns 'Never'."""
        assert format_relative_time(None) == "Never"

    def test_empty_string_returns_never(self):
        """Test empty string returns 'Never'."""
        assert format_relative_time("") == "Never"
        assert format_relative_time("   ") == "Never"

    def test_just_now(self):
        """Test timestamps less than 1 minute ago."""
        now = datetime.now()
        assert format_relative_time(now) == "Just now"

        seconds_ago = now - timedelta(seconds=30)
        assert format_relative_time(seconds_ago) == "Just now"

    def test_minutes_ago(self):
        """Test timestamps minutes ago."""
        now = datetime.now()

        one_min = now - timedelta(minutes=1)
        assert format_relative_time(one_min) == "1 minute ago"

        five_mins = now - timedelta(minutes=5)
        assert format_relative_time(five_mins) == "5 minutes ago"

        fifty_nine_mins = now - timedelta(minutes=59)
        assert format_relative_time(fifty_nine_mins) == "59 minutes ago"

    def test_hours_ago(self):
        """Test timestamps hours ago."""
        now = datetime.now()

        one_hour = now - timedelta(hours=1)
        assert format_relative_time(one_hour) == "1 hour ago"

        three_hours = now - timedelta(hours=3)
        assert format_relative_time(three_hours) == "3 hours ago"

        twenty_three_hours = now - timedelta(hours=23)
        assert format_relative_time(twenty_three_hours) == "23 hours ago"

    def test_days_ago(self):
        """Test timestamps days ago."""
        now = datetime.now()

        one_day = now - timedelta(days=1)
        assert format_relative_time(one_day) == "1 day ago"

        five_days = now - timedelta(days=5)
        assert format_relative_time(five_days) == "5 days ago"

    def test_weeks_ago(self):
        """Test timestamps weeks ago."""
        now = datetime.now()

        one_week = now - timedelta(weeks=1)
        assert format_relative_time(one_week) == "1 week ago"

        three_weeks = now - timedelta(weeks=3)
        assert format_relative_time(three_weeks) == "3 weeks ago"

    def test_old_timestamps_show_date(self):
        """Test timestamps older than 30 days show date."""
        old = datetime.now() - timedelta(days=45)
        result = format_relative_time(old)
        assert result == old.strftime('%Y-%m-%d')

    def test_iso_string_input(self):
        """Test ISO format string input."""
        now = datetime.now()
        iso_str = now.isoformat()
        result = format_relative_time(iso_str)
        assert result == "Just now"

    def test_iso_string_with_z(self):
        """Test ISO format string with Z timezone."""
        # 5 minutes ago in UTC
        dt = datetime.utcnow() - timedelta(minutes=5)
        iso_str = dt.isoformat() + "Z"
        result = format_relative_time(iso_str)
        assert "minute" in result

    def test_invalid_input_returns_string(self):
        """Test invalid input returns string representation."""
        result = format_relative_time("not-a-date")
        assert result == "not-a-date"


class TestFormatTimestamp:
    """Tests for format_timestamp function."""

    def test_none_returns_never(self):
        """Test None input returns 'Never'."""
        assert format_timestamp(None) == "Never"

    def test_empty_string_returns_never(self):
        """Test empty string returns 'Never'."""
        assert format_timestamp("") == "Never"

    def test_default_format(self):
        """Test default format string."""
        dt = datetime(2024, 12, 15, 14, 30, 0)
        assert format_timestamp(dt) == "2024-12-15 14:30"

    def test_custom_format(self):
        """Test custom format string."""
        dt = datetime(2024, 12, 15, 14, 30, 0)
        assert format_timestamp(dt, '%Y/%m/%d') == "2024/12/15"
        assert format_timestamp(dt, '%H:%M:%S') == "14:30:00"

    def test_iso_string_input(self):
        """Test ISO format string input."""
        iso_str = "2024-12-15T14:30:00"
        assert format_timestamp(iso_str) == "2024-12-15 14:30"


class TestFormatNumber:
    """Tests for format_number function."""

    def test_small_number(self):
        """Test small numbers."""
        assert format_number(5) == "5"
        assert format_number(999) == "999"

    def test_thousands(self):
        """Test numbers with thousands."""
        assert format_number(1000) == "1,000"
        assert format_number(12345) == "12,345"
        assert format_number(1234567) == "1,234,567"

    def test_with_suffix(self):
        """Test with suffix."""
        assert format_number(5, ' notes') == "5 notes"
        assert format_number(1234, ' items') == "1,234 items"


class TestTruncateString:
    """Tests for truncate_string function."""

    def test_short_string_unchanged(self):
        """Test short strings are unchanged."""
        assert truncate_string("hello", 10) == "hello"
        assert truncate_string("hello", 5) == "hello"

    def test_long_string_truncated(self):
        """Test long strings are truncated."""
        assert truncate_string("hello world", 8) == "hello..."
        assert truncate_string("hello world", 10) == "hello w..."

    def test_custom_suffix(self):
        """Test custom suffix."""
        assert truncate_string("hello world", 8, '…') == "hello w…"
        assert truncate_string("hello world", 8, '>>') == "hello >>"
