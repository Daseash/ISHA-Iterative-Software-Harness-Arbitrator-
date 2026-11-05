"""
Calculator module — demo target for ISHA.

Contains seeded bugs for the eval suite:
  - subtract() uses + instead of -
  - divide() has no zero-division guard
"""


class Calculator:
    """A simple calculator with seeded bugs for ISHA to fix."""

    def add(self, a: float, b: float) -> float:
        """Return the sum of two numbers."""
        return a + b

    def subtract(self, a: float, b: float) -> float:
        """Return the difference of two numbers.

        BUG: uses + instead of -
        """
        return a + b  # BUG: should be a - b

    def multiply(self, a: float, b: float) -> float:
        """Return the product of two numbers."""
        return a * b

    def divide(self, a: float, b: float) -> float:
        """Return the quotient of two numbers.

        BUG: no zero-division guard — raises ZeroDivisionError
        instead of ValueError('Cannot divide by zero').
        """
        return a / b  # BUG: missing zero guard

    def percentage(self, value: float) -> float:
        """Return what percentage ``value`` is of some total.

        Example: percentage(25) with total=100 returns 25.0 — but this
        method only works when the total is 100 because the ``total``
        parameter is missing entirely.

        BUG: total is hardcoded to 100.  Should accept a ``total``
        parameter so callers can compute percentages against any
        denominator, not just 100.
        """
        return float(value)  # Only correct when total is 100
