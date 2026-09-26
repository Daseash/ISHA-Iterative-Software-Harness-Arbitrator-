"""
Calculator module — Target test codebase with intentional bugs.

This module contains a simple Calculator class with deliberate bugs
that ISHA's agentic loop should be able to detect and fix.

Bugs:
    1. subtract() returns a + b instead of a - b
    2. divide() doesn't handle division by zero
"""


class Calculator:
    """A simple calculator with intentional bugs for testing ISHA."""

    def add(self, a: float, b: float) -> float:
        """Add two numbers. (Works correctly)"""
        return a + b

    def subtract(self, a: float, b: float) -> float:
        """Subtract b from a.

        BUG: Returns a + b instead of a - b.
        ISHA should detect and fix this.
        """
        return a + b  # 🐛 BUG: should be a - b

    def divide(self, a: float, b: float) -> float:
        """Divide a by b.

        BUG: Doesn't handle division by zero.
        ISHA should add a proper check and raise ValueError.
        """
        return a / b  # 🐛 BUG: no ZeroDivisionError handling

    def multiply(self, a: float, b: float) -> float:
        """Multiply two numbers. (Works correctly)"""
        return a * b
