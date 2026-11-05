"""AR-4 #6: per-org calibrated thresholds live at the approval gate."""

import json

import pytest

from src.agents.state import AgentState
from src.approval import gate as approval_gate
from src.review import calibration as cal


@pytest.fixture()
def org_artifact(tmp_path, monkeypatch):
    path = tmp_path / "calibration_real.json"
    path.write_text(
        """{
  "per_org_90_precision": {
    "django": {"n": 10, "threshold": 0.93, "precision": 1.0},
    "matplotlib": {"n": 5, "threshold": 0.04, "precision": 1.0}
  }
}""",
        encoding="utf-8",
    )
    monkeypatch.setattr(cal, "REAL_ARTIFACT_PATH", path)
    return path


@pytest.fixture()
def approvals_file(tmp_path, monkeypatch):
    path = tmp_path / "approvals.jsonl"
    monkeypatch.setenv("ISHA_APPROVALS_FILE", str(path))
    monkeypatch.setattr(approval_gate, "APPROVALS_FILE", str(path))
    return path


def _approved_state(instance_id, prob):
    return AgentState(
        issue_text="Regression: wrong value on edge case",
        repo_path="repos/django",
        instance_id=instance_id,
        patch="--- a/f.py\n+++ b/f.py\n@@ -1 +1 @@\n-x\n+y\n",
        critic_verdict="approved",
        critic_score=0.9,
        laya_scores={"combined": prob},
        strategy="minimal_diff",
    )


def test_per_org_threshold_reads_artifact(org_artifact):
    assert cal.per_org_threshold("django") == 0.93
    assert cal.per_org_threshold("matplotlib") == 0.04
    assert cal.per_org_threshold("sympy") is None
    assert cal.per_org_threshold("") is None


def test_gate_blocks_low_prob_below_org_threshold(org_artifact, approvals_file, monkeypatch):
    monkeypatch.setenv("ISHA_PER_ORG_GATE", "1")
    st = _approved_state("django__django-12345", 0.50)
    out = approval_gate.approval_node(st, None)
    assert out.approved is None
    with open(approvals_file, encoding="utf-8") as fh:
        record = [json.loads(line) for line in fh if line.strip()][-1]
    assert record["per_org_gate"] == {"org": "django", "prob": 0.5, "threshold": 0.93}


def test_gate_auto_approves_above_org_threshold(org_artifact, approvals_file, monkeypatch):
    monkeypatch.setenv("ISHA_PER_ORG_GATE", "1")
    st = _approved_state("matplotlib__matplotlib-23456", 0.50)
    out = approval_gate.approval_node(st, None)
    assert out.approved is True


def test_gate_off_keeps_default_behavior(approvals_file, monkeypatch):
    monkeypatch.setenv("ISHA_PER_ORG_GATE", "0")
    st = _approved_state("django__django-12345", 0.10)
    out = approval_gate.approval_node(st, None)
    assert out.approved is True
