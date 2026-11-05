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


def test_baseline_red_gate_node_distinguishes_failures(monkeypatch, tmp_path):
    """Verify baseline_red_gate_node correctly identifies failing tests vs collection errors."""
    from src.agents.nodes import baseline_red_gate_node

    dummy_repo = tmp_path / "repo"
    dummy_repo.mkdir()

    # Case 1: Real failing assertion (RED)
    monkeypatch.setattr("src.agents.nodes.make_sandbox", lambda r: str(r))
    monkeypatch.setattr("src.agents.nodes.cleanup_sandbox", lambda s: None)
    monkeypatch.setattr("src.agents.nodes.run_tests", lambda s, test_file=None: "FAILED test_repro.py::test_repro - AssertionError\n1 failed, 0 passed in 0.12s")

    state = AgentState(
        issue_text="repro bug",
        repo_path=str(dummy_repo),
        regression_test="def test_repro(): assert False",
    )
    result = baseline_red_gate_node(state)
    assert result.repro_ok is True
    assert result.baseline_repro_failed is True
    assert "1 failed" in result.repro_output

    # Case 2: Collection / Import error (NOT a genuine RED test)
    monkeypatch.setattr("src.agents.nodes.run_tests", lambda s, test_file=None: "ERROR collecting test_repro.py\nModuleNotFoundError: No module named 'invalid_pkg'\n1 error in 0.05s")
    state2 = AgentState(
        issue_text="repro bug",
        repo_path=str(dummy_repo),
        regression_test="import invalid_pkg\ndef test_repro(): pass",
    )
    result2 = baseline_red_gate_node(state2)
    assert result2.repro_ok is False
    assert result2.baseline_repro_failed is False
    assert any("Baseline repro gate notice" in note for note in result2.context_notes)

    # Case 3: Strict mode escalation
    monkeypatch.setenv("ISHA_STRICT_BASELINE", "1")
    result3 = baseline_red_gate_node(state2)
    assert result3.repro_ok is False
    assert "Generated repro did not produce a clean failing test" in result3.escalation

