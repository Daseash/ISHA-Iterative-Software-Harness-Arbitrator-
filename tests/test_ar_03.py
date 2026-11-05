"""AR-3 (merger scope): _MERGED dedupes one logical winner, never cross-talk.

- Same thread + same instance + same patch -> merge runs exactly once,
  even under concurrent threads (lock-guarded check-and-set).
- Same thread + different instance (or different patch) -> a NEW merge runs.
- Stale entries expire (TTL) so long-lived processes can re-merge.
- Event sink: thread-local sinks do not propagate into pool workers, so
  run_instance passes the sink explicitly and _append is lock-guarded.
"""

import json
import threading
import time
from unittest.mock import patch as _patch

import src.agents.graph as graph_mod
from src.agents.graph import _merge_key, merger_node
from src.agents.state import AgentState
from src.bench.runner import _append, _invoke_graph
from src.config import _call_event, reset_call_events, set_call_event_sink


def _winner(instance="django__django-11099", patch="diff --git a/x b/x"):
    return AgentState(
        issue_text="b",
        repo_path="/tmp",
        instance_id=instance,
        patch=patch,
        test_output="PASSED",
        local_sandbox_status="passed",
        critic_verdict="approved",
        approved=True,
        critic_score=0.9,
        strategy="minimal_diff",
    )


def _cfg(tid):
    return {"configurable": {"thread_id": tid, "apply": True}}


def test_same_winner_merges_once():
    st = _winner()
    with _patch("src.tools.patch_engine.apply_patch") as m:
        m.return_value = (False, "mocked")
        merger_node(st, config=_cfg("t-ar03-once"))
        merger_node(st, config=_cfg("t-ar03-once"))
        assert m.call_count == 1


def test_concurrent_same_winner_merges_once():
    st = _winner()
    with _patch("src.tools.patch_engine.apply_patch") as m:
        m.return_value = (False, "mocked")
        threads = [
            threading.Thread(
                target=merger_node, args=(st, _cfg("t-ar03-race"))
            )
            for _ in range(8)
        ]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        assert m.call_count == 1


def test_different_instance_is_new_merge():
    with _patch("src.tools.patch_engine.apply_patch") as m:
        m.return_value = (False, "mocked")
        merger_node(_winner(instance="a__a-1"), config=_cfg("t-ar03-shared"))
        merger_node(_winner(instance="b__b-2"), config=_cfg("t-ar03-shared"))
        assert m.call_count == 2


def test_different_patch_is_new_merge():
    with _patch("src.tools.patch_engine.apply_patch") as m:
        m.return_value = (False, "mocked")
        merger_node(_winner(patch="diff --git a/1 b/1"), config=_cfg("t-ar03-patch"))
        merger_node(_winner(patch="diff --git a/2 b/2"), config=_cfg("t-ar03-patch"))
        assert m.call_count == 2


def test_stale_entry_expires():
    st = _winner()
    key = _merge_key(st, "t-ar03-ttl")
    graph_mod._MERGED[key] = time.time() - (graph_mod._MERGED_TTL + 1)
    with _patch("src.tools.patch_engine.apply_patch") as m:
        m.return_value = (False, "mocked")
        merger_node(st, config=_cfg("t-ar03-ttl"))
        assert m.call_count == 1


def test_sink_does_not_leak_across_threads():
    """Thread-local sinks stay put: a sink armed on THIS thread is invisible
    to a pool worker — which is exactly why run_instance passes it explicitly."""
    received = []
    set_call_event_sink(received.append)
    try:
        out = []

        def worker():
            _call_event("coder", "m", "p", "ok", "note")
            out.append(len(received))

        t = threading.Thread(target=worker)
        t.start()
        t.join()
        assert out == [0]
        assert received == []
    finally:
        reset_call_events()


def test_worker_scoped_sink_routes_events():
    received = []

    def worker():
        reset_call_events()  # clear stale TLS (pools reuse threads)
        set_call_event_sink(received.append)
        _call_event("coder", "m", "p", "ok", "note")

    t = threading.Thread(target=worker)
    t.start()
    t.join()
    reset_call_events()
    assert len(received) == 1
    assert received[0]["role"] == "coder"


def test_append_thread_safe_jsonl(tmp_path):
    log = tmp_path / "log.jsonl"

    def writer(n):
        for i in range(25):
            _append(log, {"event": "call", "worker": n, "i": i})

    threads = [threading.Thread(target=writer, args=(n,)) for n in range(8)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    lines = log.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 200
    for ln in lines:
        assert set(json.loads(ln)) >= {"event", "worker", "i"}


def test_invoke_graph_propagates_sink(tmp_path):
    import src.bench.runner as runner_mod

    record = {"problem_statement": "b", "instance_id": "x__x-1"}
    received = []

    class FakeGraph:
        def invoke(self, state, config=None):
            _call_event("coder", "m", "p", "ok", "note")
            return AgentState(issue_text="b", repo_path="/tmp")

    with (
        _patch.object(runner_mod, "instance_checkout", return_value=tmp_path),
        _patch("src.agents.context.build_repo_context", return_value=""),
        _patch("src.agents.graph.compiled_graph", new=FakeGraph()),
    ):
        out = _invoke_graph(record, "t-ar03-sink", sink=received.append)
        assert received and received[0]["role"] == "coder"
        assert out["state"].issue_text == "b"
        # No sink: no crash, no events.
        out2 = _invoke_graph(record, "t-ar03-sink-none")
        assert out2["state"].issue_text == "b"
    reset_call_events()
