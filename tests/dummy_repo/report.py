"""
Report module — renders Calculator results through the Formatter.

Third link in the multi-file call chain:
    calculator.py  ->  formatter.py  ->  report.py

Any change to Calculator's method signatures (e.g. adding ``total`` to
percentage(), or renaming subtract()) must be propagated through the
formatter AND this file, otherwise the report layer breaks at runtime.
"""

try:
    from formatter import format_difference, format_percentage
except ImportError:
    from tests.dummy_repo.formatter import format_difference, format_percentage


def difference_report(values: list) -> str:
    """Build a report of pairwise differences for a list of numbers."""
    lines = []
    for a, b in zip(values, values[1:]):
        lines.append(format_difference(a, b))
    return "\n".join(lines)


def percentage_report(part: float, whole: float) -> str:
    """Build a report line showing ``part`` as a share of ``whole``."""
    return f"share: {format_percentage(part, whole)}"


def summary(values: list) -> str:
    """Combined report: differences plus the first value's share of the total."""
    total = values[-1] if values else 0
    return difference_report(values) + "\n" + percentage_report(values[0], total)
