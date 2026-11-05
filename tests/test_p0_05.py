"""P0-05: resolved writeback (Write-A NULL, Write-B non-NULL)."""

from src.agents.state import AgentState


def test_p0_05_write_a_then_write_b(monkeypatch, tmp_path):
    import src.agents.fix_history as fh
    from src.memory import store as mem

    monkeypatch.setenv("ISHA_MEMORY_DB", str(tmp_path / "memory.db"))
    monkeypatch.setattr(fh, "_ledger_path", lambda: tmp_path / "fix_history.jsonl")

    # Write-A x5
    for i in range(5):
        st = AgentState(
            issue_text=f"bug {i} traceback ValueError frame f{i}",
            repo_path="repos/django",
            instance_id=f"django__django-1000{i}",
            plan="fix it",
            patch=f"--- a/f{i}.py\n+++ b/f{i}.py\n@@ -1 +1 @@\n-x\n+y{i}\n",
            critic_verdict="approved",
            critic_score=0.8,
            test_output="PASSED",
            strategy="minimal_diff",
        )
        assert fh.record_fix(st) is True

    # All 5 rows exist with resolved NULL (Write-A)
    for i in range(5):
        row = mem.fetch(f"django__django-1000{i}")
        assert row is not None
        assert row["resolved"] is None

    # Write-B: Docker truth
    for i in range(3):
        assert mem.resolve(f"django__django-1000{i}", True, "tests_failed") is True
    for i in range(3, 5):
        assert mem.resolve(f"django__django-1000{i}", False, "tests_failed") is True

    # Acceptance: 5 rows with non-NULL resolved
    non_null = 0
    for i in range(5):
        row = mem.fetch(f"django__django-1000{i}")
        assert row is not None and row["resolved"] in (0, 1)
        non_null += 1
    assert non_null == 5
