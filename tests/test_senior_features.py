"""Tests for the senior-dev instinct features (F1-F7)."""

import os
import subprocess
from pathlib import Path

import pytest

from src.agents.state import AgentState
from src.agents.graph import (
    _route_after_confidence_gate,
    approval_node,
    compiled_graph,
)
from src.agents.investigation import investigate_repository
from src.review.checklist import security_perf_checklist
from src.tools.git_history import file_history, mentioned_files
from src.tools.style_reference import style_examples

# ── F1: git history reasoning ───────────────────────────────────────────────


def _git(cwd: Path, *args: str) -> None:
    subprocess.run(
        ["git", *args],
        cwd=str(cwd),
        capture_output=True,
        check=False,
        env=os.environ.copy(),
    )


def _make_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init")
    _git(repo, "config", "user.email", "t@example.com")
    _git(repo, "config", "user.name", "t")
    (repo / "calc.py").write_text("def add(a, b):\n    return a + b\n", encoding="utf-8")
    _git(repo, "add", "calc.py")
    _git(repo, "commit", "-m", "fix add edge case")
    (repo / "calc.py").write_text("def add(a, b):\n    return a + b\n\ndef mul(a, b):\n    return a * b\n", encoding="utf-8")
    _git(repo, "add", "calc.py")
    _git(repo, "commit", "-m", "introduce mul")
    return repo


def test_mentioned_files_extracts_paths_in_order():
    text = "Patch `pkg/mod.py` and also other.py plus pkg/mod.py again"
    assert mentioned_files(text) == ["pkg/mod.py", "other.py"]


def test_mentioned_files_empty_text():
    assert mentioned_files("") == []


def test_file_history_returns_commit_messages(tmp_path):
    repo = _make_repo(tmp_path)
    out = file_history(str(repo), ["calc.py"])
    assert "fix add edge case" in out
    assert "introduce mul" in out


def test_file_history_missing_repo_is_silent(tmp_path):
    assert file_history(str(tmp_path / "nope"), ["x.py"]) == ""
    assert file_history("", ["x.py"]) == ""
    assert file_history(str(tmp_path), ["x.py"]) == ""


# ── F2: confidence gate ─────────────────────────────────────────────────────


def test_planner_parses_confidence_and_strips_line(monkeypatch, tmp_path):
    import src.agents.nodes as nodes

    monkeypatch.setattr(
        nodes,
        "call_planner",
        lambda prompt: "Step 1: root cause\nStep 2: fix\nCONFIDENCE: 0.25",
    )
    state = AgentState(issue_text="bug", repo_path=str(tmp_path))
    state = nodes.planner_node(state)
    assert state.planner_confidence == 0.25
    assert "CONFIDENCE" not in state.plan


def test_planner_unknown_confidence_is_minus_one(monkeypatch, tmp_path):
    import src.agents.nodes as nodes

    monkeypatch.setattr(nodes, "call_planner", lambda prompt: "Step 1: x\nStep 2: y")
    state = AgentState(issue_text="bug", repo_path=str(tmp_path))
    state = nodes.planner_node(state)
    assert state.planner_confidence == -1.0


def test_confidence_gate_escalates_below_threshold(monkeypatch, tmp_path):
    import src.agents.nodes as nodes

    monkeypatch.setenv("ISHA_CONFIDENCE_THRESHOLD", "0.4")
    state = AgentState(issue_text="bug", repo_path=str(tmp_path), planner_confidence=0.2)
    state = nodes.confidence_gate_node(state)
    assert "low planner confidence" in state.escalation


def test_confidence_gate_passes_high_or_unknown(monkeypatch, tmp_path):
    import src.agents.nodes as nodes

    monkeypatch.setenv("ISHA_CONFIDENCE_THRESHOLD", "0.4")
    for confidence in (0.9, -1.0):
        state = AgentState(issue_text="bug", repo_path=str(tmp_path), planner_confidence=confidence)
        state = nodes.confidence_gate_node(state)
        assert state.escalation == ""


def test_confidence_gate_router():
    low = AgentState(issue_text="b", escalation="low planner confidence 0.20")
    clear = AgentState(issue_text="b")
    assert _route_after_confidence_gate(low) == "approval"
    assert _route_after_confidence_gate(clear) == "regression_test"


def test_approval_escalates_low_confidence(tmp_path, monkeypatch):
    import src.approval.gate as gate

    monkeypatch.setattr(gate, "APPROVALS_FILE", str(tmp_path / "approvals.jsonl"))
    state = AgentState(issue_text="b", escalation="low planner confidence 0.30 < 0.40")
    result = approval_node(state, config={"configurable": {}})
    assert result.approved is False
    assert "low planner confidence" in state.escalation


# ── F3: blast radius ────────────────────────────────────────────────────────


def test_investigation_computes_blast_radius_meta():
    repo = str(Path(__file__).parent / "dummy_repo")
    meta: dict = {}
    report = investigate_repository(repo, "subtract method returns wrong sum", meta=meta)
    assert isinstance(report, str)
    assert "blast_radius" in meta
    assert {"score", "callers", "files"} <= set(meta["blast_radius"])


def test_high_blast_radius_forces_human_review(tmp_path, monkeypatch):
    import src.approval.gate as gate

    monkeypatch.setattr(gate, "APPROVALS_FILE", str(tmp_path / "approvals.jsonl"))
    monkeypatch.setenv("ISHA_BLAST_REVIEW_SCORE", "0.4")
    monkeypatch.setenv("ISHA_BLAST_REVIEW_CALLERS", "150")
    state = AgentState(
        issue_text="b",
        patch="--- a/x.py\n+++ b/x.py\n@@ -1 +1 @@\n-old\n+new\n",
        critic_verdict="approved",
        critic_score=0.9,
        blast_radius={"score": 0.9, "callers": 300},
    )
    result = approval_node(state, config={"configurable": {}})
    assert result.approved is False


