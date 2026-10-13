"""Tests for baseline-test gate, failure classification, replanning, and explicit completion reporting."""

import pytest
from src.agents.state import AgentState
from src.agents.nodes import classify_failure, replan_node
from src.review.completion_report import format_completion_report


def test_classify_failure_categories():
    """Verify failure modes are classified accurately from test output."""
    assert classify_failure("SyntaxError: invalid syntax at line 4") == "SYNTAX_INDENTATION"
    assert classify_failure("TypeError: function takes 2 positional arguments but 3 were given") == "SIGNATURE_MISMATCH"
    assert classify_failure("TypeError: object of type 'NoneType' has no len()") == "TYPE_ERROR_NONE"
    assert classify_failure("TypeError: unhashable type: 'list'") == "HASHABILITY_CONTRACT"
    assert classify_failure("AssertionError: assert 'a' == 'b'") == "ASSERTION_MISMATCH"
    assert classify_failure("ModuleNotFoundError: No module named 'custom_pkg'") == "IMPORT_ERROR"
    assert classify_failure("pytest: tests timed out after 30s") == "TIMEOUT_REGRESSION"
    assert classify_failure("random error without keyword") == "BEHAVIORAL_FAIL"


def test_replan_node_updates_plan_with_evidence():
    """Verify replan_node classifies the failure and appends diagnostic evidence to the plan."""
    initial_plan = "Step 1: Fix the helper function."
    state = AgentState(
        issue_text="TypeError: object of type 'NoneType' has no len()",
        plan=initial_plan,
        test_output="FAILED test_x.py - TypeError: object of type 'NoneType' has no len()",
        retry_count=0,
    )

    updated = replan_node(state)
    assert updated.retry_count == 1
    assert updated.failure_classification == "TYPE_ERROR_NONE"
    assert "EVIDENCE-BASED RE-PLANNING" in updated.plan
    assert "GUARD CLAUSE" in updated.plan
    assert "TypeError: object of type 'NoneType' has no len()" in updated.plan


def test_completion_report_honest_distinction():
    """Verify completion report explicitly reports patch, files, tests run, and distinguishes local from Docker."""
    diff = "diff --git a/app.py b/app.py\n--- a/app.py\n+++ b/app.py\n@@ -1 +1 @@\n-old\n+new\n"
    state = AgentState(
        issue_text="fix a bug",
        repo_path="/test/repo",
        instance_id="django__django-12345",
        patch=diff,
        baseline_repro_failed=True,
        local_sandbox_status="passed",
        official_docker_status="not_run",
        test_output="1 passed in 0.02s",
        critic_score=0.92,
        critic_verdict="approved",
    )

    report = format_completion_report(state)
    assert "ISHA EXPLICIT COMPLETION REPORT" in report
    assert "BASELINE REPRO GATE  : ✅ CONFIRMED RED" in report
    assert "LOCAL SANDBOX TEST   : PASSED (Host/Simulated sandbox execution)" in report
    assert "OFFICIAL DOCKER TEST : NOT_RUN (Isolated SWE-bench container execution)" in report
    assert "app.py" in report
    assert "+1, -1 lines" in report
