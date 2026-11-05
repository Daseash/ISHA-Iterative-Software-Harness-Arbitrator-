"""Veto: near-identical query to a graded failure returns NEVER-DO."""

from src.agents.state import AgentState


def test_veto_fires_on_identical_failed_issue(monkeypatch, tmp_path):
    import src.agents.fix_history as fh
    from src.memory import store as mem

    monkeypatch.setenv("ISHA_MEMORY_DB", str(tmp_path / "m.db"))
    monkeypatch.setattr(fh, "_ledger_path", lambda: tmp_path / "fh.jsonl")

    issue = "ValueError identical failure case for veto check"
    st = AgentState(
        issue_text=issue,
        repo_path="repos/django",
        instance_id="django__django-9001",
        plan="try X",
        patch="--- a/f.py\n+++ b/f.py\n@@ -1 +1 @@\n-x\n+y\n",
        critic_verdict="approved",
        critic_score=0.8,
        test_output="FAILED",
        strategy="minimal_diff",
    )
    assert fh.record_fix(st) is True
    assert mem.resolve("django__django-9001", False, "tests_failed") is True

    hits = fh.retrieve_fixes(issue, "repos/django")
    vetoes = [h for h in hits if h.get("verdict") == "NEVER-DO"]
    assert len(vetoes) == 1
    assert "9001" in vetoes[0]["issue"]


def test_no_veto_when_resolved(monkeypatch, tmp_path):
    import src.agents.fix_history as fh
    from src.memory import store as mem

    monkeypatch.setenv("ISHA_MEMORY_DB", str(tmp_path / "m.db"))
    monkeypatch.setattr(fh, "_ledger_path", lambda: tmp_path / "fh.jsonl")

    issue = "totally different success case here"
    st = AgentState(
        issue_text=issue,
        repo_path="repos/django",
        instance_id="django__django-9002",
        plan="try Y",
        patch="--- a/g.py\n+++ b/g.py\n@@ -1 +1 @@\n-p\n+q\n",
        critic_verdict="approved",
        critic_score=0.9,
        test_output="PASSED",
        strategy="minimal_diff",
    )
    assert fh.record_fix(st) is True
    assert mem.resolve("django__django-9002", True, "") is True

    hits = fh.retrieve_fixes(issue, "repos/django")
    assert not [h for h in hits if h.get("verdict") == "NEVER-DO"]
