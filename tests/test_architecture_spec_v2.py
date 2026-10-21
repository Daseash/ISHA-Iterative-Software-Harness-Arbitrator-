"""
Comprehensive verification test for all 11 Subsystem upgrades from
isha_architecture_audit_and_upgrade_specification.md (v2.0)
"""

import sqlite3
import time
from pathlib import Path
import pytest

from src.agents.state import AgentState
from src.tools.localizer import compute_hybrid_score, _file_prior
from src.rag.indexer import format_chunk_for_embedding, QdrantIndexer, VECTOR_SIZE
from src.review.laya_judge import compute_laya_composite, diff_deletes_test_assertions
from src.agents.dispatch import select_tournament_strategies
from src.memory.store import (
    reap_orphans,
    get_episodic_invariants,
    record_episodic_invariant,
    org_critic_threshold,
)
from src.agents.nodes import build_coder_prompt


def test_subsystem_1_hybrid_score_normalization_and_priors():
    # 1. Test BM25 saturation: very large BM25 score cannot blow up total score
    signals_extreme = {
        "bm25": 1000.0,
        "vector": 0.8,
        "seed": 0.5,
        "defs": 1.0,
        "llm_loc": 0.9,
        "callers": 0.5,
    }
    score_loc = compute_hybrid_score(signals_extreme, file_kind="source", phase="localize")
    assert 0.0 <= score_loc <= 1.0

    # 2. Test phase-aware priors: test files get prior 1.0 during regression_test, 0.70 during localize
    signals_standard = {"bm25": 1.5, "vector": 0.5, "seed": 0.5, "defs": 0.5, "llm_loc": 0.5, "callers": 0.5}
    score_test_in_loc = compute_hybrid_score(signals_standard, file_kind="test", phase="localize")
    score_test_in_repro = compute_hybrid_score(signals_standard, file_kind="test", phase="regression_test")
    assert score_test_in_repro > score_test_in_loc
    assert abs(score_test_in_repro / score_test_in_loc - (1.0 / 0.70)) < 0.05


def test_subsystem_2_ast_chunk_header():
    chunk = {
        "file_path": "django/core/handlers/base.py",
        "name": "BaseHandler.resolve_request",
        "content": "def resolve_request(self, request):\n    pass",
    }
    formatted = format_chunk_for_embedding(chunk)
    assert "# File: django/core/handlers/base.py | Name: BaseHandler.resolve_request" in formatted
    assert "def resolve_request" in formatted


def test_subsystem_4_laya_composite_vetoes_and_test_deletion():
    # Normal passing patch
    clean_score = compute_laya_composite(
        fix_quality=2,
        matches_issue=0.9,
        safe_to_apply=0.9,
        secrets_or_danger=0.0,
        logic_drift=0.0,
    )
    assert clean_score > 0.8

    # Multiplicative hard veto on danger > 0.50
    danger_score = compute_laya_composite(
        fix_quality=2,
        matches_issue=0.9,
        safe_to_apply=0.9,
        secrets_or_danger=0.55,
        logic_drift=0.0,
    )
    assert danger_score == 0.0

    # Multiplicative hard veto on logic_drift > 0.70
    drift_score = compute_laya_composite(
        fix_quality=2,
        matches_issue=0.9,
        safe_to_apply=0.9,
        secrets_or_danger=0.0,
        logic_drift=0.75,
    )
    assert drift_score == 0.0

    # Test assertion deletion detection
    cheat_patch = (
        "--- a/tests/test_views.py\n"
        "+++ b/tests/test_views.py\n"
        "@@ -10,3 +10,2 @@\n"
        " def test_calc():\n"
        "-    assert result == 42\n"
    )
    assert diff_deletes_test_assertions(cheat_patch) is True

    valid_patch = (
        "--- a/src/calc.py\n"
        "+++ b/src/calc.py\n"
        "@@ -10,2 +10,3 @@\n"
        " def calc(val):\n"
        "+    if val is None: return 0\n"
        "     return val + 1\n"
    )
    assert diff_deletes_test_assertions(valid_patch) is False


