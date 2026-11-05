"""AR-2: structured routing — local_sandbox_status wins over substrings.

Accept: a crafted PASSED verdict whose output embeds traceback/FAILED text
routes to critic (never replan), and a FAILED verdict embedding per-test
PASSED lines never clears the merger apply gate.
"""

from unittest.mock import patch as _patch

from src.agents.graph import _route_after_sandbox, merger_node
from src.agents.nodes import _verdict
from src.agents.state import AgentState
from src.agents.state import test_failed as sandbox_failed
from src.agents.state import test_passed as sandbox_passed


def _state(**kw):
    base = dict(issue_text="b", repo_path="/tmp")
    base.update(kw)
    return AgentState(**base)


def test_zero_failed_is_not_failed():
    assert _verdict("2 passed, 0 failed in 1.23s") == "PASSED"
    assert _verdict("1 failed, 2 passed in 0.9s") == "FAILED"
    assert _verdict("3 passed in 0.4s") == "PASSED"


def test_passed_with_traceback_text_routes_to_critic():
    st = _state(
        test_output=(
            "PASSED\n1 passed, 0 failed\n"
            "warnings summary:\n"
            "FAILED test_old_flaky.py::test_x - previous run artifact\n"
            "Traceback (most recent call last):\n"
            '  File "x.py", line 1, in <module>\n'
            "DeprecationWarning: legacy shim"
        ),
        local_sandbox_status="passed",
        retry_count=0,
    )
    assert sandbox_failed(st) is False
    assert sandbox_passed(st) is True
    assert _route_after_sandbox(st) == "critic"


def test_failed_status_routes_to_replan_then_critic():
    st = _state(test_output="FAILED", local_sandbox_status="failed", retry_count=0)
    assert _route_after_sandbox(st) == "replan"
    st.retry_count = 99
    assert _route_after_sandbox(st) == "critic"


def test_legacy_not_run_falls_back_to_substring():
    st = _state(test_output="FAILED: no patch to apply", retry_count=0)
    assert st.local_sandbox_status == "not_run"
    assert sandbox_failed(st) is True
    assert _route_after_sandbox(st) == "replan"
    st2 = _state(test_output="PASSED", retry_count=0)
    assert sandbox_passed(st2) is True
    assert _route_after_sandbox(st2) == "critic"


def test_merger_fail_open_closed():
    """Collateral FAILED output with per-test PASSED lines must not apply."""
    st = _state(
        patch="diff --git a/x b/x",
        test_output=(
            "FAILED: Collateral regression detected!\n"
            "- test_new\n\nFull pytest output:\n"
            "test_keep PASSED\ntest_new FAILED"
        ),
        local_sandbox_status="failed",
        critic_verdict="approved",
        critic_score=0.9,
        strategy="minimal_diff",
    )
    assert sandbox_passed(st) is False
    with _patch("src.tools.patch_engine.apply_patch") as m:
        m.return_value = (False, "mocked")
        merger_node(st, config={"configurable": {"thread_id": "t-ar02-a", "apply": True}})
        m.assert_not_called()


def test_merger_applies_on_structured_pass():
    st = _state(
        patch="diff --git a/x b/x",
        test_output="PASSED",
        local_sandbox_status="passed",
        critic_verdict="approved",
        critic_score=0.9,
        strategy="minimal_diff",
    )
    with _patch("src.tools.patch_engine.apply_patch") as m:
        m.return_value = (False, "mocked")
        merger_node(st, config={"configurable": {"thread_id": "t-ar02-b", "apply": True}})
        m.assert_called_once()
