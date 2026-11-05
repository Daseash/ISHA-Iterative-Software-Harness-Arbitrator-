"""P0-13: arbitration fallback + verdict merge + approval pending."""

from src.review import arbitration as arb


def test_laya_down_deterministic(monkeypatch):
    monkeypatch.setattr(arb, "get_judge", lambda: (_ for _ in ()).throw(RuntimeError("down")))
    rows = [
        {"test_output": "PASSED", "critic_score": 0.3, "retry_count": 0, "strategy": "a"},
        {"test_output": "PASSED", "critic_score": 0.9, "retry_count": 0, "strategy": "b"},
    ]
    w = arb.arbitration_node(rows)
    assert w["strategy"] == "b"


def test_approval_pending_logged(monkeypatch, tmp_path):
    import src.approval.gate as gate
    from src.agents.state import AgentState

    monkeypatch.setattr(gate, "APPROVALS_FILE", str(tmp_path / "appr.jsonl"))
    st = AgentState(issue_text="b", patch="diff", critic_verdict="flagged", critic_score=0.1)
    out = gate.approval_node(st, config={"configurable": {"approval_mode": "auto"}})
    assert out.approved is None
    recs = gate.recent_approvals()
    assert recs and recs[0]["decision"] == "pending"
