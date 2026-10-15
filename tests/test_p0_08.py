"""P0-08: single budget, tier demotion, ledger lock."""

import time


def test_repro_empty_demoted_below_evidence():
    from src.agents.candidates import Candidate, rank_candidates

    def mk(idx, repro, score):
        c = Candidate(index=idx, strategy="m", temperature=0.1)
        c.patch = "diff --git a/f b/f\n--- a/f\n+++ b/f\n@@ -1 +1 @@\n-x\n+y\n"
        c.apply_ok = True
        c.gate_ok = True
        c.repro = repro
        c.combined_score = score
        c.added, c.removed = 5, 5
        return c

    unverified = mk(1, {}, 0.99)
    confirmed = mk(2, {"available": True, "before_ok": True, "after_ok": True}, 0.5)
    ordered = rank_candidates([unverified, confirmed])
    assert ordered[0].index == 2


def test_single_shared_deadline_fast(monkeypatch):
    import src.agents.candidates as cand
    from src.agents.state import AgentState

    monkeypatch.setenv("ISHA_CANDIDATE_TIMEOUT", "5")
    monkeypatch.setenv("ISHA_CANDIDATES_PARALLEL", "1")
    st = AgentState(issue_text="b", repo_path="/tmp")
    t0 = time.time()
    out = cand.generate_candidates(st, n=1, instance_id="x", seed_patch="[no patch]")
    assert time.time() - t0 < 5 + 10
    assert isinstance(out, list)
