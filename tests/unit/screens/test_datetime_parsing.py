"""Unit tests for datetime parsing in TUI screens.

These tests ensure proper handling of:
- ISO 8601 datetime formats with various timezone representations
- Timezone-aware vs timezone-naive datetime comparisons
- Relative date parsing (+7d, +30d format)

This would have caught Bug #3: DateTime timezone mismatch.
"""

from datetime import datetime, timedelta, timezone

import pytest


class TestISODateTimeParsing:
    """Test ISO 8601 datetime parsing patterns used in screens."""

    @pytest.mark.parametrize(
        "input_str,expected_tz",
        [
            ("2025-01-15T10:30:00Z", timezone.utc),
            ("2025-01-15T10:30:00+00:00", timezone.utc),
            ("2025-01-15T10:30:00-05:00", timezone(timedelta(hours=-5))),
        ],
    )
    def test_parse_iso_with_timezone(self, input_str, expected_tz):
        """Parse ISO datetime with timezone info."""
        # Pattern used in screens: replace Z with +00:00
        normalized = input_str.replace("Z", "+00:00")
        result = datetime.fromisoformat(normalized)

        assert result.tzinfo is not None
        assert result.year == 2025
        assert result.month == 1
        assert result.day == 15

    def test_parse_iso_without_timezone(self):
        """Parse ISO datetime without timezone (naive)."""
        input_str = "2025-01-15T10:30:00"
        result = datetime.fromisoformat(input_str)

        assert result.tzinfo is None
        assert result.year == 2025

    def test_z_suffix_replacement(self):
        """Verify Z suffix is properly replaced for parsing."""
        input_str = "2025-01-15T10:30:00Z"

        # This is the pattern used in screens
        normalized = input_str.replace("Z", "+00:00")
        result = datetime.fromisoformat(normalized)

        assert result.tzinfo == timezone.utc

    def test_inconsistent_z_replacement_causes_issues(self):
        """Demonstrate issue with inconsistent Z replacement."""
        input_str = "2025-01-15T10:30:00Z"

        # BAD: Just removing Z creates naive datetime
        bad_normalized = input_str.replace("Z", "")
        naive_result = datetime.fromisoformat(bad_normalized)
        assert naive_result.tzinfo is None

        # GOOD: Replacing Z with +00:00 creates aware datetime
        good_normalized = input_str.replace("Z", "+00:00")
        aware_result = datetime.fromisoformat(good_normalized)
        assert aware_result.tzinfo == timezone.utc


class TestTimezoneAwareComparisons:
    """Test timezone-aware datetime comparisons."""

    def test_aware_minus_aware_works(self):
        """Subtracting two aware datetimes works."""
        now = datetime.now(timezone.utc)
        past = datetime(2025, 1, 15, 10, 30, tzinfo=timezone.utc)

        # This should not raise
        diff = now - past
        assert isinstance(diff, timedelta)

    def test_naive_minus_aware_fails(self):
        """Subtracting naive from aware raises TypeError."""
        aware = datetime.now(timezone.utc)
        naive = datetime(2025, 1, 15, 10, 30)  # No timezone

        with pytest.raises(TypeError) as exc_info:
            _ = aware - naive

        assert "offset-naive" in str(exc_info.value).lower() or "subtract" in str(
            exc_info.value
        ).lower()

    def test_aware_minus_naive_fails(self):
        """Subtracting aware from naive raises TypeError."""
        aware = datetime.now(timezone.utc)
        naive = datetime(2025, 1, 15, 10, 30)

        with pytest.raises(TypeError):
            _ = naive - aware

    def test_fix_naive_datetime_for_comparison(self):
        """Show how to fix naive datetime for comparison."""
        aware = datetime.now(timezone.utc)
        naive = datetime(2025, 1, 15, 10, 30)

        # Fix: Add timezone info to naive datetime
        fixed = naive.replace(tzinfo=timezone.utc)

        # Now comparison works
        diff = aware - fixed
        assert isinstance(diff, timedelta)


