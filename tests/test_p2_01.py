"""P2-01: caller-graph signal in localizer fusion."""

from pathlib import Path

from src.tools.localizer import _caller_scores, parse_issue

DUMMY = str(Path(__file__).resolve().parent / "dummy_repo")


def test_caller_boost_finds_calling_files():
    seeds = parse_issue("Calculator.subtract returns a+b")
    assert "subtract" in seeds.symbols
    scores = _caller_scores(DUMMY, seeds)
    assert scores.get("test_calculator.py", 0.0) > 0.0


def test_no_seeds_no_signal():
    seeds = parse_issue("the thing is broken somehow")
    assert _caller_scores(DUMMY, seeds) == {}


def test_unknown_repo_safe():
    seeds = parse_issue("Calculator.subtract returns a+b")
    assert _caller_scores("/nonexistent/repo", seeds) == {}
