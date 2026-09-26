"""
Tests for Calculator — These tests expose the intentional bugs.

Running `pytest test_calculator.py` should produce FAILURES because
the bugs in calculator.py haven't been fixed yet. ISHA's job is to
fix calculator.py so all these tests pass.
"""

import pytest

from calculator import Calculator


@pytest.fixture
def calc():
    """Create a fresh Calculator instance for each test."""
    return Calculator()


# ── add() tests — should all PASS ───────────────────────────────────────────


class TestAdd:
    def test_add_positive(self, calc):
        assert calc.add(2, 3) == 5

    def test_add_negative(self, calc):
        assert calc.add(-1, -1) == -2

    def test_add_zero(self, calc):
        assert calc.add(0, 0) == 0

    def test_add_mixed(self, calc):
        assert calc.add(-5, 3) == -2

    def test_add_floats(self, calc):
        assert calc.add(1.5, 2.5) == 4.0


# ── subtract() tests — should FAIL due to bug ──────────────────────────────


class TestSubtract:
    def test_subtract_positive(self, calc):
        """This will FAIL: subtract(5, 3) returns 8 instead of 2."""
        assert calc.subtract(5, 3) == 2

    def test_subtract_negative(self, calc):
        """This will FAIL: subtract(-1, -1) returns -2 instead of 0."""
        assert calc.subtract(-1, -1) == 0

    def test_subtract_zero(self, calc):
        """This passes by accident: subtract(0, 0) = 0 + 0 = 0."""
        assert calc.subtract(0, 0) == 0

    def test_subtract_result_negative(self, calc):
        """This will FAIL: subtract(3, 5) returns 8 instead of -2."""
        assert calc.subtract(3, 5) == -2

    def test_subtract_floats(self, calc):
        """This will FAIL: subtract(5.5, 2.5) returns 8.0 instead of 3.0."""
        assert calc.subtract(5.5, 2.5) == 3.0


# ── divide() tests — should FAIL on zero division ──────────────────────────


class TestDivide:
    def test_divide_normal(self, calc):
        assert calc.divide(10, 2) == 5.0

    def test_divide_float_result(self, calc):
        assert calc.divide(7, 2) == 3.5

    def test_divide_by_one(self, calc):
        assert calc.divide(5, 1) == 5.0

    def test_divide_by_zero(self, calc):
        """This will FAIL: should raise ValueError, but raises ZeroDivisionError."""
        with pytest.raises(ValueError, match="Cannot divide by zero"):
            calc.divide(10, 0)

    def test_divide_negative(self, calc):
        assert calc.divide(-10, 2) == -5.0


# ── multiply() tests — should all PASS ─────────────────────────────────────


class TestMultiply:
    def test_multiply_positive(self, calc):
        assert calc.multiply(3, 4) == 12

    def test_multiply_by_zero(self, calc):
        assert calc.multiply(5, 0) == 0

    def test_multiply_negative(self, calc):
        assert calc.multiply(-3, 4) == -12
