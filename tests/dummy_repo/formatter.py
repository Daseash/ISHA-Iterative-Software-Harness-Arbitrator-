"""
Formatter module — produces display strings using Calculator.

Contains a multi-file bug: format_percentage() cannot pass the ``whole``
denominator to Calculator.percentage() because that method only accepts
a single ``value`` argument (total is hardcoded to 100).

Fixing this requires changes to BOTH files:
  1. calculator.py — add a ``total`` parameter to percentage()
  2. formatter.py  — pass ``whole`` to the new parameter
"""

try:
    from calculator import Calculator
except ImportError:
    from tests.dummy_repo.calculator import Calculator

_calc = Calculator()


def format_percentage(part: float, whole: float) -> str:
    """Format a part-of-whole as a human-readable percentage string.

    BUG: Cannot pass ``whole`` to percentage() because it only takes
    one argument.  Result is wrong whenever ``whole != 100``.
    """
    pct = _calc.percentage(part)  # BUG: can't pass whole
    return f"{pct:.1f}%"


def format_difference(a: float, b: float) -> str:
    """Format the difference between two numbers."""
    diff = _calc.subtract(a, b)
    return f"{a} - {b} = {diff}"
