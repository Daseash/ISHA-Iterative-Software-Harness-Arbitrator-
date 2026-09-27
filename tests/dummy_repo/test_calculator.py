"""
Calculator tests — eval suite expects TestSubtract and TestDivide selectors.

These tests are GREEN against the *correct* calculator and RED against the
seeded bugs, which is what ISHA's regression-test-first loop verifies.
"""

import pytest

from calculator import Calculator


class TestAdd:
    """Sanity: add() has no bug — these should always pass."""

    def test_add_positive(self):
        assert Calculator().add(2, 3) == 5

    def test_add_negative(self):
        assert Calculator().add(-1, -1) == -2

    def test_add_zero(self):
        assert Calculator().add(0, 0) == 0


class TestSubtract:
    """FAIL before fix: subtract() returns a+b instead of a-b."""

    def test_subtract_positive(self):
        assert Calculator().subtract(5, 3) == 2

    def test_subtract_negative(self):
        assert Calculator().subtract(-1, -1) == 0

    def test_subtract_zero(self):
        assert Calculator().subtract(7, 0) == 7


class TestMultiply:
    """Sanity: multiply() has no bug."""

    def test_multiply_basic(self):
        assert Calculator().multiply(3, 4) == 12

    def test_multiply_zero(self):
        assert Calculator().multiply(5, 0) == 0


class TestDivide:
    """FAIL before fix: divide(x, 0) must raise ValueError, not ZeroDivisionError."""

    def test_divide_basic(self):
        assert Calculator().divide(10, 2) == 5.0

    def test_divide_by_zero(self):
        with pytest.raises(ValueError, match="Cannot divide by zero"):
            Calculator().divide(10, 0)
