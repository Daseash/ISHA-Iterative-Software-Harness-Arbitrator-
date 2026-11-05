"""P0-10: dispatch isolation + attempt ledger."""

from src.agents.dispatch import STRATEGIES


def test_strategies_match_candidates():
    from src.agents.candidates import STRATEGY_VARIANTS

    valid = {name for name, _, _ in STRATEGY_VARIANTS}
    for s in STRATEGIES:
        assert s in valid, f"{s} has no variant (generic prompt)"
    assert "alt_test_phrasing" not in STRATEGIES
    assert len(set(STRATEGIES)) == 3


def test_dispatch_deepcopy_and_unique_worktrees(monkeypatch, tmp_path):
    import src.agents.dispatch as disp
    from src.agents.state import AgentState

    import src.tools.worktree_manager as wm

    monkeypatch.setattr(wm, "create_worktree", lambda repo, tag: f"/tmp/{tag}")

    st = AgentState(
        issue_text="bug",
        repo_path=str(tmp_path),
        instance_id="django__django-1",
        plan="p",
        escalation="stale?",
        context_notes=["n1"],
        localization=[{"f": "a"}],
    )
    sends = disp.dispatch_agents(st)
    assert len(sends) == 3
    nodes = sorted(s.node for s in sends)
    assert nodes == ["attempt1", "attempt2", "attempt3"]
    payloads = [s.arg for s in sends]
    assert sorted(p["strategy"] for p in payloads) == sorted(STRATEGIES)
    # Unique worktrees per branch
    assert len({p["worktree"] for p in payloads}) == 3
    # Stale escalation cleared, nested lists deep-copied (not shared)
    assert all(p["escalation"] == "" for p in payloads)
    assert payloads[0]["context_notes"] == ["n1"]
    payloads[0]["context_notes"].append("mut")
    assert payloads[1]["context_notes"] == ["n1"]
    # Fallback: re-derive via direct call inspection is complex; assert strategies distinct
    assert STRATEGIES == ["minimal_diff", "call_site_aware", "root_cause_first"]


def test_attempt_records_ledger(monkeypatch):
    from src.agents import attempt as att
    from src.agents.state import AgentState
    from src.review import arbitration as arb

    monkeypatch.setattr(att, "coder_node", lambda s: s)
    monkeypatch.setattr(att, "sandbox_node", lambda s: s)
    monkeypatch.setattr(att, "critic_node", lambda s, c=None: s)
    arb.collect_attempts("t-p010-3")  # drain leftovers
    for strat in ("minimal_diff", "call_site_aware", "root_cause_first"):
        st = AgentState(issue_text="b", repo_path="/tmp", strategy=strat)
        out = att.attempt_node(st, config={"configurable": {"thread_id": "t-p010-3"}})
        assert isinstance(out, dict)
    rows = arb.collect_attempts("t-p010-3")
    assert len(rows) == 3
    assert sorted(r["strategy"] for r in rows) == ["call_site_aware", "minimal_diff", "root_cause_first"]
