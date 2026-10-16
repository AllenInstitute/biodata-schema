"""Tests for data asset naming regular expressions and helpers."""

import unittest
from datetime import datetime, timedelta, timezone

from biodata_schema.utils.data_name_patterns import (
    DataRegex,
    RegexParts,
    build_data_name,
    datetime_from_name_string,
    datetime_to_name_string,
)


class TestRegexParts(unittest.TestCase):
    """Tests for timestamp regular expression components."""

    def test_patterns_success(self):
        """Test valid date, time and timestamp strings."""
        self.assertRegex("20201019", RegexParts.DATE)
        self.assertRegex("083059", RegexParts.TIME)
        self.assertRegex("20201019T083059", RegexParts.DATETIME)

    def test_patterns_fail(self):
        """Test malformed date, time and timestamp strings."""
        self.assertNotRegex("10/19/2020", RegexParts.DATE)
        self.assertNotRegex("8:30:59", RegexParts.TIME)
        self.assertNotRegex("2020-10-19T08:30:59", RegexParts.DATETIME)


class TestDataRegex(unittest.TestCase):
    """Tests for current data asset naming patterns."""

    def test_patterns_success(self):
        """Test valid names and field values."""
        self.assertRegex("ecephys_20201019T083059", DataRegex.DATA)
        self.assertRegex("batch-17_20201019T083059", DataRegex.DATA)
        self.assertRegex("123455_20201019T083059_sorted_20201121T093158", DataRegex.DERIVED)
        self.assertRegex("project_analysis_30331221T042211", DataRegex.ANALYZED)
        self.assertRegex("abc-123<something>", DataRegex.NO_UNDERSCORES)
        self.assertRegex("abc efg - 123", DataRegex.NO_SPECIAL_CHARS_EXCEPT_SPACE)

    def test_patterns_fail(self):
        """Test malformed names and disallowed characters."""
        self.assertNotRegex("ecephys_20201019T083059+0000", DataRegex.DATA)
        self.assertNotRegex("ecephys_20201019T083059-0700", DataRegex.DATA)
        self.assertNotRegex("123455_20201019T083059_sorted_20201121T093158+0000", DataRegex.DERIVED)
        self.assertNotRegex("123455_20201019T083059+0000_sorted_20201121T093158", DataRegex.DERIVED)
        self.assertNotRegex("project_analysis_30331221T042211+0000", DataRegex.ANALYZED)
        self.assertNotRegex("ecephys_2020-10-19T08:30:59", DataRegex.DATA)
        self.assertNotRegex("123455_2020-10-19T083059_test", DataRegex.DATA)
        self.assertNotRegex("123455_2020-10-19T083059_sorted_2020-11-21T09:31:58", DataRegex.DERIVED)
        self.assertNotRegex("project_analysis_3033-12-21T042211_test", DataRegex.ANALYZED)
        self.assertNotRegex("abc_123<something>", DataRegex.NO_UNDERSCORES)
        for character in '<>:;"/|?\\_':
            self.assertNotRegex(
                f"abc efg - 123 {character}something{character}", DataRegex.NO_SPECIAL_CHARS_EXCEPT_SPACE
            )


class TestDataNamePatternsMethods(unittest.TestCase):
    """Tests for data asset naming helpers."""

    def test_datetime_to_name_string(self):
        """Test that naive datetimes keep their local time without an offset."""
        timestamp = datetime(2020, 12, 29, 1, 10, 50)
        self.assertEqual("20201229T011050", datetime_to_name_string(timestamp))

    def test_datetime_with_tz_to_name_string(self):
        """Test formatting a timezone-aware datetime."""
        self.assertEqual(
            "20201229T011050", datetime_to_name_string(datetime(2020, 12, 29, 1, 10, 50, tzinfo=timezone.utc))
        )

    def test_datetime_from_name_string(self):
        """Test parsing a data asset timestamp."""
        self.assertEqual(datetime(2020, 12, 29, 1, 10, 50), datetime_from_name_string("20201229T011050"))

    def test_historical_datetime_from_name_string(self):
        """Historical timestamps keep their original timezone-naive representation."""
        self.assertEqual(datetime(2020, 12, 29, 1, 10, 50), datetime_from_name_string("2020-12-29_01-10-50"))

    def test_offsets_are_omitted(self):
        """Positive and negative offsets preserve local wall time at second-level precision."""
        for offset in [timedelta(hours=-7), timedelta(hours=5, minutes=30), timedelta(seconds=30)]:
            timestamp = datetime(2020, 12, 29, 1, 10, 50, 123456, tzinfo=timezone(offset))
            name = datetime_to_name_string(timestamp)
            self.assertEqual("20201229T011050", name)
            self.assertEqual(timestamp.replace(tzinfo=None, microsecond=0), datetime_from_name_string(name))

    def test_datetime_from_name_string_invalid(self):
        """Test that invalid timestamps are rejected."""
        with self.assertRaises(ValueError):
            datetime_from_name_string("2020-12-29T01:10:50")
        for timestamp in ["20201229T011050+0000", "20201229T011050-0700"]:
            with self.assertRaises(ValueError):
                datetime_from_name_string(timestamp)

    def test_build_data_name(self):
        """Test constructing a name from its label and timestamp."""
        self.assertEqual(
            "123456_20201229T011050",
            build_data_name(label="123456", creation_datetime=datetime(2020, 12, 29, 1, 10, 50, tzinfo=timezone.utc)),
        )
