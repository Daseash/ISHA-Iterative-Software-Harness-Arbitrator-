"""
Unit tests for ISHA Advanced Repository Understanding & v2 Capabilities:
1. Dependency Graph & Impact Analysis (AST-based call graph, import graph, blast radius).
2. Hierarchical Bug Decomposition (Decomposer node & sub-issues).
3. Checkpointed, Resumable Sessions & Progress Ledger.
4. Active Pre-Planning Investigation (Baseline tests, grep, full-file inspection).
5. Cross-File Consistency & Collateral Regression Validation.
"""

import json
from pathlib import Path
import pytest

from src.agents.decomposer import SubIssue, decompose_issue, decomposer_node
from src.agents.investigation import (
    grep_codebase,
    investigate_repository,
    investigation_node,
    load_suspect_files,
    run_baseline_tests,
)
from src.agents.session_manager import (
    list_sessions,
    load_session,
    resume_session_state,
    save_session,
)
from src.agents.state import AgentState
from src.tools.consistency_checker import (
    check_patch_consistency,
    extract_modified_signatures,
)
from src.tools.dependency_graph import DependencyGraph, ImpactAnalysis

DUMMY_REPO = "tests/dummy_repo"


# ── 1. Dependency Graph & Impact Analysis ─────────────────────────────────────

def test_dependency_graph_extracts_definitions_and_calls():
    dg = DependencyGraph(DUMMY_REPO)
    assert len(dg.definitions) > 0

    sym_names = [s.name for s in dg.definitions]
    assert "Calculator" in sym_names
    assert "add" in sym_names
    assert "subtract" in sym_names
    assert "divide" in sym_names

    # Check reverse call graph connects test methods to calculator methods
    callers = dg.reverse_call_graph.get("subtract", set())
    assert any("test_subtract" in c for c in callers)


def test_impact_analysis_calculates_blast_radius():
    dg = DependencyGraph(DUMMY_REPO)
    impact = dg.analyze_impact(["subtract"])

    assert isinstance(impact, ImpactAnalysis)
    assert len(impact.directly_impacted_symbols) >= 1
    assert "test_calculator.py" in impact.impacted_test_files
    assert impact.blast_radius_score > 0.0

    report = dg.render_impact_report(impact)
    assert "Repository Dependency & Impact Analysis" in report
    assert "subtract" in report


# ── 2. Hierarchical Bug Decomposition ────────────────────────────────────────

def test_decomposer_offline_fallback():
    issue = "Fix subtract operator and add zero guard in divide"
    sub_issues = decompose_issue(issue, "repo context", "investigation report")
    assert len(sub_issues) >= 1
    assert isinstance(sub_issues[0], SubIssue)


def test_decomposer_node_populates_state():
    state = AgentState(
        issue_text="Single bug: return a + b instead of a - b in subtract",
        repo_path=DUMMY_REPO,
    )
    new_state = decomposer_node(state)
    assert len(new_state.sub_issues) >= 1
    assert new_state.current_sub_issue_index == 0
    assert new_state.sub_issues[0]["status"] == "in_progress"


# ── 3. Checkpointed, Resumable Sessions & Progress Ledger ────────────────────

def test_session_save_and_resume(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "src.agents.session_manager._sessions_dir",
        lambda: tmp_path,
    )

    state = AgentState(
        session_id="test_sess_001",
        issue_text="subtract returns sum",
        repo_path=DUMMY_REPO,
        patch="--- a/calculator.py\n+++ b/calculator.py\n@@ -20,1 +20,1 @@\n- return a + b\n+ return a - b\n",
        critic_verdict="approved",
        critic_score=0.92,
    )

    sid = save_session(state, status="in_progress")
    assert sid == "test_sess_001"

    data = load_session(sid)
    assert data is not None
    assert data["session_id"] == "test_sess_001"
    assert data["critic_score"] == 0.92
    assert len(data["accumulated_patches"]) == 1

    resumed_state = resume_session_state(sid, human_approved=True)
    assert resumed_state is not None
    assert resumed_state.approved is True
    assert resumed_state.session_id == "test_sess_001"


# ── 4. Active Investigation Phase ─────────────────────────────────────────────

def test_investigation_helpers():
    # Grep codebase
    hits = grep_codebase(DUMMY_REPO, ["subtract", "Calculator"])
    assert len(hits) > 0
    assert any(h["pattern"] == "subtract" for h in hits)

    # Suspect files
    files = load_suspect_files(DUMMY_REPO, ["calculator.py"])
    assert "calculator.py" in files
    assert "class Calculator" in files["calculator.py"]


def test_investigation_node_populates_report():
    state = AgentState(
        issue_text="The subtract method in calculator.py returns a+b instead of a-b",
        repo_path=DUMMY_REPO,
    )
    new_state = investigation_node(state)
    assert "Pre-Planning Investigation Report" in new_state.investigation_report
    assert "Baseline Test Execution" in new_state.investigation_report
    assert "calculator.py" in new_state.investigation_report


# ── 5. Multi-File Consistency Checks ──────────────────────────────────────────

def test_consistency_checker_flags_unpatched_callers():
    # Patch renames subtract -> subtract_v2 in calculator.py without updating test_calculator.py
    breaking_patch = """--- a/calculator.py
+++ b/calculator.py
@@ -17,2 +17,2 @@
-    def subtract(self, a: float, b: float) -> float:
+    def subtract_v2(self, a: float, b: float) -> float:
         return a - b
"""
    dg = DependencyGraph(DUMMY_REPO)
    warnings = check_patch_consistency(DUMMY_REPO, breaking_patch, dg)
    assert len(warnings) > 0
    assert any("test_calculator.py" in w for w in warnings)


def test_consistency_checker_clears_consistent_patch():
    # Patch only modifies internal logic, not function signature
    clean_patch = """--- a/calculator.py
+++ b/calculator.py
@@ -22,1 +22,1 @@
-        return a + b
+        return a - b
"""
    dg = DependencyGraph(DUMMY_REPO)
    warnings = check_patch_consistency(DUMMY_REPO, clean_patch, dg)
    assert len(warnings) == 0
