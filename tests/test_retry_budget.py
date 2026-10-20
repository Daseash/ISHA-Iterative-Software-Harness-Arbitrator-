"""Retry budget single-accounting: exactly +1 per failed cycle, owned by replan.

Regression: coder_node and replan_node BOTH incremented retry_count, so one
failed coder->sandbox->replan cycle burned 2 budget instead of 1 (MAX_RETRIES
exhausted after ~2 real retries, count overshooting past the cap).
"""

import src.agents.nodes as nodes
from src.agents.nodes import coder_node, replan_node
from src.agents.state import AgentState


def _failed_state(**kw):
    base = dict(
        issue_text="b",
        repo_path="/tmp",
        test_output="FAILED: assertion mismatch",
        local_sandbox_status="failed",
        retry_count=0,
    )
    base.update(kw)
    return AgentState(**base)


def test_coder_does_not_consume_budget(monkeypatch, tmp_path):
    (tmp_path / "calc.py").write_text("def mul(a, b):\n    return a * b\n")
    monkeypatch.setattr(nodes, "call_coder", lambda prompt: "diff")
    st = _failed_state(repo_path=str(tmp_path))
    out = coder_node(st)
    assert out.retry_count == 0


def test_replan_consumes_exactly_one():
    st = _failed_state()
    out = replan_node(st)
    assert out.retry_count == 1


def test_two_failed_cycles_cost_two_not_four(monkeypatch, tmp_path):
    (tmp_path / "calc.py").write_text("def mul(a, b):\n    return a * b\n")
    monkeypatch.setattr(nodes, "call_coder", lambda prompt: "diff")
    st = _failed_state(repo_path=str(tmp_path))
    for _ in range(2):  # coder -> sandbox(FAILED) -> replan, x2
        st = coder_node(st)
        st = replan_node(st)  # sandbox verdict stays FAILED between cycles
    assert st.retry_count == 2
