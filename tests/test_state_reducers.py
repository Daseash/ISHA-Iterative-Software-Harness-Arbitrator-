"""P0-04: state reducers must not drop parallel branch evidence."""

import operator

import pytest

from src.agents.state import AgentState, coerce_state


def _reducer_for(field_name):
    ann = AgentState.model_fields[field_name].metadata
    # Pydantic stores Annotated metadata; find the reducer callable
    for m in ann:
        if m is operator.add:
            return operator.add
    # fallback: check annotation directly
    return ann[0] if ann else None


def test_append_only_lists_use_additive_reducer():
    for field in ("localization", "context_notes", "candidates", "model_log", "consistency_warnings"):
        reducer = _reducer_for(field)
        assert reducer is operator.add, f"{field} must use operator.add, got {reducer}"


def test_parallel_branches_concatenate_model_log():
    """Simulate 3 Send() branches each returning one log entry — all must survive."""
    branch_logs = [
        [{"role": "coder", "model": "m1", "strategy": "minimal_diff"}],
        [{"role": "coder", "model": "m2", "strategy": "call_site_aware"}],
        [{"role": "coder", "model": "m3", "strategy": "root_cause_first"}],
    ]
    merged: list = []
    for log in branch_logs:
        merged = operator.add(merged, log)
    assert len(merged) == 3
    assert {e["model"] for e in merged} == {"m1", "m2", "m3"}


def test_model_name_field_exists():
    s = AgentState(issue_text="bug")
    assert hasattr(s, "model_name")
    assert s.model_name == ""


def test_coerce_state_rejects_unknown_types():
    with pytest.raises(TypeError):
        coerce_state(12345)  # type: ignore[arg-type]
    with pytest.raises(TypeError):
        coerce_state(None)  # type: ignore[arg-type]
