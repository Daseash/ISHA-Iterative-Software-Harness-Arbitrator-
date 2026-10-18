"""AR-5: strategy bandit over graded outcomes (reorders, never drops)."""

import pytest

from src.memory import store as ms
from src.agents.dispatch import STRATEGIES


@pytest.fixture()
def tmp_db(monkeypatch, tmp_path):
    monkeypatch.setenv("ISHA_MEMORY_DB", str(tmp_path / "memory.db"))
    return tmp_path


def _attempt_and_grade(iid, repo, strategy, resolved, path=None, tests_passed=True):
    assert ms.record_attempt(
        iid, repo, "issue " + iid, strategy, "m", "patch", 0.5, tests_passed, path=path
    )
    assert ms.resolve(iid, resolved, fail_bucket="", path=path) is True


def test_bandit_prefers_winning_strategy(tmp_db):
    path = tmp_db / "memory.db"
    for n in range(4):
        _attempt_and_grade(f"sympy__sympy-1000{n}", "", "minimal_diff", False, path=path)
    for n in range(2):
        _attempt_and_grade(f"sympy__sympy-2000{n}", "", "root_cause_first", True, path=path)
    order = ms.strategy_order("sympy__sympy-30000", "", epsilon=0.0, path=path)
    assert order[0] == "root_cause_first"
    assert order[-1] == "minimal_diff"
    assert sorted(order) == sorted(STRATEGIES)


def test_bandit_keeps_all_strategies_under_exploration(tmp_db):
    path = tmp_db / "memory.db"
    order = ms.strategy_order("sympy__sympy-1", "", epsilon=1.0, path=path)
    assert sorted(order) == sorted(STRATEGIES)


def test_bandit_empty_db_preserves_canonical_order(tmp_db):
    path = tmp_db / "memory.db"
    order = ms.strategy_order("sympy__sympy-2", "", epsilon=0.0, path=path)
    assert order == STRATEGIES


def test_bandit_ignores_ungraded_attempts(tmp_db):
    path = tmp_db / "memory.db"
    # Several attempts, none graded — must not distort the canonical order.
    for n in range(5):
        assert ms.record_attempt(
            "django__django-3000" + str(n),
            "",
            "issue for grading gap test",
            "call_site_aware",
            "m",
            "p",
            0.9,
            True,
            path=path,
        )
    order = ms.strategy_order("django__django-9", "", epsilon=0.0, path=path)
    assert order == STRATEGIES