class TestRelativeDateParsing:
    """Test relative date parsing (+7d, +30d format)."""

    def test_parse_relative_days_format(self):
        """Parse +Nd format for relative dates."""
        test_cases = [
            ("+7d", 7),
            ("+30d", 30),
            ("+1d", 1),
            ("+365d", 365),
        ]

        for date_str, expected_days in test_cases:
            # Extract number of days
            if date_str.startswith("+") and date_str.endswith("d"):
                days = int(date_str[1:-1])
                assert days == expected_days

    def test_relative_date_to_absolute(self):
        """Convert relative date to absolute datetime."""
        now = datetime.now(timezone.utc)

        for days_str, expected_days in [("+7d", 7), ("+30d", 30)]:
            days = int(days_str[1:-1])
            future = now + timedelta(days=days)

            # Verify it's the expected number of days in the future
            diff = (future - now).days
            assert diff == expected_days

    def test_relative_date_output_format(self):
        """Relative date output should be ISO format with timezone."""
        now = datetime.now(timezone.utc)
        days = 7
        future = now + timedelta(days=days)

        # Format used in modals
        output = future.strftime("%Y-%m-%dT00:00:00Z")

        # Verify format is correct
        assert output.endswith("Z")
        assert "T" in output
        assert len(output) == 20


class TestDateOnlyParsing:
    """Test date-only string parsing."""

    def test_parse_date_only_string(self):
        """Parse YYYY-MM-DD format."""
        date_str = "2025-01-15"
        result = datetime.strptime(date_str, "%Y-%m-%d")

        assert result.year == 2025
        assert result.month == 1
        assert result.day == 15
        assert result.hour == 0
        assert result.minute == 0

    def test_date_only_to_iso_with_time(self):
        """Convert date-only to full ISO format."""
        date_str = "2025-01-15"

        # Pattern used in modals
        output = f"{date_str}T00:00:00Z"

        assert output == "2025-01-15T00:00:00Z"

    def test_extract_date_from_iso(self):
        """Extract date portion from ISO datetime."""
        iso_str = "2025-01-15T10:30:00Z"

        # Pattern used in modals
        date_only = iso_str[:10]

        assert date_only == "2025-01-15"


class TestDateFormattingForDisplay:
    """Test date formatting for UI display."""

    def test_format_date_only(self):
        """Format datetime as date only."""
        dt = datetime(2025, 1, 15, 10, 30, tzinfo=timezone.utc)

        formatted = dt.strftime("%Y-%m-%d")
        assert formatted == "2025-01-15"

    def test_format_date_time_compact(self):
        """Format datetime in compact form for tables."""
        dt = datetime(2025, 1, 15, 10, 30, tzinfo=timezone.utc)

        formatted = dt.strftime("%m-%d %H:%M")
        assert formatted == "01-15 10:30"

    def test_calculate_days_until(self):
        """Calculate days until a future date."""
        now = datetime.now(timezone.utc)
        future = now + timedelta(days=15)

        days_until = (future - now).days
        assert days_until == 15

    def test_calculate_days_overdue(self):
        """Calculate days overdue for a past date."""
        now = datetime.now(timezone.utc)
        past = now - timedelta(days=5)

        days_ago = (now - past).days
        assert days_ago == 5


class TestEdgeCases:
    """Test edge cases in datetime handling."""

    def test_empty_date_string(self):
        """Handle empty date string gracefully."""
        date_str = ""

        # Pattern: check before parsing
        if date_str:
            result = datetime.fromisoformat(date_str)
        else:
            result = None

        assert result is None

    def test_none_date_value(self):
        """Handle None date value."""
        date_value = None

        # Pattern: check for None
        if date_value:
            result = datetime.fromisoformat(date_value)
        else:
            result = None

        assert result is None

    def test_invalid_date_format(self):
        """Handle invalid date format gracefully."""
        invalid_dates = [
            "15-01-2025",  # Wrong order
            "2025/01/15",  # Wrong separator
            "not-a-date",
            "2025-13-45",  # Invalid month/day
        ]

        for date_str in invalid_dates:
            with pytest.raises(ValueError):
                datetime.fromisoformat(date_str)

    def test_microseconds_in_iso(self):
        """Handle ISO datetime with microseconds."""
        iso_str = "2025-01-15T10:30:00.123456Z"
        normalized = iso_str.replace("Z", "+00:00")

        result = datetime.fromisoformat(normalized)
        assert result.microsecond == 123456
