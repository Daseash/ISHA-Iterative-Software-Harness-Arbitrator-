"""
Tests for the formatter module — exercises the multi-file percentage bug.

The percentage bug spans two files:
  - calculator.py: percentage() hardcodes total=100 (missing parameter)
  - formatter.py:  format_percentage() can't pass the denominator

Tests that use whole=100 pass accidentally; tests with other totals FAIL.
"""

import pytest

try:
    from formatter import format_percentage, format_difference
except ImportError:
    from tests.dummy_repo.formatter import format_percentage, format_difference


class TestFormatPercentage:
    """FAIL before fix: percentage() hardcodes total=100."""

    def test_non_100_total(self):
        """25 out of 200 = 12.5%, not 25.0%."""
        assert format_percentage(25, 200) == "12.5%"

    def test_small_fraction(self):
        """1 out of 1000 = 0.1%, not 1.0%."""
        assert format_percentage(1, 1000) == "0.1%"

    def test_half(self):
        """50 out of 100 = 50.0% — passes by accident (whole=100)."""
        assert format_percentage(50, 100) == "50.0%"

    def test_full(self):
        """100 out of 100 = 100.0% — passes by accident (whole=100)."""
        assert format_percentage(100, 100) == "100.0%"


class TestFormatDifference:
    """FAIL before fix: depends on the subtract bug in calculator.py."""

    def test_basic_difference(self):
        assert format_difference(10, 3) == "10 - 3 = 7"
