"""P0-06: semantic embed path + word-boundary seeds + org/cross-org transfer."""

from src.rag.indexer import VECTOR_SIZE, embed_text


def test_embed_is_384d_and_cached():
    v1 = embed_text("django ValueError frame fix")
    v2 = embed_text("django ValueError frame fix")
    assert len(v1) == VECTOR_SIZE == 384
    assert v1 == v2


def test_seed_word_boundary_no_single_char_match():
    from src.tools.localizer import _seed_score, IssueSeeds

    seeds = IssueSeeds(symbols=["a"], traceback_funcs=[], traceback_files=[], paths=[], exceptions=[], identifiers=[])
    # 1-char symbol must not match everything (was 0.45 via substring)
    assert _seed_score("some/long/file_xyz.py", seeds) == 0.0


def test_org_prefix_and_cross_org_analog(monkeypatch, tmp_path):
    import src.agents.fix_history as fh

    monkeypatch.setattr(fh, "_ledger_path", lambda: tmp_path / "fix_history.jsonl")
    from src.agents.state import AgentState

    django = AgentState(
        issue_text="django ValueError division frame",
        repo_path="repos/django",
        plan="guard divisor",
        patch="--- a/d.py\n+++ b/d.py\n@@ -1 +1 @@\n-x\n+y\n",
        critic_verdict="approved",
        critic_score=0.9,
        test_output="PASSED",
        strategy="minimal_diff",
    )
    assert fh.record_fix(django) is True

    # Same-org/transfer query with analog enabled returns the Django fix
    hits = fh.retrieve_fixes("sympy ValueError division frame", "repos/sympy", include_analog=True)
    assert len(hits) >= 1
    assert hits[-1].get("transfer") == "cross-org-analog"

    # Default stays isolated (backward-compatible)
    assert fh.retrieve_fixes("separability nothing related zzzqqq", "repos/django") == []