def test_low_blast_radius_auto_approves(tmp_path, monkeypatch):
    import src.approval.gate as gate

    monkeypatch.setattr(gate, "APPROVALS_FILE", str(tmp_path / "approvals.jsonl"))
    state = AgentState(
        issue_text="b",
        patch="--- a/x.py\n+++ b/x.py\n@@ -1 +1 @@\n-old\n+new\n",
        critic_verdict="approved",
        critic_score=0.9,
        blast_radius={"score": 0.05, "callers": 3},
    )
    result = approval_node(state, config={"configurable": {}})
    assert result.approved is True


def test_graph_wires_confidence_gate():
    nodes = set(compiled_graph.get_graph().nodes.keys())
    assert "confidence_gate" in nodes


# ── F4 + F5: edge-case tests and style matching (prompt contracts) ─────────


def test_regression_prompt_requests_edge_cases(monkeypatch, tmp_path):
    import src.agents.nodes as nodes

    captured = {}
    monkeypatch.setattr(nodes, "call_planner", lambda prompt: captured.update(prompt=prompt) or "pass")
    state = AgentState(issue_text="bug", repo_path=str(tmp_path))
    nodes.regression_test_node(state)
    assert "edge-case tests" in captured["prompt"]


def test_coder_prompt_includes_history_and_style(monkeypatch, tmp_path):
    import src.agents.nodes as nodes

    repo = _make_repo(tmp_path)
    captured = {}
    monkeypatch.setattr(nodes, "call_coder", lambda prompt: captured.update(prompt=prompt) or "--- a/calc.py\n+++ b/calc.py\n")
    state = AgentState(
        issue_text="mul wrong for negatives",
        repo_path=str(repo),
        plan="Fix mul in calc.py to handle negatives",
    )
    nodes.coder_node(state)
    prompt = captured["prompt"]
    assert "GIT HISTORY" in prompt
    assert "CODE STYLE REFERENCE" in prompt
    assert "def mul" in prompt  # style example pulled from the target file


def test_style_examples_prefers_mentioned_definition(tmp_path):
    repo = tmp_path / "r"
    repo.mkdir()
    (repo / "m.py").write_text(
        "def alpha():\n    pass\n\ndef beta():\n    pass\n", encoding="utf-8"
    )
    out = style_examples(str(repo), "change beta in m.py")
    assert "def beta" in out


def test_style_examples_unknown_file_returns_empty(tmp_path):
    assert style_examples(str(tmp_path), "nothing here") == ""


# ── F6: critic security/performance checklist ───────────────────────────────


def test_checklist_parses_pass(monkeypatch):
    import src.config as config

    monkeypatch.setattr(config, "LLM_ENABLED", True)
    monkeypatch.setattr(
        config, "call_planner", lambda prompt: "SECURITY: PASS\nPERFORMANCE: PASS\nVERDICT: PASS"
    )
    result = security_perf_checklist("bug", "--- a/x\n+++ b/x\n")
    assert result == {"verdict": "PASS", "review": "SECURITY: PASS\nPERFORMANCE: PASS\nVERDICT: PASS"}


def test_checklist_blocks_dangerous_patch(monkeypatch):
    import src.config as config

    monkeypatch.setattr(config, "LLM_ENABLED", True)
    monkeypatch.setattr(config, "call_planner", lambda prompt: "SECURITY: FAIL shell=True\nVERDICT: BLOCK")
    result = security_perf_checklist("bug", "--- a/x\n+++ b/x\n")
    assert result["verdict"] == "BLOCK"


def test_checklist_unparseable_returns_none(monkeypatch):
    import src.config as config

    monkeypatch.setattr(config, "LLM_ENABLED", True)
    monkeypatch.setattr(config, "call_planner", lambda prompt: "no verdict line here")
    assert security_perf_checklist("bug", "diff") is None


# ── F7: fix history ─────────────────────────────────────────────────────────


def test_fix_history_roundtrip_and_repo_filter(monkeypatch, tmp_path):
    import src.agents.fix_history as fh

    monkeypatch.setattr(fh, "_ledger_path", lambda: tmp_path / "fix_history.jsonl")
    state = AgentState(
        issue_text="separability matrix wrong for nested models",
        repo_path="repos/astropy",
        plan="fix _separable",
        patch="--- a/s.py\n+++ b/s.py\n@@ -1 +1 @@\n-x\n+y\n",
        critic_verdict="approved",
        critic_score=0.85,
        test_output="PASSED",
    )
    assert fh.record_fix(state) is True
    # Sessions save repeatedly — identical issue+patch must not duplicate.
    assert fh.record_fix(state) is False

    hits = fh.retrieve_fixes("nested CompoundModel separability broken", "repos/astropy")
    assert len(hits) == 1
    assert hits[0]["verdict"] == "approved"
    assert hits[0]["similarity"] > 0.2

    # Different repo sees nothing.
    assert fh.retrieve_fixes("separability", "repos/django") == []

    rendered = fh.render_hits(hits)
    assert "separability matrix" in rendered
    assert "--- a/s.py" in rendered


def test_fix_history_ignores_error_patches(monkeypatch, tmp_path):
    import src.agents.fix_history as fh

    monkeypatch.setattr(fh, "_ledger_path", lambda: tmp_path / "fix_history.jsonl")
    state = AgentState(
        issue_text="b",
        repo_path="r",
        patch="[CODER ERROR] offline coder exhausted",
    )
    assert fh.record_fix(state) is False