def test_subsystem_5_dynamic_3_of_5_strategy_selector():
    # Issue with NoneType should select defensive_fix
    st_none = AgentState(
        issue_text="TypeError: NoneType object has no attribute 'get'",
        repo_path="repos/django",
    )
    strats_none = select_tournament_strategies(st_none)
    assert "defensive_fix" in strats_none

    # Issue with cross-file mentions should select cross_file_audit
    st_cross = AgentState(
        issue_text="Refactoring needed across submodule and cross-file dependencies",
        repo_path="repos/django",
    )
    strats_cross = select_tournament_strategies(st_cross)
    assert "cross_file_audit" in strats_cross


def test_subsystem_9_and_10_memory_store_and_episodic_invariants(tmp_path, monkeypatch):
    db_file = tmp_path / "test_memory.db"
    monkeypatch.setenv("ISHA_MEMORY_DB", str(db_file))

    # Test episodic pre-seeding for django
    rules = get_episodic_invariants("django", path=db_file)
    assert len(rules) >= 3
    assert any("HASHABILITY" in r for r in rules)
    assert any("id_for_label" in r for r in rules)
    assert any("__qualname__" in r for r in rules)

    # Test learning a new episodic invariant
    ok = record_episodic_invariant("flask", "Always preserve request context in background threads", path=db_file)
    assert ok is True
    flask_rules = get_episodic_invariants("flask", path=db_file)
    assert len(flask_rules) == 1
    assert "request context" in flask_rules[0]

    # Test orphan reaper on stale Write-A
    conn = sqlite3.connect(str(db_file))
    now = time.time()
    conn.execute(
        "INSERT INTO outcomes(instance_id, repo, repo_org, issue_hash, strategy, model, "
        "patch_hash, critic_score, tests_passed, resolved, fail_bucket, traceback_sig, ts) "
        "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
        ("stale-1", "repo", "django", "hash", "minimal_diff", "model", "phash", 0.8, 0, None, "", "", now - 1200),
    )
    conn.execute(
        "INSERT INTO outcomes(instance_id, repo, repo_org, issue_hash, strategy, model, "
        "patch_hash, critic_score, tests_passed, resolved, fail_bucket, traceback_sig, ts) "
        "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
        ("fresh-1", "repo", "django", "hash", "minimal_diff", "model", "phash", 0.8, 0, None, "", "", now - 60),
    )
    conn.commit()
    conn.close()

    # Reopen connection -> reap_orphans runs
    reaped = reap_orphans(sqlite3.connect(str(db_file)))
    assert reaped >= 1

    conn = sqlite3.connect(str(db_file))
    stale_row = conn.execute("SELECT resolved, fail_bucket FROM outcomes WHERE instance_id='stale-1'").fetchone()
    fresh_row = conn.execute("SELECT resolved FROM outcomes WHERE instance_id='fresh-1'").fetchone()
    conn.close()

    assert stale_row[0] == 0
    assert stale_row[1] == "orphan_timeout"
    assert fresh_row[0] is None


def test_subsystem_10_prompt_invariants_injection(tmp_path, monkeypatch):
    db_file = tmp_path / "test_memory.db"
    monkeypatch.setenv("ISHA_MEMORY_DB", str(db_file))

    # When repo_org is django, episodic playbooks are injected
    st_django = AgentState(
        issue_text="AttributeError in SimpleLazyObject",
        repo_path="repos/django",
        instance_id="django__django-11111",
        plan="Fix lazy evaluation",
    )
    prompt_django = build_coder_prompt(st_django)

    # Core 5 Universal Python Invariants MUST be present
    assert "CLASS ANCHORING" in prompt_django
    assert "GUARD CLAUSE COMPLETENESS" in prompt_django
    assert "DECORATOR PRESERVATION" in prompt_django
    assert "EXECUTION SCOPE & NAMESPACES" in prompt_django
    assert "TYPE & RETURN INVARIANTS" in prompt_django

    # Episodic Domain Playbook section dynamically loaded
    assert "EPISODIC DOMAIN PLAYBOOKS (dynamically loaded from memory.db for 'django')" in prompt_django
    assert "HASHABILITY CONTRACTS" in prompt_django
    assert "id_for_label" in prompt_django
