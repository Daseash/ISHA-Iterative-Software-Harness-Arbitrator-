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


# ── Phase-0 model-axis bandit ──────────────────────────────────────────────


def _grade_model(iid, strategy, model, resolved, path=None):
    assert ms.record_attempt(iid, "", "issue " + iid, strategy, model, "p", 0.6, True, path=path)
    assert ms.resolve(iid, resolved, path=path)


def test_model_pick_returns_better_model(tmp_db):
    path = tmp_db / "memory.db"
    # 4 graded attempts on one model: 3 wins. Default has no history (1/2).
    strong = "gemini/gemini-3.8-flash"
    for n in range(4):
        _grade_model(f"sympy__sympy-7000{n}", "minimal_diff", strong, n < 3, path=path)
    pick = ms.model_pick(
        "sympy__sympy-9999", "", "minimal_diff", "gemini-3.5-flash-lite", epsilon=0.0, path=path
    )
    assert pick == strong


def test_model_pick_keeps_default_when_thin(tmp_db):
    path = tmp_db / "memory.db"
    for n in range(3):  # below min_graded=4
        _grade_model(f"sympy__sympy-7100{n}", "minimal_diff", "gemini/gemini-3.8-flash", True, path=path)
    pick = ms.model_pick("sympy__sympy-9999", "", "minimal_diff", "gemini-3.5-flash-lite", path=path)
    assert pick == ""


def test_model_pick_keeps_default_when_default_wins(tmp_db):
    path = tmp_db / "memory.db"
    default = "gemini/gemini-3.5-flash-lite"
    for n in range(3):
        _grade_model(f"sympy__sympy-7200{n}", "minimal_diff", default, True, path=path)
    other = "gemini/other-model"
    for n in range(2):
        _grade_model(f"sympy__sympy-7300{n}", "minimal_diff", other, False, path=path)
    pick = ms.model_pick(
        "sympy__sympy-9999", "", "minimal_diff", default, epsilon=0.0, path=path
    )
    assert pick == ""


def test_model_pick_resolver_matches_provider_prefixes(tmp_db):
    path = tmp_db / "memory.db"
    _grade_model("sympy__sympy-7400", "root_cause_first", "gemini/-a", True, path=path)
    _grade_model("sympy__sympy-7401", "root_cause_first", "gemini/-a", True, path=path)
    _grade_model("sympy__sympy-7402", "root_cause_first", "gemini/-a", True, path=path)
    _grade_model("sympy__sympy-7403", "root_cause_first", "gemini/-a", True, path=path)
    assert ms.model_pick("sympy__sympy-9999", "", "root_cause_first", "irrelevant", path=path) == "gemini/-a"


# ── Phase-0 per-org critic threshold ───────────────────────────────────────


def test_org_critic_threshold_balanced_cut(tmp_db, monkeypatch):
    path = tmp_db / "memory.db"
    monkeypatch.setenv("ISHA_CRITIC_PER_ORG", "1")
    for n, (score, res) in enumerate(
        [(0.9, True), (0.85, True), (0.8, True), (0.3, False), (0.2, False), (0.1, False), (0.05, False), (0.02, False)]
    ):
        ms.record_attempt(f"sympy__sympy-8100{n}", "", "issue", "minimal_diff", "m", "p", score, True, path=path)
        ms.resolve(f"sympy__sympy-8100{n}", res, path=path)
    thr = ms.org_critic_threshold("sympy__sympy-9999", "", path=path)
    assert thr is not None and 0.2 <= thr <= 0.55


def test_org_critic_threshold_gate_off_by_default(tmp_db):
    path = tmp_db / "memory.db"
    thr = ms.org_critic_threshold("sympy__sympy-9999", "", path=path)
    assert thr is None


def test_org_critic_threshold_needs_both_classes(tmp_db, monkeypatch):
    path = tmp_db / "memory.db"
    monkeypatch.setenv("ISHA_CRITIC_PER_ORG", "1")
    for n in range(5):
        ms.record_attempt(f"sympy__sympy-8200{n}", "", "issue", "minimal_diff", "m", "p", 0.5, True, path=path)
        ms.resolve(f"sympy__sympy-8200{n}", True, path=path)
    assert ms.org_critic_threshold("sympy__sympy-9999", "", path=path) is None
