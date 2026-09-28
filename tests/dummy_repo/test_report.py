"""
Tests for the report module — exercises the bug across all three files.

Call chain: calculator.py -> formatter.py -> report.py
FAIL before fix: the percentage() bug in calculator.py propagates through
formatter.format_percentage() into report.percentage_report().
"""

import pytest

try:
    from report import difference_report, percentage_report, summary
except ImportError:
    from tests.dummy_repo.report import difference_report, percentage_report, summary


class TestPercentageReport:
    """FAIL before fix: percentage() hardcodes total=100."""

    def test_share_of_200(self):
        """25 of 200 = 12.5% — needs `total` threaded through all 3 files."""
        assert percentage_report(25, 200) == "share: 12.5%"

    def test_share_of_1000(self):
        assert percentage_report(1, 1000) == "share: 0.1%"

    def test_share_of_100_passes_accidentally(self):
        assert percentage_report(50, 100) == "share: 50.0%"


class TestDifferenceReport:
    """FAIL before fix: depends on the subtract bug in calculator.py."""

    def test_pairwise_differences(self):
        assert difference_report([10, 3, 1]) == "10 - 3 = 7\n3 - 1 = 2"

    def test_single_value_yields_no_lines(self):
        assert difference_report([5]) == ""


class TestSummary:
    def test_summary_combines_both(self):
        assert summary([25, 200]) == "25 - 200 = -175\nshare: 12.5%"
